from passlib.hash import pbkdf2_sha256
import uuid
from datetime import datetime,timedelta
import jwt
import uuid
from datetime import datetime, timedelta, timezone
from django.conf import settings

ACCESS_EXPIRE_MIN = 120
REFRESH_EXPIRE_DAYS = 7


#hashing password
def hash_password(password):

    return pbkdf2_sha256.hash(password)



#verify_password
def verify_password(password,hashed):

    return pbkdf2_sha256.verify(password,hashed)


#generate token
def generate_token():

    return str(uuid.uuid4)






#create jwt access token
def create_access_token(user_id, role):
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_EXPIRE_MIN),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


#create jwt refresh tokewn
def create_refresh_token(user_id):
    jti = str(uuid.uuid4())
    payload = {
        "sub": str(user_id),
        "jti": jti,
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_EXPIRE_DAYS),
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token, jti
