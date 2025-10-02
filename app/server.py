from fastapi import FastAPI,Security,Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
import jwt
from http import HTTPStatus
from typing import Optional
import bcrypt
from .database import (add_user,delete_product,retrieve_user,retrieve_users,retrieve_products,add_product)
from fastapi.encoders import jsonable_encoder
from .schema import Product,healthcheckResponse
app=FastAPI()
security_scheme = HTTPBearer()

#Classes for request and response models
class UserSignin(BaseModel):
    username : str
    password : str

class UserSignup(BaseModel):
    username : str
    password : str
    firstname : str
    lastname : Optional[str] = None
    role: str
    @field_validator('role')
    def validate_role(cls, value):
        if value.lower() not in ['admin', 'user']:
            raise ValueError('Role must be either admin or user')
        return value

# Simple health check endpoint
@app.get("/health")
def health_check() -> healthcheckResponse:
    return {"status": "ok"}

@app.post("/register")
async def register(user : UserSignup) -> dict:
    try:
        username=user.username.lower()
        password=user.password
        firstname=user.firstname
        lastname=user.lastname
        role=user.role.lower()
        users=await retrieve_users()
        # print(users)
        for u in users:
            if u["username"]==username:
                return {"error": "User already exists"}
        hashedPassword=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        password=hashedPassword.decode('utf-8')
        user_data = {
            "username": username,
            "password": password,
            "firstname": firstname,
            "lastname": lastname,
            "role": role
        }
        user = await add_user(user_data)
        userjson = jsonable_encoder(user)
        # print("User Registered : ",userjson)
        # add to db
        # users.append({"username":username,"password":password,"firstname":firstname,"lastname":lastname,"role":role})
        # print("User Registered : ",users[-1])
        token = jwt.encode({"username": userjson["username"],"role":userjson["role"]}, "secret", algorithm="HS256")
        response= JSONResponse(content={"message": "Logged in","token":token},status_code=HTTPStatus.OK)
        response.set_cookie(key="token", value=token, httponly=True,samesite='Lax')
        return response
    except Exception as e:

        return JSONResponse(content={"error": str(e)},status_code=HTTPStatus.INTERNAL_SERVER_ERROR)


@app.post("/login")
async def login(user : UserSignin) -> dict:
    try:
        users=await retrieve_users()
        for u in users:
            if u["username"]==user.username:
                if bcrypt.checkpw(user.password.encode('utf-8'), u["password"].encode('utf-8')):
                    # Generate JWT token
                    token = jwt.encode({"username": user.username,"role":u["role"]}, "secret", algorithm="HS256")
                    response= JSONResponse(content={"message": "Logged in","token":token},status_code=HTTPStatus.OK)
                    response.set_cookie(key="token", value=token, httponly=True,samesite='Lax')
                    return response
        return {"error": "Invalid credentials"}   
    except Exception as e:
        print(e)
        return JSONResponse(content={"error": "Something went wrong"},status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    

@app.get("/products")
async def get_products(authorization: HTTPAuthorizationCredentials = Security(security_scheme)) -> list[Product]:
    # print("Authorization Header: ",authorization)
    if authorization is None:
        return JSONResponse(content={"error": "Authorization token missing"},status_code=HTTPStatus.UNAUTHORIZED)
    try:
        user=jwt.decode(authorization.credentials, "secret", algorithms=["HS256"])
        products=await retrieve_products()

        return JSONResponse(content={"products": products},status_code=HTTPStatus.OK)
    except jwt.ExpiredSignatureError:
        return JSONResponse(content={"error": "Token has expired"},status_code=HTTPStatus.UNAUTHORIZED)
    except jwt.InvalidTokenError:
        return JSONResponse(content={"error": "Invalid token"},status_code=HTTPStatus.UNAUTHORIZED)
    
@app.post("/add_product")
async def add_product_endpoint(product : Product, authorization: HTTPAuthorizationCredentials = Security(security_scheme)):
    if authorization is None:
        return JSONResponse(content={"error": "Authorization token missing"},status_code=HTTPStatus.UNAUTHORIZED)
    try:
        
        user=jwt.decode(authorization.credentials, "secret", algorithms=["HS256"])
        if user is None:
            return JSONResponse(content={"error": "Invalid token"},status_code=HTTPStatus.UNAUTHORIZED)
        # Check if the user has admin role
        current_user = await retrieve_user(user["username"])
        if current_user is None or current_user.get("role") != "admin":
            return JSONResponse(content={"error": "Admin privileges required"},status_code=HTTPStatus.FORBIDDEN)
        
         # Add the new product to the database
        product=product.model_dump()
        if product["product_id"] <= 0:
            return JSONResponse(content={"error": "Product ID must be a positive integer"},status_code=HTTPStatus.BAD_REQUEST)
        if product["price"] <= 0:
            return JSONResponse(content={"error": "Price must be a positive integer"},status_code=HTTPStatus.BAD_REQUEST)
        products=await retrieve_products()
        for p in products:
            if p["product_id"]==product["product_id"]:
                return JSONResponse(content={"error": "Product with this ID already exists"},status_code=HTTPStatus.BAD_REQUEST)
        new_product = await add_product(product)
        return JSONResponse(content={"product": new_product,"message":"Product created"},status_code=HTTPStatus.CREATED)
    except jwt.ExpiredSignatureError:
        return JSONResponse(content={"error": "Token has expired"},status_code=HTTPStatus.UNAUTHORIZED)
    except jwt.InvalidTokenError:
        return JSONResponse(content={"error": "Invalid token"},status_code=HTTPStatus.UNAUTHORIZED)
    except Exception as e:
        # print(e)
        return JSONResponse(content={"error": str(e)},status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
@app.put("/delete_product/{product_id}")
async def delete_product(product_id: int, authorization: HTTPAuthorizationCredentials = Security(security_scheme)):
    if authorization is None:
        return JSONResponse(content={"error": "Authorization token missing"},status_code=HTTPStatus.UNAUTHORIZED)
    try:
        
        user=jwt.decode(authorization.credentials, "secret", algorithms=["HS256"])
        if user is None:
            return JSONResponse(content={"error": "Invalid token"},status_code=HTTPStatus.UNAUTHORIZED)
        # Check if the user has admin role
        current_user =await retrieve_user(user["username"])
        if current_user is None or current_user.get("role") != "admin":
            return JSONResponse(content={"error": "Admin privileges required"},status_code=HTTPStatus.FORBIDDEN)
        
         # Delete the product from the database
        products=await retrieve_products()
        product_to_delete = next((p for p in products if int(p["product_id"]) == int(product_id)), None)
        if product_to_delete is None:
            return JSONResponse(content={"error": "Product not found"},status_code=HTTPStatus.NOT_FOUND)
        await delete_product(product_id)
        return JSONResponse(content={"message":"Product deleted"},status_code=HTTPStatus.OK)
    except jwt.ExpiredSignatureError:
        return JSONResponse(content={"error": "Token has expired"},status_code=HTTPStatus.UNAUTHORIZED)
    except jwt.InvalidTokenError:
        return JSONResponse(content={"error": "Invalid token"},status_code=HTTPStatus.UNAUTHORIZED)
    except Exception as e:
        # print(e)
        return JSONResponse(content={"error": str(e)},status_code=HTTPStatus.INTERNAL_SERVER_ERROR)