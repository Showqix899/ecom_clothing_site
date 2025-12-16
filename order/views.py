import json
from bson.objectid import ObjectId
from datetime import datetime, timezone

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from config.mongo import db
from accounts.current_user import get_current_user
from cart.utils import get_user_cart

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
