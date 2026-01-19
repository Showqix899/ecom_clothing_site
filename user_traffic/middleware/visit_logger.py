from config.mongo import db
# Collection for logging site visits
visits_col = db['site_visits']


from datetime import datetime
from django.utils.deprecation import MiddlewareMixin

class VisitLoggerMiddleware(MiddlewareMixin):

    def process_request(self, request):
        # Avoid logging static files & admin
        if request.path.startswith('/static') or request.path.startswith('/admin'):
            return

        ip = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        user_id = None
        if request.user.is_authenticated:
            user_id = str(request.user.id)

        visits_col.insert_one({
            "user_id": user_id,
            "ip": ip,
            "user_agent": user_agent,
            "visited_at": datetime.utcnow()
        })

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
