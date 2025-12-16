
from datetime import datetime, timezone
from config.mongo import db

carts_col = db['carts']

def get_user_cart(user_id):
    cart = carts_col.find_one({'user_id': user_id})
    if not cart:
        cart = {
            'user_id': user_id,
            'items': [],
            'updated_at': datetime.now(timezone.utc)
        }
        carts_col.insert_one(cart)
        cart = carts_col.find_one({'user_id': user_id})
    return cart
