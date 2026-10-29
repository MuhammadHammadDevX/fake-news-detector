import pymongo
from pymongo import MongoClient

print("Connecting to MongoDB...")
client = MongoClient('mongodb://localhost:27017/')

old_db = client['fakeguard_db']
new_db = client['factify_db']

collections_to_migrate = ['users', 'feedbacks', 'contacts', 'analyses']

for coll_name in collections_to_migrate:
    print(f"Migrating collection '{coll_name}'...")
    old_col = old_db[coll_name]
    new_col = new_db[coll_name]
    
    docs = list(old_col.find({}))
    if not docs:
        print(f"  - No documents found in '{coll_name}'.")
        continue
        
    inserted_count = 0
    updated_count = 0
    for doc in docs:
        if coll_name == 'users' and 'email' in doc:
            query = {'email': doc['email']}
            # Ensure we don't accidentally overwrite an existing _id when matching by email
            doc_without_id = {k: v for k, v in doc.items() if k != '_id'}
            result = new_col.update_one(query, {'$set': doc_without_id}, upsert=True)
            if result.upserted_id:
                inserted_count += 1
            elif result.modified_count:
                updated_count += 1
        else:
            query = {'_id': doc['_id']}
            result = new_col.replace_one(query, doc, upsert=True)
            if result.upserted_id:
                inserted_count += 1
            elif result.modified_count:
                updated_count += 1
            
    print(f"  - Migrated {len(docs)} documents ({inserted_count} new, {updated_count} updated).")

print("Recreating database indexes...")
new_db['users'].create_index('email', unique=True)
print("  - Users collection unique email index created.")

print("Dropping old database 'fakeguard_db'...")
client.drop_database('fakeguard_db')
print("  - Old database dropped successfully.")

print("Migration completed successfully!")
