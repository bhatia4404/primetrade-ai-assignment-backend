from pydantic import BaseModel
from typing import Optional
class User(BaseModel):
    username : str
    password : str
    firstname : str
    lastname : Optional[str] = None
    role: str

class Product(BaseModel):
    product_id: int
    name: str
    price: float
    description: Optional[str] = None


class healthcheckResponse(BaseModel):
    status: str