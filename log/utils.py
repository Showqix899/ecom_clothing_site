from datetime import datetime, timezone
from config.mongo import db
from django.http import JsonResponse

log_collection = db["logs"]


###========= user logging functions================###


# for user login
def login_log(request, user):
    try:
        log_entry = {
            "actor_id": str(user["_id"]),
            "actor_type": "user",
            "action": "user_login",
            "entity_type": "user",
            "entity_id": str(user["_id"]),
            "entity_name": user["username"],
            "description": f"User '{user['username']}' logged in",
            "metadata": {},
            "timestamp": datetime.now(timezone.utc)
        }
        log_collection.insert_one(log_entry)
    except:
        pass


# for user logout
def logout_log(request, user):
    try:
        log_entry = {
            "actor_id": str(user["_id"]),
            "actor_name":user['name'],
            "actor_type": "user",
            "action": "user_logout",
            "entity_type": "user",
            "entity_id": str(user["_id"]),
            "entity_name": user["username"],
            "description": f"User '{user['username']}' logged out",
            "metadata": {},
            "timestamp": datetime.now(timezone.utc)
        }
        log_collection.insert_one(log_entry)
    except:
        pass


# for user registration
def register_log(request, user):
    try:
        log_entry = {
            "actor_id": str(user["_id"]),
            "actor_name":user['name'],
            "actor_type": "user",
            "action": "user_register",
            "entity_type": "user",
            "entity_id": str(user["_id"]),
            "entity_name": user["username"],
            "description": f"User '{user['username']}' registered",
            "metadata": {},
            "timestamp": datetime.now(timezone.utc)
        }
        log_collection.insert_one(log_entry)
    except:
        pass


# for user deletion
def user_delete_log(request, user, deleted_by):
    try:
        log_entry = {
            "actor_id": str(deleted_by["_id"]),
            "actor_name":user['name'],
            "actor_type": deleted_by['role'],
            "action": "user_delete",
            "entity_type": "user",
            "entity_id": str(user["_id"]),
            "entity_name": user["username"],
            "description": f"User '{user['username']}' was deleted by admin",
            "metadata": {},
            "timestamp": datetime.now(timezone.utc)
        }
        log_collection.insert_one(log_entry)
    except:
        pass


# for user update
def user_update_log(request, user, updated_by, updated_fields):
    try:
        log_entry = {
            "actor_id": str(updated_by["_id"]),
            "actor_name":updated_by['name'],
            "actor_type": updated_by['role'],
            "action": "user_update",
            "entity_type": "user",
            "entity_id": str(user["_id"]),
            "entity_name": user["username"],
            "description": f"User '{user['username']}' was updated by admin",
            "metadata": {"updated_fields": updated_fields},
            "timestamp": datetime.now(timezone.utc)
        }
        log_collection.insert_one(log_entry)
    except:
        pass


# ========= product loggings ================= #


# product creation logging
def product_create_log(product_id, product_name,created_by):
    try:
        log_entry = {
            "actor_id": str(created_by["_id"]),
            "actor_name":created_by['name'],
            "actor_type": created_by['role'],
            "action": "product_create",
            "entity_type": "product",
            "entity_id": product_id,
            "entity_name": product_name,
            "description": f"Product '{product_name}' was created",
            "metadata": {},
            "timestamp": datetime.now(timezone.utc)
        }
        log_collection.insert_one(log_entry)
    except:
        pass


# product deletion logging
def product_deletion_log(product, deleted_by):
    try:
        log_entry = {
            "actor_id": str(deleted_by["_id"]),
            "actor_name":deleted_by['name'],
            "actor_type": deleted_by['role'],
            "action": "product_delete",
            "entity_type": "product",
            "entity_id": str(product["_id"]),
            "entity_name": product["name"],
            "description": f"Product '{product['name']}' was deleted",
            "metadata": {"product_details":product},
            "timestamp": datetime.now(timezone.utc)
        }
        log_collection.insert_one(log_entry)
    except:
        pass


# product update logging
def product_update_log(update_data,product,updated_by):
    
        
    try:
        log_entry = {
            "actor_id": str(updated_by["_id"]),
            "actor_name":update_data['name'],
            "actor_type": updated_by['role'],
            "action": "product_update",
            "entity_type": "product",
            "entity_id": str(product["_id"]),
            "entity_name": product["name"],
            "description": f"Product '{product['name']}' was updated",
            "metadata": {"updated_fields":update_data},
            "timestamp": datetime.now(timezone.utc)
        }
        log_collection.insert_one(log_entry)
    except Exception as e:
        pass
    
    

##====== product updatation ============#

# attributes creation logging
def attribute_creation_log(request, attribute, created_by):
    try:
        
        log_entry = {
            "actor_id": str(created_by["_id"]),
            "actor_name":created_by['name'],
            "actor_type": created_by['role'],
            "action": "attribute_create",
            "entity_type": "attribute",
            "entity_id": str(attribute["_id"]),
            "entity_name": attribute["name"],
            "description": f"attribute '{attribute['name']}' was created",
            "metadata": {},
            "timestamp": datetime.now(timezone.utc)
        }
        log_collection.insert_one(log_entry)
    except:
        pass


# attribute deletation logging
def attribute_delation_log(request, attribute, deleted_by):
    
        
    try:
        log_entry = {
            "actor_id": str(deleted_by["_id"]),
            "actor_name":deleted_by["name"],
            "actor_type": deleted_by['role'],
            "action": "attribute_delete",
            "entity_type": "attribute",
            "entity_id": str(attribute["_id"]),
            "entity_name": attribute["name"],
            "description": f"attribute '{attribute['name']}' was deleted",
            "metadata": {},
            "timestamp": datetime.now(timezone.utc)
        }
        log_collection.insert_one(log_entry)
    except:
        pass
    
# order updation logging
def order_updation_log(order, updated_by):
    
    try:
        log_entry = {
            "actor_id": str(updated_by["_id"]),
            "actor_name":updated_by['name'],
            "actor_type": updated_by['role'],
            "action": "Order Updation",
            "entity_type": "Order",
            "entity_id": str(order["_id"]),
            "entity_name":order['name'],
            "description": f"order was updated by {updated_by['username']}",
            "metadata": {
                "updated_by":updated_by['username']
                },
            "timestamp": datetime.now(timezone.utc)
        }
        log_collection.insert_one(log_entry)
    except:
        pass
    
    
#order deletion logging
def order_deletion_log(order,deleted_by):
    
    try:
        log_entry = {
            "actor_id": str(deleted_by["_id"]),
            "actor_name":deleted_by['name'],
            "actor_type": deleted_by['role'],
            "action": "Order deleted",
            "entity_type": "Order",
            "entity_id": str(order["_id"]),
            "actor_name":order['name'],
            "description": f"order was deleted by {deleted_by['username']}",
            "metadata": {
                "deleted_by":deleted_by['username']
                },
            "timestamp": datetime.now(timezone.utc)
        }
        log_collection.insert_one(log_entry)
    except:
        pass
        