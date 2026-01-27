from .utils import hash_password,verify_password,generate_token
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from bson.objectid import ObjectId
from rest_framework import status
from datetime import datetime, timedelta,timezone
from django.conf import settings
import jwt
from config.mongo import db
from .current_user import get_current_user
from .utils import create_access_token, create_refresh_token
from config.permissions import is_user_admin, is_user_moderator
from math import ceil
from log.utils import login_log,logout_log,register_log,user_update_log,user_delete_log
from rest_framework.decorators import api_view

collection = db['user']
cart_col=db['carts']
order_col=db['orders']
payment_col=db['payments']
import os 
from dotenv import load_dotenv
load_dotenv()
MAX_LOGIN_ATTEMPTS = 5
LOCK_DURATION_MINUTES = 5


#user registration
@api_view(['POST'])
def register(request):

    if request.method == 'POST':

        body = json.loads(request.body)

        first_name = body.get("first_name")
        last_name = body.get("last_name")
        password = body.get("password")
        email = body.get('email')
        address=body.get('address')
        phone= body.get('phone')

        if first_name == None:

            return JsonResponse({"error":"Please enter a username"})
        
        if last_name == None:
            return JsonResponse({"error":"Please enter a username"})
        
        if email == None:
            return JsonResponse({"error":"please enter an email."})
        
        if password == None:

            return JsonResponse({"error":"please enter a password."})

        if len(password)<4:

            return JsonResponse({"error":"password is too short"})

        existing_email = collection.find_one({"email":email})
        
        if existing_email:
            return JsonResponse({"error": "email already exists"},status=400)

        hash_pass = hash_password(password)


        try:
            result =collection.insert_one({
            "first_name":first_name,
            "last_name":last_name,
            'email':email,
            "password":hash_pass,
            "logged_in":False,
            "role":"user",
            'address':address,
            'phone':phone,
            "refresh_tokens": [],
            'created_at':datetime.now(timezone.utc),
            "login_attempt":0,
            "timeout_untill":None
            })
            
            #loggin the registration
            user = collection.find_one({"_id": result.inserted_id})
            register_log(request,user)
            
        except Exception as e:
            return JsonResponse({"error":str(e)})
        

        return JsonResponse({
            "success":"user created successfully",
        },status=201)



#user login
@api_view(['POST'])
def login(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    try:
        body = json.loads(request.body or "{}")
        email = body.get("email")
        password = body.get("password")

        if not email or not password:
            return JsonResponse(
                {"error": "email and password are required"},
                status=400
            )

        user = collection.find_one({"email": email})
        if not user:
            return JsonResponse({"error": "Invalid credentials"}, status=401)

        now = datetime.now(timezone.utc)

        timeout_until = user.get("timeout_until")
        if timeout_until and timeout_until < now:
            # unlock user
            collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"login_attempt": 0, "timeout_until": None}}
            )
            user["login_attempt"] = 0
            timeout_until = None

        if timeout_until and now < timeout_until:
            remaining = int((timeout_until - now).total_seconds() // 60)
            return JsonResponse(
                {"error": f"Account locked. Try again in {remaining} minutes"},
                status=403
            )

        if not verify_password(password, user["password"]):
            attempts = user.get("login_attempt", 0) + 1

            update = {"login_attempt": attempts}

            if attempts >= MAX_LOGIN_ATTEMPTS:
                update["timeout_until"] = now + timedelta(minutes=LOCK_DURATION_MINUTES)

            collection.update_one({"_id": user["_id"]}, {"$set": update})

            return JsonResponse(
                {
                    "error": "Invalid credentials",
                    "attempts_left": max(0, MAX_LOGIN_ATTEMPTS - attempts)
                },
                status=401
            )

        # -------- SUCCESS --------
        access_token = create_access_token(user["_id"], user["role"])
        refresh_token, jti = create_refresh_token(user["_id"])

        collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "logged_in": True,
                    "login_attempt": 0,
                    "timeout_until": None
                },
                "$push": {"refresh_tokens": jti}
            }
        )

        login_log(request, user)

        safe_user = {
            "_id": str(user["_id"]),
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "email": user.get("email"),
            "role": user["role"]
        }

        return JsonResponse(
            {
                "message": "Login successful",
                "user": safe_user,
                "access_token": access_token,
                "refresh_token": refresh_token
            },
            status=200
        )

    except Exception as e:
        return JsonResponse(
            {"error": "Internal server error", "details": str(e)},
            status=500
        )

        
        
        




#user log out
@api_view(['POST'])
def logout(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    try:
        body = json.loads(request.body or "{}")
        refresh_token = body.get("refresh_token")

        if not refresh_token:
            return JsonResponse({"error": "refresh_token required"}, status=400)

        payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )

        if payload.get("type") != "refresh":
            return JsonResponse({"error": "Invalid token type"}, status=401)

        user_id = payload["sub"]
        jti = payload["jti"]

        user = collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return JsonResponse({"error": "User not found"}, status=404)

        # Idempotent logout
        collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {"logged_in": False},
                "$pull": {"refresh_tokens": jti}
            }
        )

        logout_log(request, user)

        return JsonResponse({"message": "Logged out successfully"}, status=200)

    except jwt.ExpiredSignatureError:
        return JsonResponse({"error": "Token expired"}, status=401)

    except jwt.InvalidTokenError:
        return JsonResponse({"error": "Invalid token"}, status=401)

    except Exception as e:
        return JsonResponse(
            {"error": "Internal server error", "details": str(e)},
            status=500
        )







#refresh token
@api_view(['POST'])
def refresh_token(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    body = json.loads(request.body)
    token = body.get("refresh_token")

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )

        if payload["type"] != "refresh":
            return JsonResponse({"error": "Invalid token"}, status=401)

        
        user = collection.find_one({"_id": ObjectId(payload["sub"])})
        
        user['_id'] = str(user['_id'])
        
        #safe user data
        safe_user = {
            "_id": user["_id"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "email": user.get("email"),
            "role": user["role"]
        }
        
        
        
        if user['logged_in'] == False:
            return JsonResponse({"error": "User is logged out"}, status=401)

        if not user or payload["jti"] not in user.get("refresh_tokens", []):
            return JsonResponse({"error": "Token revoked"}, status=401)

        access_token = create_access_token(user["_id"], user["role"])

        return JsonResponse({"access_token": access_token,"user":safe_user})

    except jwt.ExpiredSignatureError:
        return JsonResponse({"error": "Refresh token expired"}, status=401)
    except jwt.InvalidTokenError:
        return JsonResponse({"error": "Invalid token"}, status=401)


#modarator creator
@api_view(['PUT'])
def create_modarator_or_admin(request,user_id):
    
    
    
    if request.method != "PUT":
        return JsonResponse({"error": "POST method required"}, status=405)

    body = json.loads(request.body)
    user,error= get_current_user(request)
    
    
    
    
    if error:
        return JsonResponse({"error":error})
    
    if is_user_admin(user) == False:
        
        return JsonResponse({
            "error":"You are not authorized to do this action"
        })
        
    
    if user['logged_in'] == False:
        return JsonResponse({"error":"User is logged out"},status=401)
    
    role = body.get('role')
    
    
    if role not in ['admin','moderator']:
        return JsonResponse({"error":"role must be either 'admin' or 'moderator'"})

    #check if user exists
    updating_user = collection.find_one({"_id":ObjectId(user_id)})
    if not updating_user:
        return JsonResponse({"error":"User not found"},status=404)
    
    #update role
    try:
        result = collection.update_one(
            {"_id":ObjectId(user_id)},
            {"$set":{"role":role}}
        )
        
        if result.matched_count ==0:
            return JsonResponse({"error":"User not found"},status=404)
            
    except Exception as e:
            return JsonResponse({"error":str(e)})
        

    return JsonResponse({
            "success":"user created successfully",
        },status=201)
    
        

#for testing
@api_view(['GET'])
def test_data(request):
    
    user,error = get_current_user(request)
    
    
    
    if error:
        return JsonResponse({"error":error},status=401)
    
    if user['logged_in'] == False:
        return JsonResponse({"error":"User is logged out"},status=401)
    
    
    return JsonResponse({"user":user,"status":user['logged_in']})



#normal user update
@api_view(['GET', 'PUT'])
def update_user(request):
    
    if request.method !="PUT":
        
        if request.method =="GET":
            user, error = get_current_user(request)
            if error:
                return JsonResponse({"error": error}, status=401)
            if user['logged_in'] == False:
                return JsonResponse({"error": "User is logged out"}, status=401)
            
            user.pop("password", None)
            user.pop("refresh_tokens", None)
            user.pop("login_attempt", None)
            user.pop("timeout_untill", None)
            return JsonResponse({"user": user})
        return JsonResponse({"error":"PUT method required"},status=405)
    
    user,error = get_current_user(request)
    
    if error:
        
        return JsonResponse({"error":error},status=401)
    
    body = json.loads(request.body)
    first_name = body.get('first_name')
    last_name = body.get('last_name')
    address= body.get('address')
    phone = body.get('phone')
    email = body.get('email')
    
    update_fields = {}
    if first_name:
        update_fields['first_name']= first_name
    if last_name:
        update_fields['last_name']= last_name
    if address:
        update_fields['address']= address
    if phone:
        update_fields['phone']= phone
    if email:
        update_fields['email']= email
    if not update_fields:
        return JsonResponse({"error":"No fields to update"},status=400)
    
    collection.update_one(
        {"_id":ObjectId(user['_id'])},
        {"$set":update_fields}
    )
    #log the update
    updated_by = collection.find_one({"_id":ObjectId(user['_id'])})
    user_update_log(request, user,updated_by, update_fields)
    return JsonResponse({"message":"User updated successfully","updated_fields":update_fields,'user':user})




#admin user update other users
@api_view(['GET', 'PUT'])
def admin_update_user(request, user_id):

    # ---------- VALIDATE USER ID ----------
    try:
        user_object_id = ObjectId(user_id)
    except:
        return JsonResponse({"error": "Invalid user ID"}, status=400)

    # ---------- GET USER (ADMIN VIEW) ----------
    if request.method == "GET":
        user = collection.find_one({"_id": user_object_id})
        if not user:
            return JsonResponse({"error": "User not found"}, status=404)

        user_safe = dict(user)
        user_safe["_id"] = str(user_safe["_id"])

        # remove sensitive fields
        for field in ["password", "refresh_tokens", "login_attempt", "timeout_untill"]:
            user_safe.pop(field, None)

        return JsonResponse({"user": user_safe}, status=200)

    # ---------- ONLY PUT ALLOWED ----------
    if request.method != "PUT":
        return JsonResponse({"error": "PUT method required"}, status=405)

    # ---------- AUTHENTICATION ----------
    admin_user, error = get_current_user(request)
    if error:
        return JsonResponse({"error": error}, status=401)

    # ---------- AUTHORIZATION ----------
    if admin_user.get("role") != "admin" or not admin_user.get("logged_in"):
        return JsonResponse(
            {"error": "You are not authorized to perform this action"},
            status=403
        )

    # ---------- PARSE REQUEST BODY ----------
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    # ---------- ALLOWED FIELDS ----------
    allowed_fields = ["first_name","last_name", "address", "phone", "email", "role"]
    update_fields = {
        field: body[field]
        for field in allowed_fields
        if field in body and body[field]
    }

    if not update_fields:
        return JsonResponse({"error": "No valid fields to update"}, status=400)

    # ---------- CHECK USER EXISTS ----------
    user_before_update = collection.find_one({"_id": user_object_id})
    if not user_before_update:
        return JsonResponse({"error": "User not found"}, status=404)

    # ---------- UPDATE USER ----------
    collection.update_one(
        {"_id": user_object_id},
        {"$set": update_fields}
    )

    # ---------- LOG UPDATE ----------
    updated_by = collection.find_one({"_id": ObjectId(admin_user["_id"])})
    user_update_log(request, user_before_update, updated_by, update_fields)

    return JsonResponse(
        {
            "message": "User updated successfully",
            "updated_fields": update_fields
        },
        status=200
    )




#user deletion by admin
@api_view(['DELETE'])
def delete_user(request,user_id):
    
    if request.method != "DELETE":
        
        return JsonResponse({"error":"DELETE method required"},status=405)
    
    admin_user,error = get_current_user(request)
    
    if error:
        
        return JsonResponse({"error":error},status=401)
    
    if admin_user.get('role') != 'admin' and admin_user['logged_in'] == True:
        
        return JsonResponse({"error":"You are not authorized to perform this action"},status=403)
    
    
    result = collection.delete_one({"_id":ObjectId(user_id)})
    
    if result.deleted_count ==0:
        
        return JsonResponse({"error":"User not found"},status=404)
    
    #log deletion
    user = collection.find_one({"_id": ObjectId(user_id)})
    user_delete_log(request,user,admin_user)
    return JsonResponse({"message":"User deleted successfully"})


#admin user list all users
@api_view(['GET'])
def list_users(request):
    
    if request.method != "GET":
        
        return JsonResponse({"error":"GET method required"},status=405)
    
    admin_user,error = get_current_user(request)
    
    if error:
        
        return JsonResponse({"error":error},status=401)
    
    if admin_user.get('role') != 'admin' and admin_user['logged_in'] == True:
        
        return JsonResponse({"error":"You are not authorized to perform this action"},status=403)
    
    
    users_cursor = collection.find()
    users = []
    for user in users_cursor:
        user_safe = dict(user)
        user_safe["_id"] = str(user_safe["_id"])
        user_safe.pop("password", None)
        user_safe.pop("refresh_tokens", None)
        user_safe.pop("login_attempt", None)
        user_safe.pop("timeout_untill", None)
        users.append(user_safe)
    
    return JsonResponse({"users":users})

#admin user get single user details
@api_view(['GET'])
def get_user_details(request, user_id):

    # -------- METHOD CHECK --------
    if request.method != "GET":
        return JsonResponse({"error": "GET method required"}, status=405)

    #-------- AUTH --------
    admin_user, error = get_current_user(request)
    if error:
        return JsonResponse({"error": error}, status=401)

    if admin_user.get('role') != 'admin':
        return JsonResponse(
            {"error": "You are not authorized to perform this action"},
            status=403
        )

    # -------- GET USER --------
    user = collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        return JsonResponse({"error": "User not found"}, status=404)
    

    # -------- SAFE USER DATA --------
    user_safe = dict(user)
    user_safe["_id"] = str(user_safe["_id"])
    user_safe.pop("password", None)
    user_safe.pop("refresh_tokens", None)
    user_safe.pop("login_attempt", None)
    user_safe.pop("timeout_untill", None)

    # ================= CART INFO =================
    cart = cart_col.find_one({"user_id": str(user_id)})
    cart_info = {
        "items_count": len(cart["items"]) if cart else 0,
        "updated_at": cart.get("updated_at") if cart else None
    }

    # ================= QUERY PARAMS =================
    order_status = request.GET.get("order_status")
    payment_status = request.GET.get("payment_status")

    page = int(request.GET.get("page", 1))
    limit = int(request.GET.get("limit", 10))
    skip = (page - 1) * limit

    # ================= ORDERS =================
    order_query = {"user_id": ObjectId(user_id)}

    if order_status:
        order_query["order_status"] = order_status

    if payment_status:
        order_query["payment_status"] = payment_status

    total_orders = order_col.count_documents(order_query)

    orders_cursor = (
        order_col
        .find(order_query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    orders = []
    for order in orders_cursor:
        order["_id"] = str(order["_id"])
        order["user_id"] = str(order["user_id"])

        for item in order.get("items", []):
            item["product_id"] = str(item["product_id"])
            item["color_id"] = str(item["color_id"])
            item["size_id"] = str(item["size_id"])

        orders.append(order)

    # ================= PAYMENTS =================
    payment_page = int(request.GET.get("payment_page", 1))
    payment_limit = int(request.GET.get("payment_limit", 10))
    payment_skip = (payment_page - 1) * payment_limit

    payment_query = {"user_id": ObjectId(user_id)}
    if payment_status:
        payment_query["status"] = payment_status

    total_payments = payment_col.count_documents(payment_query)

    payments_cursor = (
        payment_col
        .find(payment_query)
        .sort("submitted_at", -1)
        .skip(payment_skip)
        .limit(payment_limit)
    )

    payments = []
    total_paid_amount = 0
    paid_count = 0
    submitted_count = 0

    for payment in payments_cursor:
        payment["_id"] = str(payment["_id"])
        payment["user_id"] = str(payment["user_id"])
        payment["order_id"] = str(payment["order_id"])

        if payment["status"] == "submitted":
            submitted_count += 1

        if payment["status"] == "paid":
            paid_count += 1
            order = order_col.find_one({"_id": ObjectId(payment["order_id"])})
            if order:
                total_paid_amount += order.get("total_price", 0)

        payments.append(payment)

    # ================= ANALYTICS =================
    completed_orders = order_col.count_documents({
        "user_id": ObjectId(user_id),
        "order_status": "completed"
    })

    cancelled_orders = order_col.count_documents({
        "user_id": ObjectId(user_id),
        "order_status": {"$in": ["cancelled", "expired"]}
    })

    avg_order_value = (
        round(total_paid_amount / paid_count, 2)
        if paid_count > 0 else 0
    )

    # ================= FINAL RESPONSE =================
    return JsonResponse({
        "user": user_safe,

        "cart": cart_info,

        "orders": {
            "data": orders,
            "pagination": {
                "page": page,
                "limit": limit,
                "total_orders": total_orders,
                "total_pages": ceil(total_orders / limit)
            }
        },

        "payments": {
            "data": payments,
            "pagination": {
                "page": payment_page,
                "limit": payment_limit,
                "total_payments": total_payments,
                "total_pages": ceil(total_payments / payment_limit)
            }
        },

        "analytics": {
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "cancelled_or_expired_orders": cancelled_orders,
            "total_payments": total_payments,
            "submitted_payments": submitted_count,
            "paid_payments": paid_count,
            "total_spent": total_paid_amount,
            "average_order_value": avg_order_value
        }

    }, status=200)
    
    
#user details by user
@api_view(['GET'])
def get_normal_user_details(request):

    # -------- METHOD CHECK --------
    if request.method != "GET":
        return JsonResponse({"error": "GET method required"}, status=405)

    #-------- AUTH --------
    user, error = get_current_user(request)
    if error:
        return JsonResponse({"error": error}, status=401)
    
    
    if user['logged_in'] == False:
        return JsonResponse({"error": "User is logged out"}, status=401)

    
    user_id = str(user["_id"])
    

    

    # -------- SAFE USER DATA --------
    user_safe = dict(user)
    user_safe["_id"] = str(user_safe["_id"])
    user_safe.pop("password", None)
    user_safe.pop("refresh_tokens", None)
    user_safe.pop("login_attempt", None)
    user_safe.pop("timeout_untill", None)

    # ================= CART INFO =================
    cart = cart_col.find_one({"user_id": str(user_id)})
    cart_info = {
        "items_count": len(cart["items"]) if cart else 0,
        "updated_at": cart.get("updated_at") if cart else None
    }

    # ================= QUERY PARAMS =================
    order_status = request.GET.get("order_status")
    payment_status = request.GET.get("payment_status")

    page = int(request.GET.get("page", 1))
    limit = int(request.GET.get("limit", 10))
    skip = (page - 1) * limit

    # ================= ORDERS =================
    order_query = {"user_id": ObjectId(user_id)}

    if order_status:
        order_query["order_status"] = order_status

    if payment_status:
        order_query["payment_status"] = payment_status

    total_orders = order_col.count_documents(order_query)

    orders_cursor = (
        order_col
        .find(order_query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    orders = []
    for order in orders_cursor:
        order["_id"] = str(order["_id"])
        order["user_id"] = str(order["user_id"])

        for item in order.get("items", []):
            item["product_id"] = str(item["product_id"])
            item["color_id"] = str(item["color_id"])
            item["size_id"] = str(item["size_id"])

        orders.append(order)

    # ================= PAYMENTS =================
    payment_page = int(request.GET.get("payment_page", 1))
    payment_limit = int(request.GET.get("payment_limit", 10))
    payment_skip = (payment_page - 1) * payment_limit

    payment_query = {"user_id": ObjectId(user_id)}
    if payment_status:
        payment_query["status"] = payment_status

    total_payments = payment_col.count_documents(payment_query)

    payments_cursor = (
        payment_col
        .find(payment_query)
        .sort("submitted_at", -1)
        .skip(payment_skip)
        .limit(payment_limit)
    )

    payments = []
    total_paid_amount = 0
    paid_count = 0
    submitted_count = 0

    for payment in payments_cursor:
        payment["_id"] = str(payment["_id"])
        payment["user_id"] = str(payment["user_id"])
        payment["order_id"] = str(payment["order_id"])

        if payment["status"] == "submitted":
            submitted_count += 1

        if payment["status"] == "paid":
            paid_count += 1
            order = order_col.find_one({"_id": ObjectId(payment["order_id"])})
            if order:
                total_paid_amount += order.get("total_price", 0)

        payments.append(payment)

    # ================= ANALYTICS =================
    completed_orders = order_col.count_documents({
        "user_id": ObjectId(user_id),
        "order_status": "completed"
    })

    cancelled_orders = order_col.count_documents({
        "user_id": ObjectId(user_id),
        "order_status": {"$in": ["cancelled", "expired"]}
    })

    avg_order_value = (
        round(total_paid_amount / paid_count, 2)
        if paid_count > 0 else 0
    )

    # ================= FINAL RESPONSE =================
    return JsonResponse({
        "user": user_safe,

        "cart": cart_info,

        "orders": {
            "data": orders,
            "pagination": {
                "page": page,
                "limit": limit,
                "total_orders": total_orders,
                "total_pages": ceil(total_orders / limit)
            }
        },

        "payments": {
            "data": payments,
            "pagination": {
                "page": payment_page,
                "limit": payment_limit,
                "total_payments": total_payments,
                "total_pages": ceil(total_payments / payment_limit)
            }
        },

        "analytics": {
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "cancelled_or_expired_orders": cancelled_orders,
            "total_payments": total_payments,
            "submitted_payments": submitted_count,
            "paid_payments": paid_count,
            "total_spent": total_paid_amount,
            "average_order_value": avg_order_value
        }

    }, status=200)
    
    
#admin user search users
@api_view(['GET'])
def search_users(request):

    if request.method != "GET":
        return JsonResponse({"error": "GET method required"}, status=405)

    query = {}

    # ---------- FILTER BY ROLE ----------
    role = request.GET.get("role")
    if role:
        if role not in ["user", "admin", "moderator"]:
            return JsonResponse({"error": "Invalid role"}, status=400)
        query["role"] = role

    # ---------- SEARCH BY USER ID ----------
    user_id = request.GET.get("user_id")
    if user_id:
        try:
            query["_id"] = ObjectId(user_id)
        except:
            return JsonResponse({"error": "Invalid user_id"}, status=400)

    # ---------- SEARCH BY USERNAME ----------
    first_name = request.GET.get("first_name")
    if first_name:
        query["first_name"] = {"$regex": first_name, "$options": "i"}
    last_name = request.GET.get("last_name")
    if last_name:
        query["last_name"] = {"$regex": last_name, "$options": "i"}

    # ---------- SEARCH BY EMAIL ----------
    email = request.GET.get("email")
    if email:
        query["email"] = {"$regex": email, "$options": "i"}

    # ---------- SEARCH BY PHONE ----------
    phone = request.GET.get("phone")
    if phone:
        query["phone"] = {"$regex": phone, "$options": "i"}

    # ---------- SORTING ----------
    sort_by = request.GET.get("sort_by", "created_at")
    order = request.GET.get("order", "desc")

    allowed_sort_fields = ["created_at", "first_name","last_name", "email", "role"]
    if sort_by not in allowed_sort_fields:
        return JsonResponse({"error": "Invalid sort field"}, status=400)

    sort_order = -1 if order == "desc" else 1

    # ---------- PAGINATION ----------
    try:
        page = int(request.GET.get("page", 1))
        limit = int(request.GET.get("limit", 10))
    except:
        return JsonResponse({"error": "Invalid pagination values"}, status=400)

    if page < 1 or limit < 1:
        return JsonResponse({"error": "Page and limit must be positive"}, status=400)

    skip = (page - 1) * limit

    total_users = collection.count_documents(query)

    users = (
        collection
        .find(query)
        .sort(sort_by, sort_order)
        .skip(skip)
        .limit(limit)
    )

    # ---------- CLEAN RESPONSE ----------
    user_list = []
    for user in users:
        user["_id"] = str(user["_id"])
        user.pop("password", None)
        user.pop("refresh_tokens", None)
        user.pop("login_attempt", None)
        user.pop("timeout_untill", None)
        user_list.append(user)

    return JsonResponse({
        "total": total_users,
        "page": page,
        "limit": limit,
        "total_pages": ceil(total_users / limit),
        "users": user_list
    }, status=200)
