from fastapi import APIRouter

auth_router = APIRouter()

@auth_router.post("/login")
def login():
    return {"message": "Login endpoint"}

@auth_router.post("/register")
def register():
    return {"message": "Register endpoint"}
