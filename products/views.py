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
from log.utils import (attribute_creation_log,attribute_delation_log
                       ,product_create_log,product_deletion_log,
                       product_update_log)
import cloudinary.uploader
from rest_framework.decorators import api_view
import csv
from django.http import HttpResponse

products_col = db["products"] #product collection
colors_col = db["colors"] #colors collection
sizes_col = db["sizes"] #sizes collection
categories_col = db["categories"] #categories collection


#add color
@api_view(['POST'])
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
        
        #adding log
        color = colors_col.find_one({'_id':ObjectId(result.inserted_id)})
        attribute_creation_log(request,color,user)
        
        return JsonResponse({'message': 'Color added successfully.', 'color_id': str(result.inserted_id)}, status=201)
    
    
    

#delete color
@api_view(['DELETE'])
def delete_color(request, color_id):
    
    #getting current user
    user,error = get_current_user(request)
    if error:
        return JsonResponse({'error': error}, status=401)
    
    
    #checking user is admin or moderator
    if not is_user_admin(user) or is_user_moderator(user):
        return JsonResponse({'error': 'Unauthorized. Admin  or moderator access required.'}, status=403)
    
    
    if request.method == 'DELETE':
        color = colors_col.find_one({"_id":ObjectId(color_id)})
        result = colors_col.delete_one({'_id': ObjectId(color_id)})
        if result.deleted_count == 0:
            return JsonResponse({'error': 'Color not found.'}, status=404)
        
        #attribute deletion log
        attribute_delation_log(request,color,user)
        return JsonResponse({'message': 'Color deleted successfully.'}, status=200)
    
    



#add size
@api_view(['POST'])
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
        
        #attribute logging 
        size = sizes_col.find_one({"_id":ObjectId(result.inserted_id)})
        attribute_creation_log(request,size,user)
        
        
        
        return JsonResponse({'message': 'Size added successfully.', 'size_id': str(result.inserted_id)}, status=201)
    
    
    
    
    
#delete size
@api_view(['DELETE'])
def delete_size(request, size_id):
    
    #getting current user
    user,error = get_current_user(request)
    if error:
        return JsonResponse({'error': error}, status=401)
    
    
    #checking user is admin or moderator
    if not is_user_admin(user) or is_user_moderator(user):
        return JsonResponse({'error': 'Unauthorized. Admin  or moderator access required.'}, status=403)
    
    
    if request.method == 'DELETE':
        size = sizes_col.find_one({"_id":ObjectId(size_id)})
        result = sizes_col.delete_one({'_id': ObjectId(size_id)})
        if result.deleted_count == 0:
            return JsonResponse({'error': 'Size not found.'}, status=404)

        #logging size
        attribute_delation_log(request,size,user)
        return JsonResponse({'message': 'Size deleted successfully.'}, status=200)
    
    
    
#add category
@api_view(['POST'])
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
        
        #logging
        category = categories_col.find_one({'_id':ObjectId(result.inserted_id)})
        attribute_creation_log(request,category,user)
        
        
        
        return JsonResponse({'message': 'Category added successfully.', 'category_id': str(result.inserted_id)}, status=201)


#delete category
@api_view(['DELETE'])
def delete_category(request, category_id):
    #getting current user
    user,error = get_current_user(request)
    if error:
        return JsonResponse({'error': error}, status=401)
    
    
    #checking user is admin or moderator
    if not is_user_admin(user) or is_user_moderator(user):
        return JsonResponse({'error': 'Unauthorized. Admin  or moderator access required.'}, status=403)
    
    
    if request.method == 'DELETE':
        category = categories_col.find_one({'_id':ObjectId(category_id)})
        result = categories_col.delete_one({'_id': ObjectId(category_id)})
        if result.deleted_count == 0:
            return JsonResponse({'error': 'Category not found.'}, status=404)
        
        attribute_delation_log(request,category,user)
        return JsonResponse({'message': 'Category deleted successfully.'}, status=200)
    
    
    
#get all the colors , size and categories
@api_view(['GET'])
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
@api_view(['POST'])
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
            
            product_name = product_data['name']
            product_id = str(result.inserted_id)
            
            product_create_log(product_id,product_name,user)

            return JsonResponse({
                'message': 'Product created successfully',
                'product_id': str(result.inserted_id)
            }, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)





#get product details
@api_view(['GET'])
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
@api_view(['GET', 'PUT'])
def update_product(request, product_id):
    try:
        user, error = get_current_user(request)
        if error:
            return JsonResponse({'error': error}, status=401)

        if not (is_user_admin(user) or is_user_moderator(user)):
            return JsonResponse(
                {'error': 'Unauthorized. Admin or moderator access required.'},
                status=403
            )

        product = products_col.find_one({'_id': ObjectId(product_id)})
        if not product:
            return JsonResponse({'error': 'Product not found'}, status=404)

        # ---------- UPDATE PRODUCT ----------
        if request.method == 'PUT':
            # ---------- PARSE BODY ----------
            try:
                if request.content_type == 'application/json':
                    data = json.loads(request.body)
                else:
                    data = QueryDict(request.body, encoding='utf-8')
            except:
                return JsonResponse({'error': 'Invalid request body'}, status=400)

            update_data = {}
            changed_fields = []

            # ---------- HELPER FUNCTIONS ----------
            def get_value(key):
                if hasattr(data, 'getlist'):
                    return data.get(key)
                return data.get(key)

            def get_list(key):
                if hasattr(data, 'getlist'):
                    return data.getlist(key)
                return data.get(key, [])

            # -------- BASIC FIELDS --------
            for field in ['name', 'description', 'price', 'stock', 'category_id', 'image_urls']:
                value = get_value(field)
                if value is not None:
                    if field == 'price':
                        value = float(value)
                    elif field == 'stock':
                        value = int(value)
                    elif field == 'category_id':
                        value = ObjectId(value)
                    update_data[field] = value
                    changed_fields.append(field)

            # -------- COLORS --------
            if 'add_color_ids' in data or 'remove_color_ids' in data:
                colors = product.get('color_ids', [])
                remove_colors = get_list('remove_color_ids')
                add_colors = get_list('add_color_ids')

                colors = [c for c in colors if str(c) not in remove_colors]
                for c in add_colors:
                    obj_id = ObjectId(c)
                    if obj_id not in colors:
                        colors.append(obj_id)
                update_data['color_ids'] = colors
                if add_colors or remove_colors:
                    changed_fields.append('color_ids')

            # -------- SIZES --------
            if 'add_size_ids' in data or 'remove_size_ids' in data:
                sizes = product.get('size_ids', [])
                remove_sizes = get_list('remove_size_ids')
                add_sizes = get_list('add_size_ids')

                sizes = [s for s in sizes if str(s) not in remove_sizes]
                for s in add_sizes:
                    obj_id = ObjectId(s)
                    if obj_id not in sizes:
                        sizes.append(obj_id)
                update_data['size_ids'] = sizes
                if add_sizes or remove_sizes:
                    changed_fields.append('size_ids')

            if not update_data:
                return JsonResponse({'error': 'No fields provided to update'}, status=400)

            update_data['updated_at'] = datetime.now(timezone.utc)

            products_col.update_one(
                {'_id': ObjectId(product_id)},
                {'$set': update_data}
            )

            # ---------- FETCH UPDATED PRODUCT ----------
            updated_product = products_col.find_one({'_id': ObjectId(product_id)})
            
            product_update_log(update_data,product, user)

            return JsonResponse({
                'message': 'Product updated successfully',
                'updated_fields': changed_fields,
                'product_id': str(product_id)
            }, status=200)

        # ---------- GET PRODUCT ----------
        elif request.method == 'GET':
            product['_id'] = str(product['_id'])
            product['category_id'] = str(product.get('category_id')) if product.get('category_id') else None
            product['color_ids'] = [str(c) for c in product.get('color_ids', [])]
            product['size_ids'] = [str(s) for s in product.get('size_ids', [])]
            product['created_at'] = product['created_at'].isoformat()
            product['updated_at'] = product.get('updated_at')

            return JsonResponse({'product': product}, status=200)

        else:
            return JsonResponse({'error': 'Method not allowed'}, status=405)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)




#delete product
@api_view(['DELETE'])
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
            product=products_col.find_one({"_id":ObjectId(product_id)})
            result = products_col.delete_one({'_id': ObjectId(product_id)})
            if result.deleted_count == 0:
                return JsonResponse({'error': 'Product not found'}, status=404)

            product_deletion_log(product,user)
            return JsonResponse({'message': 'Product deleted successfully'}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
    
#get all the prducts
@api_view(['GET'])
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

@api_view(['PUT', 'PATCH'])
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
        
        
        
# export product data as csv
@api_view(['GET'])
def export_products_csv(request):
    
    try:
        if request.method == 'GET':
            products = list(products_col.find({}))

            # Create the HttpResponse object with CSV header
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="products.csv"'

            writer = csv.writer(response)
            # Write CSV header
            writer.writerow(['Product ID', 'Name', 'Description', 'Price', 'Category ID',
                             'Color IDs', 'Size IDs', 'Image URLs', 'Stock',
                             'Sold Count', 'Created By', 'Created At', 'Updated At'])

            for product in products:
                writer.writerow([
                    str(product['_id']),
                    product.get('name', ''),
                    product.get('description', ''),
                    product.get('price', 0),
                    str(product.get('category_id')) if product.get('category_id') else '',
                    ','.join([str(cid) for cid in product.get('color_ids', [])]),
                    ','.join([str(sid) for sid in product.get('size_ids', [])]),
                    ','.join(product.get('image_urls', [])),
                    product.get('stock', 0),
                    product.get('sold_count', 0),
                    product.get('created_by', ''),
                    product['created_at'].isoformat() if product.get('created_at') else '',
                    product['updated_at'].isoformat() if product.get('updated_at') else ''
                ])

            return response

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)