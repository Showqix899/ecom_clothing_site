import json
from bson import ObjectId
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timezone,timedelta

from config.mongo import db
from accounts.current_user import get_current_user
from config.permissions import is_user_admin, is_user_moderator
from math import ceil

orders_col = db['orders']
payments_col = db['payments']
products_col = db['products']


@csrf_exempt
def submit_payment(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    user, error = get_current_user(request)
    if error:
        return JsonResponse({'error': error}, status=401)

    data = json.loads(request.body or {})
    order_id = data.get('order_id')
    transaction_id = data.get('transaction_id')

    if not order_id or not transaction_id:
        return JsonResponse(
            {'error': 'order_id and transaction_id are required'},
            status=400
        )

    # -------- GET ORDER --------
    order = orders_col.find_one({'_id': ObjectId(order_id)})
    if not order:
        return JsonResponse({'error': 'Order not found'}, status=404)

    # -------- OWNERSHIP CHECK --------
    if str(order['user_id']) != str(user['_id']):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    # -------- ORDER STATUS CHECK --------
    if order['order_status'] in ['cancelled', 'shipped', 'delivered', 'expired']:
        return JsonResponse(
            {'error': 'Payment not allowed for this order'},
            status=400
        )

    # -------- ALREADY PAID CHECK --------
    if order['payment_status'] in ['submitted', 'paid']:
        return JsonResponse(
            {'error': 'Payment already submitted'},
            status=400
        )

    # -------- UNIQUE TRANSACTION CHECK --------
    if payments_col.find_one({'transaction_id': transaction_id}):
        return JsonResponse(
            {'error': 'Transaction ID already used'},
            status=400
        )

    # -------- 5-HOUR EXPIRY CHECK --------
    created_at = order['created_at']
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    expiry_time = created_at + timedelta(hours=5)

    if now > expiry_time:
        # -------- RESTOCK PRODUCTS --------
        for item in order['items']:
            products_col.update_one(
                {'_id': item['product_id']},
                {
                    '$inc': {
                        'stock': item['quantity'],
                        'sold_count': -item['quantity']
                    }
                }
            )

        # -------- MARK ORDER AS EXPIRED --------
        orders_col.update_one(
            {'_id': ObjectId(order_id)},
            {
                '$set': {
                    'order_status': 'expired',
                    'updated_at': now
                }
            }
        )

        return JsonResponse(
            {'error': 'Order expired. Products have been restocked.'},
            status=400
        )

    # -------- CREATE PAYMENT --------
    payment = {
        'order_id': ObjectId(order_id),
        'user_id': ObjectId(user['_id']),
        'method': 'bkash',
        'transaction_id': transaction_id,
        'status': 'submitted',
        'submitted_at': now,
        'verified_at': None
    }

    payments_col.insert_one(payment)

    # -------- UPDATE ORDER PAYMENT STATUS --------
    orders_col.update_one(
        {'_id': ObjectId(order_id)},
        {
            '$set': {
                'payment_status': 'submitted',
                'updated_at': now
            }
        }
    )

    return JsonResponse(
        {'message': 'Payment submitted successfully'},
        status=201
    )


