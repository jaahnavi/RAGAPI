from fastapi import FastAPI
from pydantic import BaseModel

app=FastAPI()

class User(BaseModel):
    name:str
    age:int

@app.get("/")
def home():
    return{"message":"Hello FastAPI"}

@app.get("/hello/{name}")
def say_hello(name:str):
    return{"message": f"Hello {name}"}

@app.post("/user")
def create_user(user:User):
    return{
        "success": True,
        "user":user
    }
