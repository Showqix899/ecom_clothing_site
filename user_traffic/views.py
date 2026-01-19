from django.shortcuts import render
from user_traffic.middleware.visit_logger import visits_col
from rest_framework.decorators import api_view
from django.http import JsonResponse
from config.permissions import is_user_admin, is_user_moderator
from datetime import datetime, timedelta, timezone
from accounts.current_user import get_current_user


# ---------------- WEEKLY USERS ----------------
def weekly_users():
    start_date = datetime.now(timezone.utc) - timedelta(days=7)

    return visits_col.aggregate([
        {"$match": {"visited_at": {"$gte": start_date}}},
        {"$group": {
            "_id": {
                "$cond": [
                    {"$ne": ["$user_id", None]},
                    "$user_id",
                    {"$concat": ["$ip", "$user_agent"]}
                ]
            }
        }},
        {"$count": "users"}
    ])


# ---------------- MONTHLY USERS ----------------
def monthly_users():
    start_date = datetime.now(timezone.utc) - timedelta(days=30)

    return visits_col.aggregate([
        {"$match": {"visited_at": {"$gte": start_date}}},
        {"$group": {
            "_id": {
                "$cond": [
                    {"$ne": ["$user_id", None]},
                    "$user_id",
                    {"$concat": ["$ip", "$user_agent"]}
                ]
            }
        }},
        {"$count": "users"}
    ])


# ---------------- YEARLY USERS ----------------
def yearly_users():
    start_date = datetime.now(timezone.utc) - timedelta(days=365)

    return visits_col.aggregate([
        {"$match": {"visited_at": {"$gte": start_date}}},
        {"$group": {
            "_id": {
                "$cond": [
                    {"$ne": ["$user_id", None]},
                    "$user_id",
                    {"$concat": ["$ip", "$user_agent"]}
                ]
            }
        }},
        {"$count": "users"}
    ])


# ---------------- SITE ANALYTICS ----------------
@api_view(['GET'])
def site_analytics(request):
    user, error = get_current_user(request)

    if error:
        return JsonResponse({"error": "Authentication required"}, status=401)

    

    if not is_user_admin(user):
        return JsonResponse({"error": "Permission denied"}, status=403)

    weekly = list(weekly_users())
    monthly = list(monthly_users())
    yearly = list(yearly_users())

    return JsonResponse({
        "weekly_users": weekly[0]["users"] if weekly else 0,
        "monthly_users": monthly[0]["users"] if yearly else 0,
        "yearly_users": yearly[0]["users"] if yearly else 0,
    })



# ----------------  helper function for get uique users as time being ----------------
def get_unique_users(start_date, end_date):
    result = list(visits_col.aggregate([
        {
            "$match": {
                "visited_at": {
                    "$gte": start_date,
                    "$lt": end_date
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "$cond": [
                        {"$ne": ["$user_id", None]},
                        "$user_id",
                        {"$concat": ["$ip", "$user_agent"]}
                    ]
                }
            }
        },
        {"$count": "users"}
    ]))

    return result[0]["users"] if result else 0


# ---------------- FILTERED SITE TRAFFIC ----------------
@api_view(['GET'])
def filtered_site_traffic(request):
    user, error = get_current_user(request)

    if error:
        return JsonResponse({"error": "Authentication required"}, status=401)


    if not is_user_admin(user):
        return JsonResponse({"error": "Permission denied"}, status=403)

    week = request.GET.get("week")
    month = request.GET.get("month")
    year = request.GET.get("year")

    try:
        if week:
            start_date = datetime.fromisoformat(week).replace(tzinfo=timezone.utc)
            end_date = start_date + timedelta(days=7)
            label = "weekly"

        elif month:
            start_date = datetime.strptime(month, "%Y-%m").replace(tzinfo=timezone.utc)
            if start_date.month == 12:
                end_date = start_date.replace(year=start_date.year + 1, month=1)
            else:
                end_date = start_date.replace(month=start_date.month + 1)
            label = "monthly"

        elif year:
            start_date = datetime(int(year), 1, 1, tzinfo=timezone.utc)
            end_date = datetime(int(year) + 1, 1, 1, tzinfo=timezone.utc)
            label = "yearly"

        else:
            return JsonResponse(
                {"error": "Provide week, month, or year parameter"},
                status=400
            )

    except ValueError:
        return JsonResponse({"error": "Invalid date format"}, status=400)

    users = get_unique_users(start_date, end_date)

    return JsonResponse({
        "type": label,
        "start_date": start_date,
        "end_date": end_date,
        "users": users
    })

