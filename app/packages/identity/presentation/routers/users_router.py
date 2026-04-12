from fastapi import APIRouter

users_router = APIRouter()

@users_router.get("/")
def get_users():
    return {"message": "List of users"}

@users_router.get("/{user_id}")
def get_user(user_id: int):
    return {"message": f"User {user_id}"}
