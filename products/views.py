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
type_col = db["products_type"] #product types collection
subcategories_col = db["subcategories"] #subcategories collection


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
        
        category_name = request.POST.get('category_name')
        catg_img = request.FILES.get('category_image')
        
        
        if not category_name:
            return JsonResponse({'error': 'Category name is required.'}, status=400)
        
        if not catg_img:
            return JsonResponse({'error': 'Category image is required.'}, status=400)
        
        # Check if category already exists
        existing_category = categories_col.find_one({'name': category_name})
        if existing_category:
            return JsonResponse({'error': 'Category already exists.'}, status=400)
        
        # Insert new category
        category_data = {'name': category_name.lower()}
        if catg_img:
            upload = cloudinary.uploader.upload(catg_img)
            category_data['image_url'] = upload['secure_url']
        
        result = categories_col.insert_one(category_data)
        
        #logging
        category = categories_col.find_one({'_id':ObjectId(result.inserted_id)})
        # attribute_creation_log(request,category,user)
        
        
        
        return JsonResponse({'message': 'Category added successfully.', 'category_id': str(result.inserted_id)}, status=201)
    
    
#subcategory 
@api_view(['POST'])
def add_subcategory(request, category_id):
    
    try:
        if not category_id:
            return JsonResponse({'error': 'Category ID is required.'}, status=400)

        sub_catg_name = request.POST.get('subcategory_name').lower()
        subcategory_name = sub_catg_name.strip()
        sub_catg_img = request.FILES.get('subcategory_image')
        
        if sub_catg_img:
            upload = cloudinary.uploader.upload(sub_catg_img)
            image_url = upload['secure_url']
        
        
        
        if not subcategory_name:
            return JsonResponse({'error': 'Subcategory name is required.'}, status=400)
        
        category = categories_col.find_one({'_id': ObjectId(category_id)})
        if not category:
            return JsonResponse({'error': 'Category not found.'}, status=404)
        
        # Check if subcategory already exists
        existing_subcategory = subcategories_col.find_one({"name":subcategory_name.lower(),"parent_id":ObjectId(category_id)})
        if existing_subcategory:
            return JsonResponse({'error': 'Subcategory already exists.'}, status=400)   
        
        # Insert new subcategory
        subcategory_data = {
            'name': subcategory_name.lower(),
            'parent_id': ObjectId(category_id),
            'image_url': image_url if sub_catg_img else None
        }
        
        result = subcategories_col.insert_one(subcategory_data)
        return JsonResponse({'message': 'Subcategory added successfully.', 'subcategory_id': str(result.inserted_id)}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
#attributes 

    
    
#list of subcategories based on category id
@api_view(['GET'])
def list_subcategories(request, category_id):
    
    try:
        if not category_id:
            return JsonResponse({'error': 'Category ID is required.'}, status=400)

        category = categories_col.find_one({'_id': ObjectId(category_id)})
        if not category:
            return JsonResponse({'error': 'Category not found.'}, status=404)
        subcategories = list(subcategories_col.find({'parent_id': ObjectId(category_id)}))
        for subcat in subcategories:
            subcat['_id'] = str(subcat['_id'])
            subcat['parent_id'] = str(subcat['parent_id'])
        return JsonResponse({'subcategories': subcategories}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(["GET"])
def all_subcategories(request):
    
    try:
        subcategories = list(subcategories_col.find({}))
        for subcat in subcategories:
            subcat['_id'] = str(subcat['_id'])
            subcat['parent_id'] = str(subcat['parent_id'])
        return JsonResponse({'subcategories': subcategories}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
    
    


#delete category
@api_view(['DELETE'])
def delete_category(request, category_id):
    # getting current user
    user, error = get_current_user(request)
    if error:
        return JsonResponse({'error': error}, status=401)

    # checking user is admin or moderator
    if not (is_user_admin(user) or is_user_moderator(user)):
        return JsonResponse(
            {'error': 'Unauthorized. Admin or moderator access required.'},
            status=403
        )

    if request.method == 'DELETE':
        category = categories_col.find_one({'_id': ObjectId(category_id)})
        if not category:
            return JsonResponse({'error': 'Category not found.'}, status=404)

        # delete category
        categories_col.delete_one({'_id': ObjectId(category_id)})

        # log deletion
        attribute_delation_log(request, category, user)

        # update products linked to this category
        products_col.update_many(
            {'category_id': ObjectId(category_id)},
            {'$set': {
                'category_id': "undefined",
                'subcategory_id': "undefined"
            }}
        )

        # delete subcategories
        subcategories_col.delete_many({'parent_id': ObjectId(category_id)})

        return JsonResponse({'message': 'Category deleted successfully.'}, status=200)



#delete subcategory
@api_view(['DELETE'])
def delete_subcategory(request, subcategory_id):
    #getting current user
    user,error = get_current_user(request)
    if error:
        return JsonResponse({'error': error}, status=401)
    
    
    #checking user is admin or moderator
    if not is_user_admin(user) or is_user_moderator(user):
        return JsonResponse({'error': 'Unauthorized. Admin  or moderator access required.'}, status=403)
    
    
    if request.method == 'DELETE':
        subcategory = subcategories_col.find_one({'_id':ObjectId(subcategory_id)})
        result = subcategories_col.delete_one({'_id': ObjectId(subcategory_id)})
        if result.deleted_count == 0:
            return JsonResponse({'error': 'Subcategory not found.'}, status=404)
        
        attribute_delation_log(request,subcategory,user)
        
        ###edititing all the product associated with this subcategory to have undifined subcategory id
        products_col.update_many(
            {'subcategory_id': ObjectId(subcategory_id)},
            {'$set': {'subcategory_id': "undefined"}}
        )
        
        return JsonResponse({'message': 'Subcategory deleted successfully.'}, status=200)
    
 


#----------- product type views -------------------- #
@api_view(['POSt'])
def create_type(request):
    
    if request.method == 'POST':
        
        body = json.loads(request.body)
        type_name = body.get('type_name')
        if not type_name:
            return JsonResponse({'error': 'Type name is required.'}, status=400)
        
        # Check if type already exists
        existiing_type = type_col.find_one({'name': type_name}) 
        if existiing_type:
            return JsonResponse({'error': 'Type already exists.'}, status=400)
        
        # Insert new type
        type_data = {'name': type_name.lower()}
        result = type_col.insert_one(type_data)
        return JsonResponse({'message': 'Type added successfully.', 'type_id': str(result.inserted_id)}, status=201)
    
#delete type
@api_view(['DELETE'])
def delete_type(request, type_id):
    
    if request.method == 'DELETE':
        result = type_col.delete_one({'_id': ObjectId(type_id)})
        if result.deleted_count == 0:
            return JsonResponse({'error': 'Type not found.'}, status=404)
        return JsonResponse({'message': 'Type deleted successfully.'}, status=200)
   
    
#get all the colors , size and categories
@api_view(['GET'])
def get_attributes(request):
    
    if request.method == 'GET':
        colors = list(colors_col.find({}, {'_id': 1, 'name': 1}))
        sizes = list(sizes_col.find({}, {'_id': 1, 'name': 1}))
        categories = list(categories_col.find({}))
        types = list(type_col.find({}))

        # Convert ObjectId to string for JSON serialization
        for color in colors:
            color['_id'] = str(color['_id'])
        for size in sizes:
            size['_id'] = str(size['_id'])
        for category in categories:
            category['_id'] = str(category['_id'])
            
        for type in types:
            type['_id'] = str(type['_id'])
        
            
        return JsonResponse({
            'colors': colors,
            'sizes': sizes,
            'categories': categories,
            'types': types
        }, status=200)


    
# ---------------- Product Views -------------------- #
#product create views for admin
@api_view(['POST','GET'])
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
            subcategory_id = request.POST.get('subcategory_id')
            stock = int(request.POST.get('stock', 0))
            color_ids = request.POST.getlist('color_ids')
            size_ids = request.POST.getlist('size_ids')
            images = request.FILES.getlist('images')
            gender = request.POST.get('gender', 'unisex')
            type = request.POST.get('type_id')
            
            if not name or not description or price <= 0 or stock < 0:
                return JsonResponse({'error': 'Please provide valid product details.'}, status=400)
            if not subcategory_id:
                return JsonResponse({'error': 'Subcategory ID is required.'}, status=400)
            
            
            if not category_id:
                return JsonResponse({'error': 'Category is required.'}, status=400)
            
            
            if gender not in ['male', 'female', 'unisex']:
                return JsonResponse({'error': 'Invalid gender value.'}, status=400)
            

            if not images or len(images) > 3:
                return JsonResponse({'error': 'Please upload between 1 to 3 images.'}, status=400)

            if not color_ids or not size_ids:
                return JsonResponse({'error': 'Color and size are required'}, status=400)
            
            #check if the subcategory belongs to category
            if subcategory_id:
                if not subcategory_id:
                    return JsonResponse({'error': 'Subcategory ID is required.'}, status=400)
                subcategory = subcategories_col.find_one({'_id': ObjectId(subcategory_id)})
                print(f'{subcategory} == {category_id}')
                if str(subcategory['parent_id']) != category_id:
                    return JsonResponse({'error': 'Subcategory does not belong to the specified category.'}, status=400)

            image_urls = []
            for image in images:
                upload = cloudinary.uploader.upload(image)
                image_urls.append(upload['secure_url'])

            product_data = {
                'name': name,
                'description': description,
                'gender': gender,
                'type': ObjectId(type),
                'price': price,
                'category_id': ObjectId(category_id) if category_id else None,
                'subcategory_id': ObjectId(subcategory_id) if subcategory_id else None,
                'color_ids': [ObjectId(cid) for cid in color_ids],
                'size_ids': [ObjectId(sid) for sid in size_ids],
                'image_urls': image_urls,
                'stock': stock,
                'sold_count': 0,
                'created_by': user['email'],
                'created_at': datetime.now(timezone.utc),
                'updated_at': None
            }

            result = products_col.insert_one(product_data)
            images = []
            
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
        product = products_col.find_one({'_id': ObjectId(product_id)})
        if not product:
            return JsonResponse({'error': 'Product not found'}, status=404)

        # Convert ObjectId fields to string
        product['_id'] = str(product['_id'])

        # FIX: convert `type`
        product['type'] = str(product['type']) if product.get('type') else None

        product['category_id'] = str(product['category_id']) if product.get('category_id') else None
        product['subcategory_id'] = str(product['subcategory_id']) if product.get('subcategory_id') else None

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
            for field in ['name', 'description', 'price', 'stock', 'category_id', 'image_urls','subcategory_id']:
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


import math
#get all the prducts
@api_view(['GET'])
def get_products(request):
    try:
        # -------- PAGINATION PARAMS --------
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))
        skip = (page - 1) * limit

        # -------- QUERY (LATEST FIRST) --------
        cursor = (
            products_col
            .find()
            .sort('created_at', -1)   # DESC order (latest first)
            .skip(skip)
            .limit(limit)
        )

        products = list(cursor)
        total_products = products_col.count_documents({})
        total_pages = math.ceil(total_products / limit)

        # -------- SERIALIZATION --------
        for product in products:
            product['_id'] = str(product['_id'])
            product['category_id'] = str(product['category_id']) if product.get('category_id') else None
            product['color_ids'] = [str(cid) for cid in product.get('color_ids', [])]
            product['size_ids'] = [str(sid) for sid in product.get('size_ids', [])]
            product['created_at'] = product['created_at'].isoformat() if product.get('created_at') else None
            product['updated_at'] = product['updated_at'].isoformat() if product.get('updated_at') else None

        return JsonResponse({
            'page': page,
            'limit': limit,
            'total_products': total_products,
            'total_pages': total_pages,
            'products': products
        }, status=200)

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
    
    
    
#filter and search products
@api_view(['GET'])
def product_list(request):
    
    
    
    # -------- Query Params --------
    search = request.GET.get("search")
    product_type = request.GET.get("type_id")
    gender = request.GET.get("gender")
    category = request.GET.get("category_id")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    sub_category = request.GET.get("subcategory_id")
    
    

    # Pagination
    page = int(request.GET.get("page", 1))
    limit = int(request.GET.get("limit", 10))
    skip = (page - 1) * limit

    # -------- MongoDB Filter --------
    query = {}

    # Search by name (case-insensitive)
    if search:
        query["name"] = {"$regex": search, "$options": "i"}

    if product_type:
        query["type"] = ObjectId(product_type)

    if gender:
        query["gender"] = gender

    if category:
        query["category_id"] = ObjectId(category)
    
    if sub_category:
        query["subcategory_id"] = ObjectId(sub_category)

    # Price range
    if min_price or max_price:
        query["price"] = {}
        if min_price:
            query["price"]["$gte"] = int(min_price)
        if max_price:
            query["price"]["$lte"] = int(max_price)

    # -------- Fetch Data --------
    total_products = products_col.count_documents(query)

    products = list(
        products_col.find(query)
        .skip(skip)
        .limit(limit)
        .sort("created_at", -1)
    )

    # Convert ObjectId → string
    for p in products:
        p["_id"] = str(p["_id"])
        p["category_id"] = str(p["category_id"])
        p["color_ids"] = [str(c) for c in p.get("color_ids", [])]
        p["size_ids"] = [str(s) for s in p.get("size_ids", [])]
        p['subcategory_id'] = str(p['subcategory_id'])
        p['type'] = str(p['type'])

    # -------- Pagination Info --------
    total_pages = math.ceil(total_products / limit)

    return JsonResponse({
        "page": page,
        "limit": limit,
        "total_products": total_products,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
        "results": products
    }, safe=False)
