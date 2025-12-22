from django.shortcuts import render
from bson import ObjectId
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
import json
from datetime import datetime
from config.permissions import is_user_admin,is_user_moderator
from accounts.current_user import get_current_user


# Create your views here.
from config.mongo import db

log_col=db['logs']



def serialize_any(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, list):
        return [serialize_any(item) for item in obj]
    if isinstance(obj, dict):
        return {key: serialize_any(value) for key, value in obj.items()}
    return obj


def list_logs(request):

    # ---------- METHOD ----------
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # ---------- AUTH ----------
    user, error = get_current_user(request)
    if error:
        return JsonResponse({"error": error}, status=401)

    if not is_user_admin(user):
        return JsonResponse({"error": "Unauthorized"}, status=403)

    # ---------- PAGINATION ----------
    try:
        page = int(request.GET.get("page", 1))
        limit = int(request.GET.get("limit", 10))
        if page < 1 or limit < 1:
            raise ValueError
    except ValueError:
        return JsonResponse({"error": "Invalid pagination params"}, status=400)

    skip = (page - 1) * limit

    # ---------- COUNT ----------
    total = log_col.count_documents({})

    # ---------- FETCH ----------
    cursor = (
        log_col.find()
        .sort("timestamp", -1)
        .skip(skip)
        .limit(limit)
    )

    logs = [serialize_any(log) for log in cursor]

    total_pages = (total + limit - 1) // limit

    # ---------- RESPONSE ----------
    return JsonResponse({
        "total": total,
        "pages": total_pages,
        "current_page": page,
        "limit": limit,
        "results": logs
    })
    
    
    
#get a log details
@csrf_exempt
def get_log(request, log_id):

    
    user,error = get_current_user(request)
    
    if error:
        return JsonResponse({"error":error})
    
    if not (is_user_admin(user)):
        return JsonResponse({"error":"You are not authorized to do this action"})
    
    
    try:
        log = log_col.find_one({"_id": ObjectId(log_id)})
        if not log:
            return JsonResponse({"error": "Log not found"}, status=404)

        log["_id"] = str(log["_id"])
        log["timestamp"] = log["timestamp"].isoformat()

        return JsonResponse(log)

    except Exception as e:
        return JsonResponse({"error": f"Invalid log ID {str(e)}"}, status=400)




#update log
@csrf_exempt
def update_log(request, log_id):
    
    if request.method not in ['PUT', 'PATCH']:
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    user,error = get_current_user(request)
    
    if error:
        return JsonResponse({"error":error})
    
    if not (is_user_admin(user)):
        return JsonResponse({"error":"You are not authorized to do this action"})
    
    
    try:
        data = json.loads(request.body)

        update_data = {
            k: v for k, v in data.items()
            if k in [
                "actor_id", "actor_type", "action",
                "entity_type", "entity_id",
                "entity_name", "description", "metadata"
            ]
        }

        result = log_col.update_one(
            {"_id": ObjectId(log_id)},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            return JsonResponse({"error": "Log not found"}, status=404)

        return JsonResponse({"message": "Log updated"})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)



#delete log
@csrf_exempt
def delete_log(request, log_id):
    
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    user,error = get_current_user(request)
    
    if error:
        return JsonResponse({"error":error})
    
    if not (is_user_admin(user)):
        return JsonResponse({"error":"You are not authorized to do this action"})
    
    try:
        result = log_col.delete_one({"_id": ObjectId(log_id)})

        if result.deleted_count == 0:
            return JsonResponse({"error": "Log not found"}, status=404)

        return JsonResponse({"message": "Log deleted"})

    except Exception:
        return JsonResponse({"error": "Invalid log ID"}, status=400)


#log filter search
@csrf_exempt
def log_search_filter(request):

    if request.method != 'GET':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    query = {}

    log_id = request.GET.get('log_id')
    entity_type = request.GET.get('entity_type')
    entity_id = request.GET.get('entity_id')
    actor_id = request.GET.get('actor_id')
    actor_type = request.GET.get('actor_type')
    actor_name = request.GET.get('actor_name')
    action = request.GET.get('action')

    if log_id:
        query["_id"] = ObjectId(log_id)   # IMPORTANT
    if entity_type:
        query["entity_type"] = entity_type
    if entity_id:
        query["entity_id"] = entity_id
    if actor_id:
        query["actor_id"] = actor_id
    if actor_type:
        query["actor_type"] = actor_type
    if actor_name:
        query["actor_name"] = actor_name
    
    if action:
        query['action'] = action

    try:
        cursor = log_col.find(query).sort("timestamp", -1)
        logs = [serialize_any(log) for log in cursor]

        return JsonResponse({
            "count": len(logs),
            "results": logs
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)