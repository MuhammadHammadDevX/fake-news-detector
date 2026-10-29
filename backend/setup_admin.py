import os
import bcrypt
from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv

# Load env file to get the exact credentials we just saved
load_dotenv()

client = MongoClient('mongodb://localhost:27017/')
db = client['factify_db']

# 1. Strip admin rights from EVERYONE to guarantee ONLY ONE admin
db.users.update_many({'role': 'admin'}, {'$set': {'role': 'user'}})

# 2. Delete the old admin if it exists to recreate it cleanly
email = os.environ.get('ADMIN_EMAIL')
password = os.environ.get('ADMIN_PASSWORD')
db.users.delete_many({'email': email})

# 3. Create the SINGLE admin
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
db.users.insert_one({
    'name': 'System Administrator',
    'email': email,
    'password_hash': hashed,
    'role': 'admin',
    'created_at': datetime.now(timezone.utc)
})

print(f"Admin enforcement complete. ONLY {email} is now an admin.")
