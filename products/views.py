from django.shortcuts import render

# Create your views here.
import json
from bson.objectid import ObjectId
from config.mongo import db
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from accounts.current_user import get_current_user
from django.views.decorators.csrf import csrf_exempt
from config.permissions import is_user_admin, is_user_moderator
from datetime import datetime, timezone, timedelta
import cloudinary.uploader

products_col = db["products"] #product collection
colors_col = db["colors"] #colors collection
sizes_col = db["sizes"] #sizes collection
categories_col = db["categories"] #categories collection


#add color
@csrf_exempt
def add_color(request):
    
    #getting current user
    user,error = get_current_user(request)
    if error:
        return JsonResponse({'error': error}, status=401)
    
    
    #checking user is admin or moderator
    if not is_user_admin(user) or is_user_moderator(user):
        return JsonResponse({'error': 'Unauthorized. Admin  or moderator access required.'}, status=403)
    
    
    #adding color
    if request.method == 'POST':
        body = json.loads(request.body)
        color_name = body.get('color_name')
        if not color_name:
            return JsonResponse({'error': 'Color name is required.'}, status=400)
        
        # Check if color already exists
        existing_color = colors_col.find_one({'name': color_name})
        if existing_color:
            return JsonResponse({'error': 'Color already exists.'}, status=400)
        
        # Insert new color
        color_data = {'name': color_name.lower()}
        result = colors_col.insert_one(color_data)
        
        return JsonResponse({'message': 'Color added successfully.', 'color_id': str(result.inserted_id)}, status=201)
    
    
    

#delete color
@csrf_exempt
def delete_color(request, color_id):
    
    #getting current user
    user,error = get_current_user(request)
    if error:
        return JsonResponse({'error': error}, status=401)
    
    
    #checking user is admin or moderator
    if not is_user_admin(user) or is_user_moderator(user):
        return JsonResponse({'error': 'Unauthorized. Admin  or moderator access required.'}, status=403)
    
    
    if request.method == 'DELETE':
        result = colors_col.delete_one({'_id': ObjectId(color_id)})
        if result.deleted_count == 0:
            return JsonResponse({'error': 'Color not found.'}, status=404)
        return JsonResponse({'message': 'Color deleted successfully.'}, status=200)
    
    



#add size
@csrf_exempt
def add_size(request):
    
    #getting current user
    user,error = get_current_user(request)
    if error:
        return JsonResponse({'error': error}, status=401)
    
    
    #checking user is admin or moderator
    if not is_user_admin(user) or is_user_moderator(user):
        return JsonResponse({'error': 'Unauthorized. Admin  or moderator access required.'}, status=403)
    
    
    if request.method == 'POST':
        body = json.loads(request.body)
        size_name = body.get('size_name')
        if not size_name:
            return JsonResponse({'error': 'Size name is required.'}, status=400)
        
        # Check if size already exists
        existing_size = sizes_col.find_one({'name': size_name})
        if existing_size:
            return JsonResponse({'error': 'Size already exists.'}, status=400)
        
        # Insert new size
        size_data = {'name': size_name.lower()}
        result = sizes_col.insert_one(size_data)
        
        return JsonResponse({'message': 'Size added successfully.', 'size_id': str(result.inserted_id)}, status=201)
#delete size
@csrf_exempt
def delete_size(request, size_id):
    
    #getting current user
    user,error = get_current_user(request)
    if error:
        return JsonResponse({'error': error}, status=401)
    
    
    #checking user is admin or moderator
    if not is_user_admin(user) or is_user_moderator(user):
        return JsonResponse({'error': 'Unauthorized. Admin  or moderator access required.'}, status=403)
    
    
    if request.method == 'DELETE':
        result = sizes_col.delete_one({'_id': ObjectId(size_id)})
        if result.deleted_count == 0:
            return JsonResponse({'error': 'Size not found.'}, status=404)
        return JsonResponse({'message': 'Size deleted successfully.'}, status=200)
    
    
    
#add category
@csrf_exempt
def add_category(request):
    #getting current user
    user,error = get_current_user(request)
    if error:
        return JsonResponse({'error': error}, status=401)
    
    
    #checking user is admin or moderator
    if not is_user_admin(user) or is_user_moderator(user):
        return JsonResponse({'error': 'Unauthorized. Admin  or moderator access required.'}, status=403)
    
    
    if request.method == 'POST':
        body = json.loads(request.body)
        category_name = body.get('category_name')
        if not category_name:
            return JsonResponse({'error': 'Category name is required.'}, status=400)
        
        # Check if category already exists
        existing_category = categories_col.find_one({'name': category_name})
        if existing_category:
            return JsonResponse({'error': 'Category already exists.'}, status=400)
        
        # Insert new category
        category_data = {'name': category_name.lower()}
        result = categories_col.insert_one(category_data)
        
        return JsonResponse({'message': 'Category added successfully.', 'category_id': str(result.inserted_id)}, status=201)


#delete category
@csrf_exempt
def delete_category(request, category_id):
    #getting current user
    user,error = get_current_user(request)
    if error:
        return JsonResponse({'error': error}, status=401)
    
    
    #checking user is admin or moderator
    if not is_user_admin(user) or is_user_moderator(user):
        return JsonResponse({'error': 'Unauthorized. Admin  or moderator access required.'}, status=403)
    
    
    if request.method == 'DELETE':
        result = categories_col.delete_one({'_id': ObjectId(category_id)})
        if result.deleted_count == 0:
            return JsonResponse({'error': 'Category not found.'}, status=404)
        return JsonResponse({'message': 'Category deleted successfully.'}, status=200)
    
    
# ---------------- Product Views -------------------- #
#product create views for admin
@csrf_exempt
def create_product(request):

    user, error = get_current_user(request)
    if error:
        return JsonResponse({'error': error}, status=401)

    if not (is_user_admin(user) or is_user_moderator(user)):
        return JsonResponse(
            {'error': 'Unauthorized. Admin or moderator access required.'},
            status=403
        )

    if request.method == 'POST':

        name = request.POST.get('name')
        description = request.POST.get('description')
        price = float(request.POST.get('price', 0))
        category_id = request.POST.get('category_id')
        stock = int(request.POST.get('stock', 0))

        color_ids = request.POST.getlist('color_ids')
        size_ids = request.POST.getlist('size_ids')
        images = request.FILES.getlist('images')

        if not images:
            return JsonResponse({'error': 'At least one image is required'}, status=400)

        if not color_ids or not size_ids:
            return JsonResponse({'error': 'Color and size are required'}, status=400)

        image_urls = []
        for image in images:
            upload = cloudinary.uploader.upload(image)
            image_urls.append(upload['secure_url'])

        product_data = {
            'name': name,
            'description': description,
            'price': price,
            'category_id': ObjectId(category_id) if category_id else None,
            'color_ids': [ObjectId(cid) for cid in color_ids],
            'size_ids': [ObjectId(sid) for sid in size_ids],
            'image_urls': image_urls,
            'stock': stock,
            'sold_count': 0,
            'created_by': user['username'],
            'created_at': datetime.now(timezone.utc),
            'updated_at': None
        }

        result = products_col.insert_one(product_data)

        return JsonResponse({
            'message': 'Product created successfully',
            'product_id': str(result.inserted_id)
        }, status=201)
