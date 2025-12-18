import json
from bson.objectid import ObjectId
from datetime import datetime, timezone,timedelta

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from config.mongo import db
from accounts.current_user import get_current_user
from cart.utils import get_user_cart
from config.permissions import is_user_admin,is_user_moderator

orders_col = db['orders']
carts_col = db['carts']
products_col = db['products']



# ---------------- PLACE ORDER (SELECTED ITEMS) ----------------
@csrf_exempt
def place_order(request):
    user, error = get_current_user(request)
    print(f'user: {user}')
    if error:
        return JsonResponse({'error': error}, status=401)

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    
    try:
        
        body = json.loads(request.body)
        shipping_address = body.get('shippingAddress')

    except json.JSONDecodeError:
        shipping_address = None
        pass
   
    if not shipping_address:
        shipping_address = user.get('address')

    cart = get_user_cart(user['_id'])
    print(f'cart: {cart}')
    if not cart:
        return JsonResponse({'error': 'Cart not found'}, status=400)

    selected_items = [
        item for item in cart['items']
        if item.get('is_selected') is True
    ]

    if not selected_items:
        
        return JsonResponse({'error': 'No items selected'}, status=400)

    order_items = []
    total_price = 0

    # -------- STOCK CHECK --------
    for item in selected_items:
        product = products_col.find_one({'_id': item['product_id']})

        if not product or product['stock'] < item['quantity']:
            return JsonResponse({
                'error': f"Too late! {product['name']} is out of stock"
            }, status=400)

        subtotal = item['price_at_add'] * item['quantity']

        order_items.append({
            'product_id': product['_id'],
            'name': product['name'],
            'color_id': item['color_id'],
            'size_id': item['size_id'],
            'quantity': item['quantity'],
            'unit_price': item['price_at_add'],
            'subtotal': subtotal
        })

        total_price += subtotal

    # -------- CREATE ORDER --------
    order = {
        'user_id': ObjectId(user['_id']),
        'items': order_items,
        'shipping_address': shipping_address,
        'total_price': total_price,
        'payment_status': 'pending',
        'order_status': 'pending',
        'created_at': datetime.now(timezone.utc),
        'updated_at': None
    }

    result = orders_col.insert_one(order)

    # -------- UPDATE PRODUCT STOCK --------
    for item in order_items:
        products_col.update_one(
            {'_id': item['product_id']},
            {'$inc': {
                'stock': -item['quantity'],
                'sold_count': item['quantity']
            }}
        )

    # -------- REMOVE ORDERED ITEMS FROM CART --------
    cart['items'] = [
        item for item in cart['items']
        if not item.get('is_selected')
    ]

    carts_col.update_one(
        {'_id': cart['_id']},
        {'$set': {'items': cart['items'], 'updated_at': datetime.now(timezone.utc)}}
    )

    return JsonResponse({
        'message': 'Order placed successfully',
        'order_id': str(result.inserted_id)
    }, status=201)


# ---------------- CANCEL ORDER ----------------
@csrf_exempt
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




@csrf_exempt
def get_all_orders(request):
    user, error = get_current_user(request)
    if error:
        return JsonResponse({'error': error}, status=401)

    if not (is_user_admin(user) or is_user_moderator(user)):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        orders = orders_col.find()
        orders_list = []
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    for order in orders:
        # --- convert order-level ObjectIds ---
        order['_id'] = str(order['_id'])
        order['user_id'] = str(order['user_id'])

        # --- convert item-level ObjectIds ---
        for item in order.get('items', []):
            item['product_id'] = str(item['product_id'])
            item['color_id'] = str(item['color_id'])
            item['size_id'] = str(item['size_id'])

        orders_list.append(order)

    return JsonResponse({'orders': orders_list}, status=200)




#search order by user, status, date range,total price range, product name
@csrf_exempt
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
    order_status = request.GET.get('status')
    payment_status = request.GET.get('payment_status')
    product_name = request.GET.get('product_name')

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    date_range = request.GET.get('date_range')   # today | this_week | this_month | this_year
    month = request.GET.get('month')             # 1 - 12
    year = request.GET.get('year')               # YYYY

    # -------- BUILD QUERY --------
    query = {}

    if user_id:
        query['user_id'] = ObjectId(user_id)

    if order_status:
        query['order_status'] = order_status

    if payment_status:
        query['payment_status'] = payment_status

    # -------- PRICE RANGE --------
    if min_price or max_price:
        query['total_price'] = {}
        if min_price:
            query['total_price']['$gte'] = float(min_price)
        if max_price:
            query['total_price']['$lte'] = float(max_price)

    # -------- DATE FILTERS --------
    now = datetime.now(timezone.utc)

    # 🔹 predefined date ranges
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

    # 🔹 explicit month/year filter
    elif month or year:
        if not year:
            return JsonResponse(
                {'error': 'Year is required when filtering by month'},
                status=400
            )

        year = int(year)
        month = int(month) if month else 1

        start = datetime(year, month, 1, tzinfo=timezone.utc)

        if month == 12:
            end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end = datetime(year, month + 1, 1, tzinfo=timezone.utc)

        query['created_at'] = {'$gte': start, '$lt': end}

    # -------- PRODUCT NAME SEARCH --------
    if product_name:
        query['items.name'] = {'$regex': product_name, '$options': 'i'}

    # -------- FETCH ORDERS --------
    orders = orders_col.find(query).sort('created_at', -1)

    orders_list = []
    total_revenue = 0
    total_items_sold = 0
    status_breakdown = {}

    for order in orders:
        order['_id'] = str(order['_id'])
        order['user_id'] = str(order['user_id'])

        total_revenue += order.get('total_price', 0)

        status = order.get('order_status', 'unknown')
        status_breakdown[status] = status_breakdown.get(status, 0) + 1

        for item in order.get('items', []):
            item['product_id'] = str(item['product_id'])
            item['color_id'] = str(item['color_id'])
            item['size_id'] = str(item['size_id'])
            total_items_sold += item.get('quantity', 0)

        orders_list.append(order)

    total_orders = len(orders_list)
    avg_order_value = (
        total_revenue / total_orders if total_orders else 0
    )

    # -------- RESPONSE --------
    return JsonResponse(
        {
            'analytics': {
                'total_orders': total_orders,
                'total_amount_orderd': total_revenue,
                'avg_order_value': round(avg_order_value, 2),
                'total_items_sold': total_items_sold,
                'by_status': status_breakdown
            },
            'count': total_orders,
            'orders': orders_list
        },
        status=200
    )    