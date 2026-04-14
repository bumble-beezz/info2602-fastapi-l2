from fastapi import APIRouter
from .todo import todo_router
from app.auth import auth_router

main_router = APIRouter()

main_router.include_router(auth_router)
main_router.include_router(todo_router)