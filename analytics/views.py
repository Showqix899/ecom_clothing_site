from django.http import JsonResponse
from datetime import datetime
from rest_framework.decorators import api_view
from bson import ObjectId

from config.mongo import db
from config.permissions import is_user_admin, is_user_moderator
from accounts.current_user import get_current_user


# ==================== COLLECTIONS ====================
orders_col = db['orders']
products_col = db['products']
categories_col = db['categories']


# ==================== CONSTANTS ====================
PAID_MATCH = {'payment_status': 'paid'}

PAID_CONFIRMED_MATCH = {
    'payment_status': 'paid',
    'order_status': 'confirmed'
}



# ==================== OBJECTID SERIALIZER ====================
def serialize_mongo(obj):
    if isinstance(obj, list):
        return [serialize_mongo(item) for item in obj]

    if isinstance(obj, dict):
        return {k: serialize_mongo(v) for k, v in obj.items()}

    if isinstance(obj, ObjectId):
        return str(obj)

    return obj


# ==================== ADMIN AUTH ====================
def admin_auth(request):
    user, error = get_current_user(request)
    if error:
        return None, JsonResponse({'error': error}, status=401)

    if not (is_user_admin(user) or is_user_moderator(user)):
        return None, JsonResponse({'error': 'Forbidden'}, status=403)

    return user, None


# ==================== DATE FILTER HELPER ====================
def build_date_match(start, end):
    if start and end:
        return {
            'created_at': {
                '$gte': datetime.fromisoformat(start),
                '$lte': datetime.fromisoformat(end)
            }
        }
    return {}


# =====================================================
# ==================== DASHBOARD ======================
# =====================================================
@api_view(['GET'])
def analytics_dashboard(request):
    """
    Combined analytics for admin dashboard:
    - Order status distribution
    - Total revenue (confirmed + paid)
    - Pending revenue
    - Canceled revenue
    - Average order value (confirmed + paid)
    - Revenue summary
    """

    user, err = admin_auth(request)
    if err:
        return err

    pipeline = [
        {
            '$facet': {

                # ---------- ORDER STATUS DISTRIBUTION ----------
                'order_status_distribution': [
                    {'$group': {
                        '_id': '$order_status',
                        'count': {'$sum': 1}
                    }}
                ],

                # ---------- TOTAL REVENUE (CONFIRMED + PAID) ----------
                'total_revenue': [
                    {'$match': {
                        'order_status': 'confirmed',
                        'payment_status': 'paid'
                    }},
                    {'$group': {
                        '_id': None,
                        'value': {'$sum': '$total_price'}
                    }}
                ],

                # ---------- PENDING REVENUE (PENDING + PAID) ----------
                'pending_revenue': [
                    {'$match': {
                        'order_status': 'pending',
                        'payment_status': 'paid'
                    }},
                    {'$group': {
                        '_id': None,
                        'value': {'$sum': '$total_price'}
                    }}
                ],

                # ---------- CANCELED REVENUE ----------
                'canceled_revenue': [
                    {'$match': {
                        'order_status': 'cancelled'
                    }},
                    {'$group': {
                        '_id': None,
                        'value': {'$sum': '$total_price'}
                    }}
                ],

                # ---------- AVERAGE ORDER VALUE (CONFIRMED + PAID) ----------
                'average_order_value': [
                    {'$match': {
                        'order_status': 'confirmed',
                        'payment_status': 'paid'
                    }},
                    {'$group': {
                        '_id': None,
                        'total': {'$sum': '$total_price'},
                        'count': {'$sum': 1}
                    }},
                    {'$project': {
                        '_id': 0,
                        'value': {
                            '$cond': [
                                {'$eq': ['$count', 0]},
                                0,
                                {'$divide': ['$total', '$count']}
                            ]
                        }
                    }}
                ],

                # ---------- REVENUE SUMMARY ----------
                'revenue_summary': [
                    {'$group': {
                        '_id': {
                            'payment_status': '$payment_status',
                            'order_status': '$order_status'
                        },
                        'revenue': {'$sum': '$total_price'},
                        'orders': {'$sum': 1}
                    }}
                ]
            }
        }
    ]

    data = list(orders_col.aggregate(pipeline))[0]

    return JsonResponse({
        'order_status_distribution': serialize_mongo(
            data['order_status_distribution']
        ),

        'total_revenue': (
            data['total_revenue'][0]['value']
            if data['total_revenue'] else 0
        ),

        'pending_revenue': (
            data['pending_revenue'][0]['value']
            if data['pending_revenue'] else 0
        ),

        'canceled_revenue': (
            data['canceled_revenue'][0]['value']
            if data['canceled_revenue'] else 0
        ),

        'average_order_value': (
            data['average_order_value'][0]['value']
            if data['average_order_value'] else 0
        ),

        'revenue_summary': serialize_mongo(data['revenue_summary']),
    })
# =====================================================
# ============== PRODUCT & CATEGORY ===================
# =====================================================
@api_view(['GET'])
def analytics_product_dashboard(request):
    """
    Product-based analytics:
    - Product revenue
    - Product sold count
    - Category revenue
    """

    user, err = admin_auth(request)
    if err:
        return err

    pipeline = [
        {'$match': PAID_MATCH},
        {'$unwind': '$items'},
        {
            '$facet': {
                # ---------- PRODUCT REVENUE ----------
                'product_revenue': [
                    {'$group': {
                        '_id': '$items.product_id',
                        'product_name': {'$first': '$items.name'},
                        'revenue': {'$sum': '$items.subtotal'},
                        'sold_qty': {'$sum': '$items.quantity'}
                    }},
                    {'$sort': {'revenue': -1}}
                ],

                # ---------- PRODUCT SOLD COUNT ----------
                'product_sold_count': [
                    {'$group': {
                        '_id': '$items.product_id',
                        'product_name': {'$first': '$items.name'},
                        'sold_count': {'$sum': '$items.quantity'}
                    }},
                    {'$sort': {'sold_count': -1}}
                ],

                # ---------- CATEGORY REVENUE ----------
                'category_revenue': [
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
                ]
            }
        }
    ]

    data = list(orders_col.aggregate(pipeline))[0]

    return JsonResponse({
        'product_revenue': serialize_mongo(data['product_revenue']),
        'product_sold_count': serialize_mongo(data['product_sold_count']),
        'category_revenue': serialize_mongo(data['category_revenue']),
    })


# =====================================================
# ================ TIME BASED ANALYTICS ===============
# =====================================================
@api_view(['GET'])
def analytics_time_based(request):
    """
    Time-based analytics:
    type = daily | weekly | monthly | yearly
    """

    user, err = admin_auth(request)
    if err:
        return err

    analytics_type = request.GET.get('type', 'daily')
    start = request.GET.get('start_date')
    end = request.GET.get('end_date')

    match_stage = build_date_match(start, end)

    # ---------- DATE GROUP ----------
    if analytics_type == 'daily':
        date_group = {
            'year': {'$year': '$created_at'},
            'month': {'$month': '$created_at'},
            'day': {'$dayOfMonth': '$created_at'}
        }
        sort_stage = {'time.year': 1, 'time.month': 1, 'time.day': 1}

    elif analytics_type == 'weekly':
        date_group = {
            'year': {'$year': '$created_at'},
            'week': {'$week': '$created_at'}
        }
        sort_stage = {'time.year': 1, 'time.week': 1}

    elif analytics_type == 'monthly':
        date_group = {
            'year': {'$year': '$created_at'},
            'month': {'$month': '$created_at'}
        }
        sort_stage = {'time.year': 1, 'time.month': 1}

    elif analytics_type == 'yearly':
        date_group = {
            'year': {'$year': '$created_at'}
        }
        sort_stage = {'time.year': 1}

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
        {'$sort': sort_stage}
    ]

    data = list(orders_col.aggregate(pipeline))

    return JsonResponse({
        'type': analytics_type,
        'time_based_data': serialize_mongo(data)
    })
