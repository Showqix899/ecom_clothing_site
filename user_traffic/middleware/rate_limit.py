import time
from django.http import JsonResponse
from threading import Lock

# ---------------- CONFIG ----------------
RATE_LIMIT = 100          # requests
WINDOW_SIZE = 60          # seconds

# ---------------- STORAGE ----------------
# {
#   "key": {
#       "tokens": int,
#       "last_refill": timestamp
#   }
# }
rate_limit_store = {}
lock = Lock()


#client key
def get_client_key(request):
    """
    Identify client:
    - Logged-in user → user_id
    - Anonymous → IP
    """
    user = getattr(request, "user", None)

    if user and getattr(user, "is_authenticated", False):
        return f"user:{user.id}"

    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return f"ip:{xff.split(',')[0]}"

    return f"ip:{request.META.get('REMOTE_ADDR')}"


def allow_request(key):
    now = time.time()

    with lock:
        bucket = rate_limit_store.get(key)

        if not bucket:
            rate_limit_store[key] = {
                "tokens": RATE_LIMIT - 1,
                "last_refill": now
            }
            return True

        elapsed = now - bucket["last_refill"]

        # refill tokens
        refill = int(elapsed * (RATE_LIMIT / WINDOW_SIZE))
        if refill > 0:
            bucket["tokens"] = min(RATE_LIMIT, bucket["tokens"] + refill)
            bucket["last_refill"] = now

        if bucket["tokens"] <= 0:
            return False

        bucket["tokens"] -= 1
        return True


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip admin & static
        if request.path.startswith("/admin") or request.path.startswith("/static"):
            return self.get_response(request)

        key = get_client_key(request)

        if not allow_request(key):
            return JsonResponse(
                {"error": "Too many requests. Please slow down."},
                status=429
            )

        return self.get_response(request)
