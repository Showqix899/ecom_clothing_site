from django.core.management.base import BaseCommand
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timedelta,timezone
import os
import certifi
from dotenv import load_dotenv
from products.views import products_col

load_dotenv()


class Command(BaseCommand):
    help = 'Seed 10 demo products into MongoDB'

    def handle(self, *args, **kwargs):

        client = MongoClient(
            os.getenv("MONGO_URI"),
            tls=True,
            tlsCAFile=certifi.where()
        )

        

        color_ids = [ObjectId("693ef72cc9420d62854f33b9")]
        size_ids = []

        image_urls = [
            "https://images.unsplash.com/photo-1522312346375-d1a52e2b99b3",
            "https://images.unsplash.com/photo-1524592094714-0f0654e20314"
        ]

        category_id = ObjectId("69738353aa6eae086a77cfcf")
        subcategory_id = ObjectId("69738354aa6eae086a77cfd3")

        products = []

        for i in range(1, 11):
            products.append({
                "name": f"Premium Watch Model {i}",
                "description": f"Premium quality analog watch version {i}.",
                "gender": "unisex",
                "type": ObjectId("695804d467f1a8364f33c53d"),
                "price": 150 + (i * 10),
                "category_id": category_id,
                "subcategory_id": subcategory_id,
                "color_ids": color_ids,
                "size_ids": size_ids,
                "image_urls": image_urls,
                "stock": 50 + i,
                "sold_count": i * 2,
                "created_by": "admin@zing.com",
                "created_at": datetime.now(timezone.utc) - timedelta(days=i),
                "updated_at": datetime.now(timezone.utc) - timedelta(days=i),
            })

        result = products_col.insert_many(products)

        self.stdout.write(self.style.SUCCESS(
            f"✅ Successfully seeded {len(result.inserted_ids)} products"
        ))
