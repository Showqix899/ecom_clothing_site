from django.http import JsonResponse
from datetime import datetime, timedelta
from rest_framework.decorators import api_view
from config.permissions import is_user_admin, is_user_moderator
from accounts.current_user import get_current_user
from config.mongo import db
from bson import ObjectId

orders_col = db['orders']
products_col = db['products']
categories_col = db['categories']


# ==================== OBJECTID SERIALIZER ====================
def serialize_mongo(obj):
    if isinstance(obj, list):
        return [serialize_mongo(item) for item in obj]

    if isinstance(obj, dict):
        return {
            key: serialize_mongo(value)
            for key, value in obj.items()
        }

    if isinstance(obj, ObjectId):
        return str(obj)

    return obj


# ==================== COMMON AUTH ====================
def admin_auth(request):
    user, error = get_current_user(request)
    if error:
        return None, JsonResponse({'error': error}, status=401)

    if not (is_user_admin(user) or is_user_moderator(user)):
        return None, JsonResponse({'error': 'Forbidden'}, status=403)

    return user, None


# ==================== TOTAL ORDERS ====================
@api_view(['GET'])
def analytics_total_orders(request):
    user, err = admin_auth(request)
    if err:
        return err

    start = request.GET.get('start_date')
    end = request.GET.get('end_date')

    query = {}
    if start and end:
        query['created_at'] = {
            '$gte': datetime.fromisoformat(start),
            '$lte': datetime.fromisoformat(end)
        }

    return JsonResponse({
        'total_orders': orders_col.count_documents(query)
    })


# ==================== ORDER STATUS ====================
@api_view(['GET'])
def analytics_order_status_distribution(request):
    user, err = admin_auth(request)
    if err:
        return err

    data = list(orders_col.aggregate([
        {'$group': {'_id': '$order_status', 'count': {'$sum': 1}}}
    ]))

    return JsonResponse({
        'order_status_distribution': serialize_mongo(data)
    })


# ==================== AVERAGE ORDER VALUE ====================
@api_view(['GET'])
def analytics_average_order_value(request):
    user, err = admin_auth(request)
    if err:
        return err

    data = list(orders_col.aggregate([
        {'$match': {'payment_status': 'paid'}},
        {'$group': {
            '_id': None,
            'total': {'$sum': '$total_price'},
            'count': {'$sum': 1}
        }},
        {'$project': {
            '_id': 0,
            'average_order_value': {
                '$cond': [
                    {'$eq': ['$count', 0]},
                    0,
                    {'$divide': ['$total', '$count']}
                ]
            }
        }}
    ]))

    return JsonResponse({
        'average_order_value': data[0]['average_order_value'] if data else 0
    })


# ==================== TOTAL REVENUE ====================
@api_view(['GET'])
def analytics_total_revenue(request):
    user, err = admin_auth(request)
    if err:
        return err

    data = list(orders_col.aggregate([
        {'$match': {'payment_status': 'paid'}},
        {'$group': {'_id': None, 'total_revenue': {'$sum': '$total_price'}}}
    ]))

    return JsonResponse({
        'total_revenue': data[0]['total_revenue'] if data else 0
    })


# ==================== REVENUE SUMMARY ====================
@api_view(['GET'])
def analytics_revenue_summary(request):
    user, err = admin_auth(request)
    if err:
        return err

    data = list(orders_col.aggregate([
        {'$group': {
            '_id': '$payment_status',
            'revenue': {'$sum': '$total_price'}
        }}
    ]))

    return JsonResponse({
        'revenue_summary': serialize_mongo(data)
    })


# ==================== PRODUCT REVENUE ====================
@api_view(['GET'])
def analytics_product_revenue(request):
    user, err = admin_auth(request)
    if err:
        return err

    data = list(orders_col.aggregate([
        {'$match': {'payment_status': 'paid'}},
        {'$unwind': '$items'},
        {'$group': {
            '_id': '$items.product_id',
            'product_name': {'$first': '$items.name'},
            'revenue': {'$sum': '$items.subtotal'},
            'sold_qty': {'$sum': '$items.quantity'}
        }},
        {'$sort': {'revenue': -1}}
    ]))

    return JsonResponse({
        'product_revenue': serialize_mongo(data)
    })


# ==================== CATEGORY REVENUE ====================
@api_view(['GET'])
def analytics_category_revenue(request):
    user, err = admin_auth(request)
    if err:
        return err

    data = list(orders_col.aggregate([
        {'$match': {'payment_status': 'paid'}},
        {'$unwind': '$items'},
        {'$lookup': {
            'from': 'products',
            'localField': 'items.product_id',
            'foreignField': '_id',
            'as': 'product'
        }},
        {'$unwind': '$product'},
        {'$group': {
            '_id': '$product.category_id',
            'revenue': {'$sum': '$items.subtotal'}
        }},
        {'$sort': {'revenue': -1}}
    ]))

    return JsonResponse({
        'category_revenue': serialize_mongo(data)
    })


# ==================== PRODUCT SOLD COUNT ====================
@api_view(['GET'])
def analytics_product_sold_count(request):
    user, err = admin_auth(request)
    if err:
        return err

    data = list(orders_col.aggregate([
        {'$match': {'payment_status': 'paid'}},
        {'$unwind': '$items'},
        {'$group': {
            '_id': '$items.product_id',
            'product_name': {'$first': '$items.name'},
            'sold_count': {'$sum': '$items.quantity'}
        }},
        {'$sort': {'sold_count': -1}}
    ]))

    return JsonResponse({
        'product_sold_count': serialize_mongo(data)
    })


# ==================== EXPIRED ORDERS ====================
@api_view(['GET'])
def analytics_expired_orders(request):
    user, err = admin_auth(request)
    if err:
        return err

    expiry_minutes = int(request.GET.get('minutes', 30))
    expiry_time = datetime.now(timedelta.utc) - timedelta(minutes=expiry_minutes)

    data = list(orders_col.find(
        {
            'payment_status': 'pending',
            'created_at': {'$lte': expiry_time}
        },
        {'items': 0}
    ))

    return JsonResponse({
        'expired_orders': serialize_mongo(data)
    })


# ==================== EXPIRED ORDER ITEMS ====================
@api_view(['GET'])
def analytics_expired_order_items(request):
    user, err = admin_auth(request)
    if err:
        return err

    expiry_minutes = int(request.GET.get('minutes', 30))
    expiry_time = datetime.utcnow() - timedelta(minutes=expiry_minutes)

    data = list(orders_col.aggregate([
        {'$match': {
            'payment_status': 'pending',
            'created_at': {'$lte': expiry_time}
        }},
        {'$unwind': '$items'},
        {'$project': {
            '_id': 0,
            'order_id': '$_id',
            'product_id': '$items.product_id',
            'product_name': '$items.name',
            'quantity': '$items.quantity',
            'subtotal': '$items.subtotal'
        }}
    ]))

    return JsonResponse({
        'expired_order_items': serialize_mongo(data)
    })
