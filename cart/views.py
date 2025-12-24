import json
from bson.objectid import ObjectId
from datetime import datetime, timezone

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from config.mongo import db
from accounts.current_user import get_current_user
from .utils import get_user_cart
from rest_framework.decorators import api_view

products_col = db['products']
carts_col = db['carts']


# ---------------- GET CART ----------------
@api_view(['GET'])
def get_cart(request):
    user, error = get_current_user(request)
    if error:
        return JsonResponse({'error': error}, status=401)

    cart = get_user_cart(user['_id'])

    total_price = sum(
        item['price_at_add'] * item['quantity']
        for item in cart['items']
    )

    for item in cart['items']:
        item['item_id'] = str(item['item_id'])
        item['product_id'] = str(item['product_id'])
        item['color_id'] = str(item['color_id'])
        item['size_id'] = str(item['size_id'])

    return JsonResponse({
        'items': cart['items'],
        'total_price': total_price
    }, status=200)


# ---------------- ADD TO CART ----------------
@api_view(['POST'])
def add_to_cart(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    user, error = get_current_user(request)
    if error:
        return JsonResponse({'error': error}, status=401)

    data = json.loads(request.body)

    product_id = ObjectId(data['product_id'])
    color_id = ObjectId(data['color_id'])
    size_id = ObjectId(data['size_id'])
    quantity = int(data.get('quantity', 1))

    product = products_col.find_one({'_id': product_id})
    if not product:
        return JsonResponse({'error': 'Product not found'}, status=404)

    cart = get_user_cart(user['_id'])

    for item in cart['items']:
        if (
            item['product_id'] == product_id and
            item['color_id'] == color_id and
            item['size_id'] == size_id
        ):
            item['quantity'] += quantity
            break
    else:
        cart['items'].append({
            'item_id': ObjectId(),
            'product_id': product_id,
            'color_id': color_id,
            'size_id': size_id,
            'quantity': quantity,
            'price_at_add': product['price'],
            'is_selected': False
        })

    carts_col.update_one(
        {'_id': cart['_id']},
        {'$set': {'items': cart['items'], 'updated_at': datetime.now(timezone.utc)}}
    )

    return JsonResponse({'message': 'Added to cart'}, status=200)


# ---------------- UPDATE QUANTITY ----------------
@api_view(['PUT'])
def update_cart_quantity(request):
    if request.method != 'PUT':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    user, error = get_current_user(request)
    if error:
        return JsonResponse({'error': error}, status=401)

    data = json.loads(request.body)
    item_id = data['item_id']
    quantity = int(data['quantity'])

    if quantity < 1:
        return JsonResponse({'error': 'Quantity must be >= 1'}, status=400)

    cart = get_user_cart(user['_id'])

    for item in cart['items']:
        if str(item['item_id']) == item_id:
            item['quantity'] = quantity
            break

    carts_col.update_one(
        {'_id': cart['_id']},
        {'$set': {'items': cart['items'], 'updated_at': datetime.now(timezone.utc)}}
    )

    return JsonResponse({'message': 'Quantity updated'}, status=200)


# ---------------- UPDATE VARIANT ----------------
@api_view(['PUT'])
def update_cart_variant(request):
    if request.method != 'PUT':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    user, error = get_current_user(request)
    if error:
        return JsonResponse({'error': error}, status=401)

    data = json.loads(request.body)

    item_id = data['item_id']
    new_color = ObjectId(data['new_color_id'])
    new_size = ObjectId(data['new_size_id'])

    cart = get_user_cart(user['_id'])

    for item in cart['items']:
        if str(item['item_id']) == item_id:
            item['color_id'] = new_color
            item['size_id'] = new_size
            break
    else:
        return JsonResponse({'error': 'Cart item not found'}, status=404)

    carts_col.update_one(
        {'_id': cart['_id']},
        {'$set': {'items': cart['items'], 'updated_at': datetime.now(timezone.utc)}}
    )

    return JsonResponse({'message': 'Variant updated'}, status=200)


# ---------------- SELECT ITEMS ----------------
@api_view(['PATCH'])
def select_cart_items(request):
    """
    Supports:
    - single
    - multiple
    - select all
    """
    if request.method != 'PATCH':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    user, error = get_current_user(request)
    if error:
        return JsonResponse({'error': error}, status=401)

    data = json.loads(request.body)
    item_ids = data.get('item_ids')  # list OR None
    is_selected = data.get('is_selected', True)

    cart = get_user_cart(user['_id'])

    for item in cart['items']:
        if not item_ids or str(item['item_id']) in item_ids:
            item['is_selected'] = is_selected

    carts_col.update_one(
        {'_id': cart['_id']},
        {'$set': {'items': cart['items'], 'updated_at': datetime.now(timezone.utc)}}
    )

    return JsonResponse({'message': 'Selection updated'}, status=200)


# ---------------- REMOVE ITEM ----------------
@api_view(['DELETE'])
def remove_cart_item(request):
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    user, error = get_current_user(request)
    if error:
        return JsonResponse({'error': error}, status=401)

    data = json.loads(request.body)
    item_id = data['item_id']

    cart = get_user_cart(user['_id'])

    cart['items'] = [
        item for item in cart['items']
        if str(item['item_id']) != item_id
    ]

    carts_col.update_one(
        {'_id': cart['_id']},
        {'$set': {'items': cart['items'], 'updated_at': datetime.now(timezone.utc)}}
    )

    return JsonResponse({'message': 'Item removed'}, status=200)





# ---------------- CLEAR CART ----------------
@api_view(['DELETE'])
def clear_cart(request):
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    user, error = get_current_user(request)
    if error:
        return JsonResponse({'error': error}, status=401)

    cart = carts_col.find_one({'user_id': ObjectId(user['_id'])})
    if not cart:
        return JsonResponse({'error': 'Cart not found'}, status=404)

    carts_col.update_one(
        {'_id': cart['_id']},
        {
            '$set': {
                'items': [],
                'updated_at': datetime.now(timezone.utc)
            }
        }
    )

    return JsonResponse({'message': 'Cart cleared successfully'}, status=200)
