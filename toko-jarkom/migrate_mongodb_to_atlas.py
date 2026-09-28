import os

from pymongo import MongoClient


LOCAL_URI = os.environ.get('LOCAL_MONGODB_URI', 'mongodb://127.0.0.1:27018')
ATLAS_URI = os.environ.get('MONGODB_URI')
LOCAL_DATABASE = os.environ.get('LOCAL_MONGODB_DATABASE', 'toko')
ATLAS_DATABASE = os.environ.get('MONGODB_DATABASE', 'toko')
COLLECTIONS = ('supply', 'purchases')


def main():
	if not ATLAS_URI:
		raise SystemExit('Set MONGODB_URI to the MongoDB Atlas connection string first.')
	if ATLAS_URI == LOCAL_URI:
		raise SystemExit('Source and target URIs match; refusing to copy into the local database.')

	local_client = MongoClient(LOCAL_URI, serverSelectionTimeoutMS=5000)
	atlas_client = MongoClient(ATLAS_URI, serverSelectionTimeoutMS=10000)
	try:
		local_client.admin.command('ping')
		atlas_client.admin.command('ping')
		local_db = local_client[LOCAL_DATABASE]
		atlas_db = atlas_client[ATLAS_DATABASE]
		for collection_name in COLLECTIONS:
			copied = 0
			for document in local_db[collection_name].find():
				atlas_db[collection_name].replace_one(
					{'_id': document['_id']},
					document,
					upsert=True,
				)
				copied += 1
			print(f'{collection_name}: {copied} documents copied or updated')
	finally:
		local_client.close()
		atlas_client.close()


if __name__ == '__main__':
	main()