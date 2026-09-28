import os

from pymongo import MongoClient

URI = os.environ.get('MONGODB_URI', 'mongodb://127.0.0.1:27018')
DATABASE_NAME = os.environ.get('MONGODB_DATABASE', 'toko')

db = MongoClient(URI)[DATABASE_NAME]
products = [
    {'nama': 'Kabel LAN 5m', 'harga': 25000, 'stok': 40},
    {'nama': 'Router WiFi', 'harga': 350000, 'stok': 10},
    {'nama': 'Switch 8 Port', 'harga': 180000, 'stok': 15},
    {'nama': 'Konektor RJ45', 'harga': 2000, 'stok': 200},
    {'nama': 'Kabel Jumpper', 'harga': 7500, 'stok': 500}
]

for product in products:
    db.supply.update_one(
        {'nama': product['nama']},
        {'$setOnInsert': product},
        upsert=True,
    )

print('Seed selesai; data yang sudah ada tetap aman')