import jwt
from django.conf import settings
from bson.objectid import ObjectId
from config.mongo import db

collection = db['user']

def get_current_user(request):
    auth_header = request.META.get("HTTP_AUTHORIZATION")
    if not auth_header:
        return None, "Authorization header missing"
    
    try:
        token_type, token = auth_header.split()
        if token_type.lower() != "bearer":
            return None, "Invalid token type"

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

        if payload.get("type") != "access":
            return None, "Not an access token"

        sub = payload.get("sub")
        if not sub:
            return None, "Invalid token: sub missing"

        try:
            user_id = ObjectId(sub)
        except Exception as e:
            return None, f"Invalid user id in token: {str(e)}"

        user = collection.find_one({"_id": user_id})
        if not user:
            return None, "User not found"

        # Make JSON-serializable
        user_safe = dict(user)
        user_safe["_id"] = str(user_safe["_id"])  # Convert ObjectId to string
        user_safe.pop("password", None)
        user_safe.pop("refresh_tokens", None)

        return user_safe, None

    except jwt.ExpiredSignatureError:
        return None, "Access token expired"
    except jwt.InvalidTokenError:
        return None, "Invalid token"
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"
