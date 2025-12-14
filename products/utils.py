import cloudinary.uploader

def upload_images(files):
    urls = []
    for file in files:
        result = cloudinary.uploader.upload(file)
        urls.append(result["secure_url"])
    return urls
