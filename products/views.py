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
from django.http import QueryDict
from django.http.multipartparser import MultiPartParser, MultiPartParserError

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
    
    
    
#get all the colors , size and categories
@csrf_exempt
def get_attributes(request):
    
    if request.method == 'GET':
        colors = list(colors_col.find({}, {'_id': 1, 'name': 1}))
        sizes = list(sizes_col.find({}, {'_id': 1, 'name': 1}))
        categories = list(categories_col.find({}, {'_id': 1, 'name': 1}))

        # Convert ObjectId to string for JSON serialization
        for color in colors:
            color['_id'] = str(color['_id'])
        for size in sizes:
            size['_id'] = str(size['_id'])
        for category in categories:
            category['_id'] = str(category['_id'])

        return JsonResponse({
            'colors': colors,
            'sizes': sizes,
            'categories': categories
        }, status=200)
    
    
# ---------------- Product Views -------------------- #
#product create views for admin
@csrf_exempt
def create_product(request):

    try:
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

            if not images or len(images) > 3:
                return JsonResponse({'error': 'Please upload between 1 to 3 images.'}, status=400)

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
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)





#get product details
@csrf_exempt
def get_product_details(request, product_id):
    
    try:
        if request.method == 'GET':
            product = products_col.find_one({'_id': ObjectId(product_id)})
        if not product:
            return JsonResponse({'error': 'Product not found'}, status=404)

        # Convert ObjectId fields to string for JSON serialization
        product['_id'] = str(product['_id'])
        product['category_id'] = str(product['category_id']) if product.get('category_id') else None
        product['color_ids'] = [str(cid) for cid in product.get('color_ids', [])]
        product['size_ids'] = [str(sid) for sid in product.get('size_ids', [])]
        product['created_at'] = product['created_at'].isoformat() if product.get('created_at') else None
        product['updated_at'] = product['updated_at'].isoformat() if product.get('updated_at') else None

        return JsonResponse({'product': product}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)




#product update view for admin
@csrf_exempt
def update_product(request, product_id):
    product = None
    try:
        user, error = get_current_user(request)
        if error:
            return JsonResponse({'error': error}, status=401)

        if not (is_user_admin(user) or is_user_moderator(user)):
            return JsonResponse(
                {'error': 'Unauthorized. Admin or moderator access required.'},
                status=403
            )

        # ---------- UPDATE PRODUCT ----------
        # if request.method == 'PUT' or (request.method == 'POST' and request.POST.get('_method') == 'PUT'):
        if request.method == 'PUT':
            data = QueryDict(request.body, encoding='utf-8')

            product = products_col.find_one({'_id': ObjectId(product_id)})
            if not product:
                return JsonResponse({'error': 'Product not found'}, status=404)

            update_data = {}

            # -------- BASIC FIELDS --------
            if data.get('name'):
                update_data['name'] = data.get('name')

            if data.get('description'):
                update_data['description'] = data.get('description')

            if data.get('price'):
                update_data['price'] = float(data.get('price'))

            if data.get('stock'):
                update_data['stock'] = int(data.get('stock'))

            if data.get('category_id'):
                update_data['category_id'] = ObjectId(data.get('category_id'))

            # -------- COLORS --------
            existing_colors = product.get('color_ids', [])

            add_colors = data.getlist('add_color_ids')
            remove_colors = data.getlist('remove_color_ids')

            if remove_colors:
                existing_colors = [
                    cid for cid in existing_colors if str(cid) not in remove_colors
                ]

            if add_colors:
                for cid in add_colors:
                    obj_id = ObjectId(cid)
                    if obj_id not in existing_colors:
                        existing_colors.append(obj_id)

            update_data['color_ids'] = existing_colors

            # -------- SIZES --------
            existing_sizes = product.get('size_ids', [])

            add_sizes = data.getlist('add_size_ids')
            remove_sizes = data.getlist('remove_size_ids')

            if remove_sizes:
                existing_sizes = [
                    sid for sid in existing_sizes if str(sid) not in remove_sizes
                ]

            if add_sizes:
                for sid in add_sizes:
                    obj_id = ObjectId(sid)
                    if obj_id not in existing_sizes:
                        existing_sizes.append(obj_id)

            update_data['size_ids'] = existing_sizes

            # -------- IMAGES --------
            update_data['image_urls'] = product.get('image_urls', [])

            update_data['updated_at'] = datetime.now(timezone.utc)
            
            for field, value in update_data.items():
                print(f'Updating field: {field} to value: {value}')

            products_col.update_one(
                {'_id': ObjectId(product_id)},
                {'$set': update_data}
            )

            return JsonResponse({'message': 'Product updated successfully'}, status=200)

        # ---------- GET PRODUCT ----------
        elif request.method == 'GET':
            product = products_col.find_one({'_id': ObjectId(product_id)})
            if not product:
                return JsonResponse({'error': 'Product not found'}, status=404)

            product['_id'] = str(product['_id'])
            product['category_id'] = str(product.get('category_id'))
            product['color_ids'] = [str(cid) for cid in product.get('color_ids', [])]
            product['size_ids'] = [str(sid) for sid in product.get('size_ids', [])]
            product['created_at'] = product['created_at'].isoformat()
            product['updated_at'] = product.get('updated_at')

            return JsonResponse({'product': product}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



#delete product
@csrf_exempt
def delete_product(request, product_id):
    try:
        user, error = get_current_user(request)
        if error:
            return JsonResponse({'error': error}, status=401)

        if not (is_user_admin(user) or is_user_moderator(user)):
            return JsonResponse(
                {'error': 'Unauthorized. Admin or moderator access required.'},
                status=403
            )

        if request.method == 'DELETE':
            result = products_col.delete_one({'_id': ObjectId(product_id)})
            if result.deleted_count == 0:
                return JsonResponse({'error': 'Product not found'}, status=404)

            return JsonResponse({'message': 'Product deleted successfully'}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
    
#get all the prducts
@csrf_exempt
def get_all_products(request):
    try:
        if request.method == 'GET':
            products = list(products_col.find({}))

            for product in products:
                product['_id'] = str(product['_id'])
                product['category_id'] = str(product.get('category_id'))
                product['color_ids'] = [str(cid) for cid in product.get('color_ids', [])]
                product['size_ids'] = [str(sid) for sid in product.get('size_ids', [])]
                product['created_at'] = product['created_at'].isoformat()
                product['updated_at'] = product.get('updated_at')

            return JsonResponse({'products': products}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
    
    

#update product images add or remove

@csrf_exempt
def update_product_images(request, product_id):
    try:
        # -------- METHOD CHECK --------
        if request.method not in ['PUT', 'PATCH']:
            return JsonResponse({'error': 'Method not allowed'}, status=405)

        # -------- MULTIPART PARSE (CRITICAL FIX) --------
        try:
            parser = MultiPartParser(
                request.META,
                request,
                request.upload_handlers
            )
            data, files = parser.parse()
        except MultiPartParserError:
            return JsonResponse(
                {'error': 'Invalid multipart/form-data'},
                status=400
            )

        # -------- PRODUCT --------
        product = products_col.find_one({'_id': ObjectId(product_id)})
        if not product:
            return JsonResponse({'error': 'Product not found'}, status=404)

        existing_images = product.get('image_urls', [])

        
        # -------- REMOVE IMAGES --------
        remove_images_str = data.get('remove_images', '[]')  # text field from form-data
        try:
            remove_images = json.loads(remove_images_str)  # try JSON list
            if not isinstance(remove_images, list):
                raise ValueError
        except Exception:
            # fallback: comma-separated string
            remove_images = [s.strip() for s in remove_images_str.split(',') if s.strip()]

        existing_images = [url for url in existing_images if url not in remove_images]


        # -------- ADD IMAGES --------
        add_images = files.getlist('add_images')

        if len(add_images) > 3:
            return JsonResponse(
                {'error': 'You can upload maximum 3 images'},
                status=400
            )

        for image in add_images:
            upload = cloudinary.uploader.upload(image)
            existing_images.append(upload['secure_url'])

        # -------- REMOVE DUPLICATES --------
        existing_images = list(dict.fromkeys(existing_images))

        # -------- VALIDATION --------
        if not (1 <= len(existing_images) <= 3):
            return JsonResponse(
                {'error': 'Product must have between 1 and 3 images'},
                status=400
            )

        # -------- UPDATE DB --------
        products_col.update_one(
            {'_id': ObjectId(product_id)},
            {
                '$set': {
                    'image_urls': existing_images,
                    'updated_at': datetime.now(timezone.utc)
                }
            }
        )

        return JsonResponse(
            {
                'message': 'Product images updated successfully',
                'image_urls': existing_images
            },
            status=200
        )

    except Exception as e:
        return JsonResponse(
            {'error': 'Internal server error', 'details': str(e)},
            status=500
        )
        
        
        
