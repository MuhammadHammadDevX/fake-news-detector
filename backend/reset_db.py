from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['factify_db']

db.users.delete_many({'email': 'audit1@example.com'})
db.users.delete_many({'email': 'admin@factify.com'})
db.users.update_many({'role': 'admin'}, {'$set': {'role': 'user'}})

print("Database reset successful.")
