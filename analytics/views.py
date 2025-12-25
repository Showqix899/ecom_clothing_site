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
def product_analytics_revenue_dashboard(request):
    user, err = admin_auth(request)
    if err:
        return err

    # ---------- TOTAL REVENUE ----------
    total_revenue_data = list(orders_col.aggregate([
        {'$match': {'payment_status': 'paid'}},
        {'$group': {'_id': None, 'total_revenue': {'$sum': '$total_price'}}}
    ]))

    total_revenue = (
        total_revenue_data[0]['total_revenue']
        if total_revenue_data else 0
    )

    # ---------- REVENUE SUMMARY ----------
    revenue_summary = list(orders_col.aggregate([
        {'$group': {
            '_id': '$payment_status',
            'revenue': {'$sum': '$total_price'},
            'orders': {'$sum': 1}
        }}
    ]))

    # ---------- PRODUCT REVENUE ----------
    product_revenue = list(orders_col.aggregate([
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

    # ---------- CATEGORY REVENUE ----------
    category_revenue = list(orders_col.aggregate([
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

    # ---------- PRODUCT SOLD COUNT ----------
    product_sold_count = list(orders_col.aggregate([
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
        'total_revenue': total_revenue,
        'revenue_summary': serialize_mongo(revenue_summary),
        'product_revenue': serialize_mongo(product_revenue),
        'category_revenue': serialize_mongo(category_revenue),
        'product_sold_count': serialize_mongo(product_sold_count),
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





## ==================== order DASHBOARD ANALYTICS ====================
@api_view(['GET'])
def analytics_dashboard(request):
    user, err = admin_auth(request)
    if err:
        return err

    # ---------- 1. ORDER STATUS DISTRIBUTION ----------
    order_status_data = list(orders_col.aggregate([
        {'$group': {'_id': '$order_status', 'count': {'$sum': 1}}}
    ]))

    # ---------- 2. AVERAGE ORDER VALUE ----------
    aov_data = list(orders_col.aggregate([
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

    average_order_value = (
        aov_data[0]['average_order_value']
        if aov_data else 0
    )

    # ---------- 3. TOTAL REVENUE ----------
    total_revenue_data = list(orders_col.aggregate([
        {'$match': {'payment_status': 'paid'}},
        {'$group': {'_id': None, 'total_revenue': {'$sum': '$total_price'}}}
    ]))

    total_revenue = (
        total_revenue_data[0]['total_revenue']
        if total_revenue_data else 0
    )

    # ---------- 4. REVENUE SUMMARY ----------
    revenue_summary_data = list(orders_col.aggregate([
        {'$group': {
            '_id': '$payment_status',
            'revenue': {'$sum': '$total_price'}
        }}
    ]))

    # ---------- FINAL RESPONSE ----------
    return JsonResponse({
        'order_status_distribution': serialize_mongo(order_status_data),
        'average_order_value': average_order_value,
        'total_revenue': total_revenue,
        'revenue_summary': serialize_mongo(revenue_summary_data),
    })
    

# ==================== TIME-BASED ANALYTICS ==================== 
@api_view(['GET'])
def analytics_time_based(request):
    user, err = admin_auth(request)
    if err:
        return err

    analytics_type = request.GET.get('type', 'daily')
    start = request.GET.get('start_date')
    end = request.GET.get('end_date')

    match_stage = {}
    if start and end:
        match_stage['created_at'] = {
            '$gte': datetime.fromisoformat(start),
            '$lte': datetime.fromisoformat(end)
        }

    # -------- GROUP FORMAT --------
    if analytics_type == 'daily':
        date_group = {
            'year': {'$year': '$created_at'},
            'month': {'$month': '$created_at'},
            'day': {'$dayOfMonth': '$created_at'}
        }
    elif analytics_type == 'weekly':
        date_group = {
            'year': {'$year': '$created_at'},
            'week': {'$week': '$created_at'}
        }
    elif analytics_type == 'monthly':
        date_group = {
            'year': {'$year': '$created_at'},
            'month': {'$month': '$created_at'}
        }
    elif analytics_type == 'yearly':
        date_group = {
            'year': {'$year': '$created_at'}
        }
    else:
        return JsonResponse({'error': 'Invalid type'}, status=400)

    pipeline = [
        {'$match': match_stage},
        {'$group': {
            '_id': date_group,
            'total_orders': {'$sum': 1},
            'total_revenue': {
                '$sum': {
                    '$cond': [
                        {'$eq': ['$payment_status', 'paid']},
                        '$total_price',
                        0
                    ]
                }
            }
        }},
        {'$project': {
            '_id': 0,
            'time': '$_id',
            'total_orders': 1,
            'total_revenue': 1,
            'average_order_value': {
                '$cond': [
                    {'$eq': ['$total_orders', 0]},
                    0,
                    {'$divide': ['$total_revenue', '$total_orders']}
                ]
            }
        }},
        {'$sort': {'time.year': 1, 'time.month': 1, 'time.day': 1}}
    ]

    time_data = list(orders_col.aggregate(pipeline))

    # -------- ORDER STATUS SUMMARY --------
    status_pipeline = [
        {'$match': match_stage},
        {'$group': {
            '_id': '$payment_status',
            'count': {'$sum': 1},
            'revenue': {'$sum': '$total_price'}
        }}
    ]

    status_data = list(orders_col.aggregate(status_pipeline))

    # -------- OVERALL SUMMARY --------
    summary_pipeline = [
        {'$match': match_stage},
        {'$group': {
            '_id': None,
            'total_orders': {'$sum': 1},
            'total_revenue': {
                '$sum': {
                    '$cond': [
                        {'$eq': ['$payment_status', 'paid']},
                        '$total_price',
                        0
                    ]
                }
            }
        }}
    ]

    summary = list(orders_col.aggregate(summary_pipeline))

    return JsonResponse({
        'type': analytics_type,
        'time_based_data': serialize_mongo(time_data),
        'order_status_summary': serialize_mongo(status_data),
        'summary': serialize_mongo(summary[0] if summary else {})
    })