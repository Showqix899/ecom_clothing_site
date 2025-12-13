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

collection = db['user']


#user registration
@csrf_exempt
def register(request):

    if request.method == 'POST':

        body = json.loads(request.body)

        username = body.get("username")
        password = body.get("password")
        email = body.get('email')
        address=body.get('address')
        phone= body.get('phone')

        if username == None:

            return JsonResponse({"error":"Please enter a username"})
        
        if password == None:

            return JsonResponse({"error":"please enter a password."})

        if len(password)<4:

            return JsonResponse({"error":"password is too short"})

        existing = collection.find_one({"username":username})

        if existing:
            return JsonResponse({"error": "username already exists"},status=400)
        

        hash_pass = hash_password(password)


        try:
            collection.insert_one({
            "username":username,
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
            
        except Exception as e:
            return JsonResponse({"error":str(e)})
        

        return JsonResponse({
            "success":"user created successfully",
        },status=201)



#user login
@csrf_exempt
def login(request):

    if request.method == "POST":

        body = json.loads(request.body)

        username = body.get("username")
        password = body.get("password")

        user = collection.find_one({"username":username})

        if not user:
            return JsonResponse({"error":"invalid username"},status=400)
        
        now = datetime.now(timezone.utc)

        timeout_untill = user.get("timeout_untill")

        if timeout_untill and timeout_untill.tzinfo is None:

            timeout_untill = timeout_untill.replace(tzinfo=timezone.utc)

        if timeout_untill and now <timeout_untill:
            remaining = int((timeout_untill-now).total_seconds()//60)

            return JsonResponse({
                "error":f'You are blocked. Try again after {remaining} minutes'
            })
        
        if not verify_password(password,user['password']):

            new_attempt = user['login_attempt']+1

            if new_attempt>=5:
                lock_time = now+timedelta(minutes=5)
                collection.update_one(
                    {"_id":user["_id"]},
                    {
                        "$set":{
                            "login_attempt":5,
                            "timeout_untill":lock_time
                        }
                    }
                )

                return JsonResponse({
                    "error":"Too many failed attempts. You are blocked for 5 minutes"
                },status = 403)
        

            collection.update_one(
                {"_id":user['_id']},
                {"$set":{
                    "login_attempt":new_attempt
                }}
            )

            return JsonResponse({
                "error":f'Invalid password. Attempt left: {5 -new_attempt}'
            },status=400)
        
        access_token = create_access_token(user["_id"], user["role"])
        refresh_token, jti = create_refresh_token(user["_id"])
        
        collection.update_one(
            {"_id":user["_id"]},
            {"$set":{
                "logged_in":True,
                "login_attempt":0,
                "timeout_untill":None
            },
             "$push":{
                 "refresh_tokens":jti
             }
             }
        )

        user['_id']=str(user['_id'])
        
        return JsonResponse({
            "user":user,
            "access_token":access_token,
            "refresh_token":refresh_token,
            "message": "Login successful",
        },status=200)
        
        
        

# @csrf_exempt
# def logout(request,username):
     
#     user = collection.find_one({"username":username})

#     if user is None:
         
#         return JsonResponse({"error":"username not found"})

#     if user['logged_in']==False:
         
#         return JsonResponse({"error":"user is not authenticated"})
     
#     collection.update_one(
#         {"_id":user["_id"]},
#         {"$set":{"logged_in":False}}
#     )

#     return JsonResponse({"message":"user successfully logged out"})



#user log out
@csrf_exempt
def logout(request):
    body = json.loads(request.body)
    refresh_token = body.get("refresh_token")

    try:
        payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )

        collection.update_one(
            {"_id": ObjectId(payload["sub"])},
            {"$pull": {"refresh_tokens": payload["jti"]}}
        )

        return JsonResponse({"message": "Logged out successfully"})

    except jwt.InvalidTokenError:
        return JsonResponse({"error": "Invalid token"}, status=401)






#refresh token
@csrf_exempt
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

        if not user or payload["jti"] not in user.get("refresh_tokens", []):
            return JsonResponse({"error": "Token revoked"}, status=401)

        access_token = create_access_token(user["_id"], user["role"])

        return JsonResponse({"access_token": access_token})

    except jwt.ExpiredSignatureError:
        return JsonResponse({"error": "Refresh token expired"}, status=401)
    except jwt.InvalidTokenError:
        return JsonResponse({"error": "Invalid token"}, status=401)


#modarator creator
@csrf_exempt
def create_modarator(request):
    
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    body = json.loads(request.body)
    role = None
    user,error= get_current_user(request)
    
    
    if error:
        return JsonResponse({"error":error})
    role = user.get('role')
    
    
    if role != "admin":
        
        return JsonResponse({
            "error":"You are not authorized to do this action"
        })
        
    username = body.get("username")
    password = body.get("password")
    email = body.get('email')
    address=body.get('address')
    phone= body.get('phone')

    
    hash_pass = hash_password(password)
    
    if username == None:

            return JsonResponse({"error":"Please enter a username"})
        
    if password == None:

            return JsonResponse({"error":"please enter a password."})

    if len(password)<4:

            return JsonResponse({"error":"password is too short"})
        
    if phone == None:

            return JsonResponse({"error":"phone number is required"})

    existing = collection.find_one({"username":username})

    if existing:
            return JsonResponse({"error": "username already exists"},status=400)
        

    hash_pass = hash_password(password)


    try:
            collection.insert_one({
            "username":username,
            'email':email,
            "password":hash_pass,
            "logged_in":False,
            "role":"moderator",
            'address':address,
            'phone':phone,
            "refresh_tokens": [],
            'created_at':datetime.now(timezone.utc),
            "login_attempt":0,
            "timeout_untill":None
        })
            
    except Exception as e:
            return JsonResponse({"error":str(e)})
        

    return JsonResponse({
            "success":"user created successfully",
        },status=201)
    
        

#for testing
@csrf_exempt
def test_data(request):
    
    user,error = get_current_user(request)
    
    
    if error:
        return JsonResponse({"error":error},status=401)
    
    
    return JsonResponse({"user":user})