import motor.motor_asyncio
DB_URL = "mongodb+srv://shivambhatiag_db_user:shivam123@cluster1.2olj9kl.mongodb.net/"
client = motor.motor_asyncio.AsyncIOMotorClient(DB_URL)
database = client.data
product_collection = database.get_collection("products_collection")
user_collection = database.get_collection("users_collection")
from bson.objectid import ObjectId
# helpers 
def user_helper(user) -> dict:
    return {
        "username": str(user["username"]),
        "password": user["password"],
        "firstname": user["firstname"],
        "lastname": user["lastname"],
        "role": user["role"],
    }
def product_helper(product) -> dict:
    return {
        "product_id": product["product_id"],
        "name": product["name"],
        "price": product["price"],
        "description": product["description"],
    }
# Retrieve all users present in the database
async def retrieve_users():
    users = []
    async for user in user_collection.find():
        users.append(user_helper(user))
    return users


# Add a new user into to the database
async def add_user(user_data: dict) -> dict:
    user = await user_collection.insert_one(user_data)
    new_user = await user_collection.find_one({"_id": user.inserted_id})
    return user_helper(new_user)


# Retrieve a user with a matching ID
async def retrieve_user(username: str) -> dict:
    user = await user_collection.find_one({"username":username })
    if user:
        return user_helper(user)


# Update a user with a matching ID
async def update_user(id: str, data: dict):
    # Return false if an empty request body is sent.
    if len(data) < 1:
        return False
    user = await user_collection.find_one({"_id": ObjectId(id)})
    if user:
        updated_user = await user_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": data}
        )
        if updated_user:
            return True
        return False


# Delete a user from the database
async def delete_user(id: str):
    user = await user_collection.find_one({"_id": ObjectId(id)})
    if user:
        await user_collection.delete_one({"_id": ObjectId(id)})
        return True
    
async def retrieve_products():
    products = []
    async for product in product_collection.find():
        products.append(product_helper(product))
    return products

async def add_product(product_data: dict) -> dict:
    product = await product_collection.insert_one(product_data)
    new_product = await product_collection.find_one({"_id": product.inserted_id})
    return product_helper(new_product)


# Sample Data
'''
{
    "product": {
        "product_id" : 1,
        "name":"product1",
        "price":100.00,
        "description":"Description of Product 1"
    }
}
'''