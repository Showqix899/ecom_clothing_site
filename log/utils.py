from datetime import datetime,timedelta,timezone
from config.mongo import db
log_collection = db["logs"]



#for user login
def login_log(request, user):
    
    try:
        log_entry = {
        "done_by": "user",
        "action": "login",
        "user_id": str(user["_id"]),
        "username": user["username"],
        "timestamp": datetime.now(timezone.utc)
        }
        log_collection.insert_one(log_entry)
    except:
        pass
    

#for user logout
def logout_log(request, user):
    
    try:
        log_entry = {
        "done_by": "user",
        "action": "logout",
        "user_id": str(user["_id"]),
        "username": user["username"],
        "timestamp": datetime.now(timezone.utc)
        }
        log_collection.insert_one(log_entry)
    except Exception as e:
        print(e)
        
    
 
#for user registration   
def register_log(request, user):
    
    try:
        log_entry = {
        "done_by": "user",
        "action": "register",
        "user_id": str(user["_id"]),
        "username": user["username"],
        "timestamp": datetime.now(timezone.utc)
        }
        log_collection.insert_one(log_entry)
    except:
        pass


#for user deletion
def user_delete_log(request, user,deleted_by):
    
    try:
        log_entry = {
        "done_by": str(deleted_by['_id']),
        "action": "delete",
        "user_id": str(user["_id"]),
        "username": user["username"],
        "timestamp": datetime.now(timezone.utc)
        }
        log_collection.insert_one(log_entry)
    except:
        pass
    
#for user update
def user_update_log(request, user,updated_by, updated_fields):
    
    try:
        log_entry = {
        "done_by": str(updated_by['_id']),
        "action": "update",
        "user_id": str(user["_id"]),
        "username": user["username"],
        "updated_fields": updated_fields,
        "timestamp": datetime.now(timezone.utc)
        }
        log_collection.insert_one(log_entry)
    except:
        pass