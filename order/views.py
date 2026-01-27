import json
from bson.objectid import ObjectId
from datetime import datetime, timezone,timedelta

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from config.mongo import db
from accounts.current_user import get_current_user
from cart.utils import get_user_cart
from config.permissions import is_user_admin,is_user_moderator
import math
from math import ceil
from log.utils import order_updation_log,order_deletion_log
from rest_framework.decorators import api_view
import csv
from django.http import HttpResponse

# MongoDB collections
orders_col = db['orders']
carts_col = db['carts']
products_col = db['products']



# ---------------- PLACE ORDER (SELECTED ITEMS) ----------------

@api_view(['POST'])
def place_order(request):
    # -------- AUTH --------
    user, error = get_current_user(request)
    if error:
        return JsonResponse({'error': error}, status=401)

    # -------- PARSE BODY --------
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        body = {}

    shipping_address = body.get('shippingAddress') or user.get('address')
    transection_id = body.get('transection_id')

    if not transection_id:
        return JsonResponse(
            {"error": "Transaction ID is required"},
            status=400
        )

    # -------- GET CART --------
    cart = get_user_cart(user['_id'])
    if not cart:
        return JsonResponse({'error': 'Cart not found'}, status=400)

    selected_items = [
        item for item in cart['items']
        if item.get('is_selected') is True
    ]

    if not selected_items:
        return JsonResponse(
            {'error': 'No items selected'},
            status=400
        )

    order_items = []
    total_price = 0
    updated_products = []  # for rollback if needed

    # -------- ATOMIC STOCK UPDATE --------
    for item in selected_items:
        quantity = item['quantity']

        update_result = products_col.find_one_and_update(
            {
                '_id': item['product_id'],
                'stock': {'$gte': quantity}
            },
            {
                '$inc': {
                    'stock': -quantity,
                    'sold_count': quantity
                }
            },
            return_document=True
        )

        if not update_result:
            # -------- ROLLBACK PREVIOUS UPDATES --------
            for p in updated_products:
                products_col.update_one(
                    {'_id': p['product_id']},
                    {
                        '$inc': {
                            'stock': p['quantity'],
                            'sold_count': -p['quantity']
                        }
                    }
                )

            return JsonResponse(
                {'error': 'Too late! One or more products are out of stock'},
                status=400
            )

        subtotal = item['price_at_add'] * quantity
        total_price += subtotal

        order_items.append({
            'product_id': update_result['_id'],
            'name': update_result['name'],
            'color_id': item['color_id'],
            'size_id': item['size_id'],
            'quantity': quantity,
            'unit_price': item['price_at_add'],
            'subtotal': subtotal
        })

        updated_products.append({
            'product_id': update_result['_id'],
            'quantity': quantity
        })

    # -------- CREATE ORDER --------
    order = {
        'user_id': ObjectId(user['_id']),
        'email':user['email'],
        'phone':user['phone'],
        'items': order_items,
        'shipping_address': shipping_address,
        'total_price': total_price,
        'payment_status': 'paid',
        'order_status': 'pending',
        'transection_id': transection_id,
        'created_at': datetime.now(timezone.utc),
        'updated_at': None
    }

    try:
        result = orders_col.insert_one(order)
    except Exception:
        # -------- ROLLBACK STOCK IF ORDER FAILS --------
        for p in updated_products:
            products_col.update_one(
                {'_id': p['product_id']},
                {
                    '$inc': {
                        'stock': p['quantity'],
                        'sold_count': -p['quantity']
                    }
                }
            )
        return JsonResponse(
            {'error': 'Order creation failed'},
            status=500
        )

    # -------- REMOVE ITEMS FROM CART --------
    carts_col.update_one(
        {'_id': cart['_id']},
        {
            '$set': {
                'items': [
                    item for item in cart['items']
                    if not item.get('is_selected')
                ],
                'updated_at': datetime.now(timezone.utc)
            }
        }
    )

    return JsonResponse(
        {
            'message': 'Order placed successfully',
            'order_id': str(result.inserted_id)
        },
        status=201
    )

# ---------------- CANCEL ORDER ----------------
@api_view(['POST'])
def cancel_order(request, order_id):
    user, error = get_current_user(request)
    if error:
        return JsonResponse({'error': error}, status=401)

    order = orders_col.find_one({'_id': ObjectId(order_id)})
    if not order:
        return JsonResponse({'error': 'Order not found'}, status=404)

    if str(order['user_id']) != str(user['_id']):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if order['order_status'] not in ['pending', 'confirmed']:
        return JsonResponse(
            {'error': 'Order cannot be cancelled'},
            status=400
        )

    # Restore stock
    for item in order['items']:
        products_col.update_one(
            {'_id': item['product_id']},
            {'$inc': {
                'stock': item['quantity'],
                'sold_count': -item['quantity']
            }}
        )

    orders_col.update_one(
        {'_id': ObjectId(order_id)},
        {'$set': {
            'order_status': 'cancelled',
            'updated_at': datetime.now(timezone.utc)
        }}
    )

    return JsonResponse({'message': 'Order cancelled'}, status=200)




@api_view(['GET'])
def get_all_orders(request):
    user, error = get_current_user(request)
    if error:
        return JsonResponse({'error': error}, status=401)

    if not (is_user_admin(user) or is_user_moderator(user)):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    # -------- PAGINATION PARAMS --------
    try:
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))
        page = max(page, 1)
        limit = min(max(limit, 1), 100)  # max 100 per page
    except ValueError:
        return JsonResponse({'error': 'Invalid pagination params'}, status=400)

    skip = (page - 1) * limit

    try:
        total_orders = orders_col.count_documents({})
        orders_cursor = (
            orders_col
            .find()
            .skip(skip)
            .limit(limit)
            .sort('_id', -1)
        )
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    orders_list = []

    for order in orders_cursor:
        order['_id'] = str(order['_id'])
        order['user_id'] = str(order['user_id'])

        for item in order.get('items', []):
            item['product_id'] = str(item['product_id'])
            item['color_id'] = str(item['color_id'])
            item['size_id'] = str(item['size_id'])

        orders_list.append(order)

    total_pages = ceil(total_orders / limit)

    return JsonResponse({
        'pagination': {
            'page': page,
            'limit': limit,
            'total_orders': total_orders,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1,
        },
        'orders': orders_list
    }, status=200)



# search order by user, status, date range, total price range, product name
@api_view(['GET'])
def search_orders(request):
    # -------- AUTH --------
    user, error = get_current_user(request)
    if error:
        return JsonResponse({'error': error}, status=401)

    if not (is_user_admin(user) or is_user_moderator(user)):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    # -------- QUERY PARAMS --------
    user_id = request.GET.get('user_id')
    user_email = request.GET.get('user_email')
    order_status = request.GET.get('status')
    payment_status = request.GET.get('payment_status')
    product_name = request.GET.get('product_name')

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    date_range = request.GET.get('date_range')   # today | this_week | this_month | this_year
    month = request.GET.get('month')             # 1 - 12
    year = request.GET.get('year')# YYYY
    phone_number = request.GET.get('phone_number')

    # -------- PAGINATION --------
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
    except ValueError:
        return JsonResponse({'error': 'Invalid pagination params'}, status=400)

    if page < 1:
        page = 1

    MAX_PAGE_SIZE = 100
    if page_size > MAX_PAGE_SIZE:
        page_size = MAX_PAGE_SIZE

    skip = (page - 1) * page_size

    # -------- BUILD QUERY --------
    query = {}

    if user_id:
        query['user_id'] = ObjectId(user_id)

    if order_status:
        query['order_status'] = order_status

    if payment_status:
        query['payment_status'] = payment_status
    
    if phone_number:
        query['phone'] = phone_number
    
    if user_email:
        query['email'] = {'$regex': user_email, '$options': 'i'}
    
   
        
        

    # -------- PRICE RANGE --------
    if min_price or max_price:
        query['total_price'] = {}
        if min_price:
            query['total_price']['$gte'] = float(min_price)
        if max_price:
            query['total_price']['$lte'] = float(max_price)

    # -------- DATE FILTERS --------
    now = datetime.now(timezone.utc)

    if date_range:
        if date_range == 'today':
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        elif date_range == 'this_week':
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)

        elif date_range == 'this_month':
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        elif date_range == 'this_year':
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        else:
            return JsonResponse({'error': 'Invalid date_range'}, status=400)

        query['created_at'] = {'$gte': start, '$lte': now}

    elif month or year:
        if not year:
            return JsonResponse(
                {'error': 'Year is required when filtering by month'},
                status=400
            )

        year = int(year)
        month = int(month) if month else 1

        start = datetime(year, month, 1, tzinfo=timezone.utc)
        end = (
            datetime(year + 1, 1, 1, tzinfo=timezone.utc)
            if month == 12
            else datetime(year, month + 1, 1, tzinfo=timezone.utc)
        )

        query['created_at'] = {'$gte': start, '$lt': end}

    # -------- PRODUCT NAME SEARCH --------
    if product_name:
        query['items.name'] = {'$regex': product_name, '$options': 'i'}

    # -------- TOTAL COUNT --------
    total_orders_count = orders_col.count_documents(query)

    # -------- ANALYTICS (ALL MATCHED ORDERS) --------
    analytics_cursor = orders_col.find(query)

    total_revenue = 0
    total_items_sold = 0
    status_breakdown = {}

    for order in analytics_cursor:
        total_revenue += order.get('total_price', 0)

        status = order.get('order_status', 'unknown')
        status_breakdown[status] = status_breakdown.get(status, 0) + 1

        for item in order.get('items', []):
            total_items_sold += item.get('quantity', 0)

    # -------- PAGINATED DATA --------
    orders_cursor = (
        orders_col
        .find(query)
        .sort('created_at', -1)
        .skip(skip)
        .limit(page_size)
    )

    orders_list = []
    for order in orders_cursor:
        order['_id'] = str(order['_id'])
        order['user_id'] = str(order['user_id'])

        for item in order.get('items', []):
            item['product_id'] = str(item['product_id'])
            item['color_id'] = str(item['color_id'])
            item['size_id'] = str(item['size_id'])

        orders_list.append(order)

    total_pages = math.ceil(total_orders_count / page_size)

    # -------- RESPONSE --------
    return JsonResponse(
        {
            'analytics': {
                'total_orders': total_orders_count,
                'total_amount_ordered': total_revenue,
                'avg_order_value': round(
                    total_revenue / total_orders_count, 2
                ) if total_orders_count else 0,
                'total_items_sold': total_items_sold,
                'by_status': status_breakdown
            },
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages,
                'total_records': total_orders_count,
                'has_next': page < total_pages,
                'has_prev': page > 1
            },
            'count': len(orders_list),
            'orders': orders_list
        },
        status=200
    )
    
    
#update orders
@api_view(['PUT'])
def update_order(request,order_id):
    
    if request.method != 'PUT':
        
        return JsonResponse({"error":"method is not allowed"})
    
    user,error = get_current_user(request)
    
    if error:
        return JsonResponse({"error":error})
    

    if not (is_user_admin(user) or is_user_moderator(user)):
        
        return JsonResponse({"error":"Your are not authorized to perform this action"})
    
    order = orders_col.find_one({"_id":ObjectId(order_id)})
    
    if not order:
        return JsonResponse({"error":"Order not Found"})
    
    update_fields = {}
    
    data = json.loads(request.body.decode('utf-8'))

    shipping_address = data.get("shipping_address")
    total_price = data.get("total_price")
    payment_status =data.get("payment_status")
    order_status = data.get("order_status")
    
    if shipping_address:
        update_fields['shipping_address']=shipping_address
    
    if total_price:
        if total_price < 0:
            return JsonResponse({"error":"price can not be less then 0"})
        update_fields['total_price']=total_price
    
    if payment_status:
        if payment_status in ['expired','pending','complete']:
            update_fields['payment_status']=payment_status
        else:
            return JsonResponse({"error":"wrong status input.it must be expired,pending or complete"})
    
    if order_status:
        if order_status in ["pending" , "confirmed","shipped","delivered","cancelled"]:
            
            update_fields['order_status']=order_status
        else:
            return JsonResponse({"error":"wrong status input.it must be pending , confirmed,shipped,delivered,cancelled"})
        
        
    try:
        orders_col.update_one(
            {"_id":ObjectId(order_id)},
            {"$set":update_fields}
        )
        #logging
        order_updation_log(order,user)
        return JsonResponse({"message":"order updated successfully"})
    except Exception as e:
        return JsonResponse({"error":str(e)})
    

#delete order
@api_view(['DELETE'])
def delete_order(request,order_id):
    
    if request.method != 'DELETE':
        
        return JsonResponse({"error":"method is not allowed"})
    
    user,error = get_current_user(request)
    
    if error:
        return JsonResponse({"error":error})
    

    if not (is_user_admin(user) or is_user_moderator(user)):
        
        return JsonResponse({"error":"Your are not authorized to perform this action"})
    
    
    order = orders_col.delete_one({"_id":ObjectId(order_id)})
    if not order:
        return JsonResponse({"error":"order not found"})
    
    
    try:
        orders_col.delete_one({"_id":ObjectId(order_id)})
        order_deletion_log(order,user)
        
        return JsonResponse({"message":"order deleted successfully"})
    except Exception as e:
        return JsonResponse({"error":str(e)})






# ---------------- GET ALL ORDERS (ADMIN/MODERATOR) and Export as CSV----------------

@api_view(['GET'])
def export_orders_csv(request):
    
    user, error = get_current_user(request)
    if error:
        return JsonResponse({'error': error}, status=401)

    if not (is_user_admin(user) or is_user_moderator(user)):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Order ID', 'User ID', 'Items', 'Shipping Address',
        'Total Price', 'Payment Status', 'Order Status',
        'Transaction ID', 'Created At', 'Updated At'
    ])

    orders_cursor = orders_col.find().sort('_id', -1)

    for order in orders_cursor:
        items_str = "; ".join([
            f"{item['name']} (Qty: {item['quantity']}, Unit Price: {item['unit_price']})"
            for item in order.get('items', [])
        ])

        writer.writerow([
            str(order['_id']),
            str(order['user_id']),
            items_str,
            order.get('shipping_address', ''),
            order.get('total_price', 0),
            order.get('payment_status', ''),
            order.get('order_status', ''),
            order.get('transection_id', ''),
            order.get('created_at', '').strftime('%Y-%m-%d %H:%M:%S') if order.get('created_at') else '',
            order.get('updated_at', '').strftime('%Y-%m-%d %H:%M:%S') if order.get('updated_at') else ''
        ])

    return response