from django.shortcuts import render
import cloudinary.uploader
import json
from bson.objectid import ObjectId
from config.mongo import db
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from accounts.current_user import get_current_user
from config.permissions import is_user_admin, is_user_moderator
from datetime import datetime, timezone, timedelta
from django.http.multipartparser import MultiPartParser, MultiPartParserError
from django.http import QueryDict
from rest_framework.decorators import api_view
from rest_framework.response import Response

# Create your views here.

banner_col = db['banner']


@api_view(['POST'])
def add_banner(request):
    
    if request.method !='POST':
        return JsonResponse({"error":f"{request.method} method not allowed"})
    
    user,error = get_current_user(request)
    
    if error:
        return JsonResponse({"error":error})
    
    #checking user is admin or moderator
    if not (is_user_admin(user) or is_user_moderator(user)):
        return JsonResponse({'error': 'Unauthorized. Admin  or moderator access required.'}, status=403)
    
    
    title = request.POST.get("title")
    subtitle = request.POST.get("subtitle")
    banner_image = request.FILES.get('banner_image')
    created_by = str(user['_id'])
    created_at = datetime.now(timezone.utc)
    
    banner_data={}
    
    if not title:
        
        return JsonResponse({"error":"please add a title"})
    
    is_existing = banner_col.find_one({'title':title})
    if is_existing:
        return JsonResponse({"error":"banner with this title already exists"})
    
    banner_data['title'] = title
    
    if subtitle:
        banner_data['subtitle'] = subtitle
        
    if not banner_image:
        return JsonResponse({"error":"please upload an image"})
    

    try:
        banner_upload = cloudinary.uploader.upload(banner_image)
        if banner_upload and banner_upload.get('secure_url'):
            banner_data['img_url'] = banner_upload['secure_url']
        else:
            return JsonResponse({"error":"image uploading failed"})
    except Exception as e:
        return JsonResponse({"error":f"image upload failed reason {str(e)}"})
    
    if created_by:
        banner_data['created_by'] = created_by
    
    if created_at:
        banner_data['created_at'] = created_at
        
        
    try:
        result = banner_col.insert_one(banner_data)
        return JsonResponse({"message":"banner created successfully"})

    except Exception as e:
        return JsonResponse({"error":str(e)})
        


@api_view(['delete'])
def delete_banner(request,banner_id):
    
    if request.method !='DELETE':
        return JsonResponse({"error":f"{request.method} method not allowed"})
    
    user,error = get_current_user(request)
    
    if error:
        return JsonResponse({"error":error})
    
    #checking user is admin or moderator
    if not (is_user_admin(user) or is_user_moderator(user)):
        return JsonResponse({'error': 'Unauthorized. Admin  or moderator access required.'}, status=403)
    
    try:
        banner = banner_col.find({'_id':ObjectId(banner_id)})
        
        if not banner:
            
            return JsonResponse({"error":"could not found the banner"})

        
        
        banner_col.delete_one({"_id":ObjectId(banner_id)})
        return JsonResponse({"error":"banner deleted successfully"})
    except Exception as e:
        return JsonResponse({"error":str(e)})


def serialize_banner(banner):
    """Convert Mongo ObjectId to string"""
    banner['_id'] = str(banner['_id'])
    return banner

@api_view(['GET'])
def search_banner(request):

    # ---------- AUTH ----------
    user, error = get_current_user(request)
    if error:
        return Response({"error": error}, status=401)

    # if not (is_user_admin(user) or is_user_moderator(user)):
    #     return Response({"error": "Unauthorized. Admin or moderator access required."}, status=403)

    # ---------- QUERY ----------
    title = request.GET.get('title')
    subtitle = request.GET.get('subtitle')
    ban_id = request.GET.get('id')
    
    query = {}
    if ban_id:
        query['_id'] = ObjectId(ban_id)
    if title:
        query['title'] = title
    if subtitle:
        query['subtitle'] = subtitle

    try:
        banners_cursor = banner_col.find(query)
        banners_list = [serialize_banner(ban) for ban in banners_cursor]
        count = len(banners_list)

        return Response({
            "count": count,
            "banners": banners_list
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)
    
    

    
@api_view(['GET'])
def list_banners(request):
    try:
        banners_cursor = banner_col.find()
        banners_list = [serialize_banner(ban) for ban in banners_cursor]
        count = len(banners_list)

        return Response({
            "count": count,
            "banners": banners_list
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)


    
@api_view(['GET'])
def add_image_to(request,type,banner_id):
    
    if request.method !='GET':
        return JsonResponse({"error":f"{request.method} method not allowed"})
    
    user,error = get_current_user(request)
    
    if error:
        return JsonResponse({"error":error})
    
    #checking user is admin or moderator
    if not (is_user_admin(user) or is_user_moderator(user)):
        return JsonResponse({'error': 'Unauthorized. Admin  or moderator access required.'}, status=403)
    
    if not type or type not in ['hero_section','landing_page','banner']:
        return JsonResponse({"error":"please add a type from hero_section, landing_page, banner"})
    
    image = banner_col.find_one({'_id':ObjectId(banner_id)})
    
    if not image:
        return JsonResponse({"error":"could not find the banner"})
    
    return JsonResponse({"image_url":image.get('banner_url')})