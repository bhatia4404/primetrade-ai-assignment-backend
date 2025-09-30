from fastapi import FastAPI,Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
import jwt
from http import HTTPStatus
from typing import Optional
import bcrypt
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

#DB
from db import users,products
###
@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/register")
def register(user : UserSignup):
    try:
        username=user.username.lower()
        password=user.password
        firstname=user.firstname
        lastname=user.lastname
        role=user.role.lower()
        for u in users:
            if u["username"]==username:
                return {"error": "User already exists"}
        hashedPassword=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        password=hashedPassword.decode('utf-8')
        # add to db
        users.append({"username":username,"password":password,"firstname":firstname,"lastname":lastname,"role":role})
        print("User Registered : ",users[-1])
        token = jwt.encode({"username": user.username}, "secret", algorithm="HS256")
        return {"token": token} 
    except Exception as e:
        return JSONResponse(content={"error": "Something went wrong"},status_code=HTTPStatus.INTERNAL_SERVER_ERROR)


@app.post("/login")
def login(user : UserSignin):
    try:
        for u in users:
            if u["username"]==user.username:
                if bcrypt.checkpw(user.password.encode('utf-8'), u["password"].encode('utf-8')):
                    # Generate JWT token
                    token = jwt.encode({"username": user.username}, "secret", algorithm="HS256")
                    return JSONResponse(content={"token": token},status_code=HTTPStatus.OK)
        return {"error": "Invalid credentials"}   
    except Exception as e:
        return JSONResponse(content={"error": "Something went wrong"},status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    

@app.get("/products")
def get_products(authorization: HTTPAuthorizationCredentials = Security(security_scheme)):
    # print("Authorization Header: ",authorization)
    if authorization is None:
        return JSONResponse(content={"error": "Authorization token missing"},status_code=HTTPStatus.UNAUTHORIZED)
    try:
        user=jwt.decode(authorization.credentials, "secret", algorithms=["HS256"])
        return JSONResponse(content={"products": products,"user":user},status_code=HTTPStatus.OK)
    except jwt.ExpiredSignatureError:
        return JSONResponse(content={"error": "Token has expired"},status_code=HTTPStatus.UNAUTHORIZED)
    except jwt.InvalidTokenError:
        return JSONResponse(content={"error": "Invalid token"},status_code=HTTPStatus.UNAUTHORIZED)