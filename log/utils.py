from datetime import datetime, timezone
from config.mongo import db

log_collection = db["logs"]


# ================= USER LOGS ================= #

def login_log(request, user):
    try:
        full_name = f"{user['first_name']} {user['last_name']}"
        log_collection.insert_one({
            "actor_id": str(user["_id"]),
            "actor_type": "user",
            "action": "user_login",
            "entity_type": "user",
            "entity_id": str(user["_id"]),
            "entity_name": full_name,
            "description": f"User {full_name} logged in",
            "metadata": {},
            "timestamp": datetime.now(timezone.utc)
        })
    except:
        pass


def logout_log(request, user):
    try:
        full_name = f"{user['first_name']} {user['last_name']}"
        log_collection.insert_one({
            "actor_id": str(user["_id"]),
            "actor_name": full_name,
            "actor_type": "user",
            "action": "user_logout",
            "entity_type": "user",
            "entity_id": str(user["_id"]),
            "entity_name": full_name,
            "description": f"User '{full_name}' logged out",
            "metadata": {},
            "timestamp": datetime.now(timezone.utc)
        })
    except:
        pass


def register_log(request, user):
    try:
        full_name = f"{user['first_name']} {user['last_name']}"
        log_collection.insert_one({
            "actor_id": str(user["_id"]),
            "actor_name": full_name,
            "actor_type": "user",
            "action": "user_register",
            "entity_type": "user",
            "entity_id": str(user["_id"]),
            "entity_name": full_name,
            "description": f"User '{full_name}' registered",
            "metadata": {},
            "timestamp": datetime.now(timezone.utc)
        })
    except:
        pass


def user_delete_log(request, user, deleted_by):
    try:
        user_name = f"{user['first_name']} {user['last_name']}"
        admin_name = f"{deleted_by['first_name']} {deleted_by['last_name']}"

        log_collection.insert_one({
            "actor_id": str(deleted_by["_id"]),
            "actor_name": admin_name,
            "actor_type": deleted_by['role'],
            "action": "user_delete",
            "entity_type": "user",
            "entity_id": str(user["_id"]),
            "entity_name": user_name,
            "description": f"User '{user_name}' was deleted by {admin_name}",
            "metadata": {},
            "timestamp": datetime.now(timezone.utc)
        })
    except:
        pass


def user_update_log(request, user, updated_by, updated_fields):
    try:
        user_name = f"{user['first_name']} {user['last_name']}"
        admin_name = f"{updated_by['first_name']} {updated_by['last_name']}"

        log_collection.insert_one({
            "actor_id": str(updated_by["_id"]),
            "actor_name": admin_name,
            "actor_type": updated_by['role'],
            "action": "user_update",
            "entity_type": "user",
            "entity_id": str(user["_id"]),
            "entity_name": user_name,
            "description": f"User '{user_name}' was updated by {admin_name}",
            "metadata": {"updated_fields": updated_fields},
            "timestamp": datetime.now(timezone.utc)
        })
    except:
        pass


# ================= PRODUCT LOGS ================= #

def product_create_log(product_id, product_name, created_by):
    try:
        admin_name = f"{created_by['first_name']} {created_by['last_name']}"

        log_collection.insert_one({
            "actor_id": str(created_by["_id"]),
            "actor_name": admin_name,
            "actor_type": created_by['role'],
            "action": "product_create",
            "entity_type": "product",
            "entity_id": product_id,
            "entity_name": product_name,
            "description": f"Product '{product_name}' was created by {admin_name}",
            "metadata": {},
            "timestamp": datetime.now(timezone.utc)
        })
    except:
        pass


def product_deletion_log(product, deleted_by):
    try:
        admin_name = f"{deleted_by['first_name']} {deleted_by['last_name']}"

        log_collection.insert_one({
            "actor_id": str(deleted_by["_id"]),
            "actor_name": admin_name,
            "actor_type": deleted_by['role'],
            "action": "product_delete",
            "entity_type": "product",
            "entity_id": str(product["_id"]),
            "entity_name": product["name"],
            "description": f"Product '{product['name']}' was deleted by {admin_name}",
            "metadata": {},
            "timestamp": datetime.now(timezone.utc)
        })
    except:
        pass


def product_update_log(update_data, product, updated_by):
    try:
        admin_name = f"{updated_by['first_name']} {updated_by['last_name']}"

        log_collection.insert_one({
            "actor_id": str(updated_by["_id"]),
            "actor_name": admin_name,
            "actor_type": updated_by['role'],
            "action": "product_update",
            "entity_type": "product",
            "entity_id": str(product["_id"]),
            "entity_name": product["name"],
            "description": f"Product '{product['name']}' was updated by {admin_name}",
            "metadata": {"updated_fields": update_data},
            "timestamp": datetime.now(timezone.utc)
        })
    except:
        pass


# ================= ATTRIBUTE LOGS ================= #

def attribute_creation_log(request, attribute, created_by):
    try:
        admin_name = f"{created_by['first_name']} {created_by['last_name']}"

        log_collection.insert_one({
            "actor_id": str(created_by["_id"]),
            "actor_name": admin_name,
            "actor_type": created_by['role'],
            "action": "attribute_create",
            "entity_type": "attribute",
            "entity_id": str(attribute["_id"]),
            "entity_name": attribute["name"],
            "description": f"Attribute '{attribute['name']}' was created by {admin_name}",
            "metadata": {},
            "timestamp": datetime.now(timezone.utc)
        })
    except:
        pass


def attribute_delation_log(request, attribute, deleted_by):
    try:
        admin_name = f"{deleted_by['first_name']} {deleted_by['last_name']}"

        log_collection.insert_one({
            "actor_id": str(deleted_by["_id"]),
            "actor_name": admin_name,
            "actor_type": deleted_by['role'],
            "action": "attribute_delete",
            "entity_type": "attribute",
            "entity_id": str(attribute["_id"]),
            "entity_name": attribute["name"],
            "description": f"Attribute '{attribute['name']}' was deleted by {admin_name}",
            "metadata": {},
            "timestamp": datetime.now(timezone.utc)
        })
    except:
        pass


# ================= ORDER LOGS ================= #

def order_updation_log(order, updated_by):
    try:
        admin_name = f"{updated_by['first_name']} {updated_by['last_name']}"

        log_collection.insert_one({
            "actor_id": str(updated_by["_id"]),
            "actor_name": admin_name,
            "actor_type": updated_by['role'],
            "action": "order_update",
            "entity_type": "order",
            "entity_id": str(order["_id"]),
            "entity_name": order.get("name", "Order"),
            "description": f"Order was updated by {admin_name}",
            "metadata": {},
            "timestamp": datetime.now(timezone.utc)
        })
    except:
        pass


def order_deletion_log(order, deleted_by):
    try:
        admin_name = f"{deleted_by['first_name']} {deleted_by['last_name']}"

        log_collection.insert_one({
            "actor_id": str(deleted_by["_id"]),
            "actor_name": admin_name,
            "actor_type": deleted_by['role'],
            "action": "order_delete",
            "entity_type": "order",
            "entity_id": str(order["_id"]),
            "entity_name": order.get("name", "Order"),
            "description": f"Order was deleted by {admin_name}",
            "metadata": {},
            "timestamp": datetime.now(timezone.utc)
        })
    except:
        pass
