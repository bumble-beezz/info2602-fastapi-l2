from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()

class User(SQLModel, table=True):
    id: Optional[int] =  Field(default=None, primary_key=True)
    username:str = Field(index=True, unique=True)
    email:str = Field(index=True, unique=True)
    password:str

    todos: List["Todo"] = Relationship(back_populates="user")
    categories: List["Category"] = Relationship(back_populates="user")
    
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.set_password(password)
    
    def set_password(self, password):
        self.password = password_hash.hash(password)

    def add_todo_category(self, todo_id:int, category_text: str):
        """"Add a category to a todo (to be implemented)"""
        pass

    def __str__(self) -> str:
        return f"(User id={self.id}, username={self.username} ,email={self.email})"

class TodoCategory(SQLModel, table=True):
    todo_id: int = Field(foreign_key='todo.id', primary_key=True)
    category_id: int = Field(foreign_key='category.id', primary_key=True)

    todo: "Todo" = Relationship(back_populates="category_links")
    category: "Category" = Relationship(back_populates="todo_links")
    
class Category(SQLModel, table=True):
    id: Optional[int] =  Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key='user.id') #set user_id as a fk to user.id 
    text: str = Field(max_length=255)

    user: "User" = Relationship(back_populates="categories")
    todos: List["Todo"] = Relationship(back_populates="categories", link_model=TodoCategory)
    todo_links: List["TodoCategory"] = Relationship(back_populates="category")

    def __str__(self) -> str:
        return f"(Category id={self.id}, text='{self.text}', user_id={self.user_id})"

class Todo(SQLModel, table=True):
    id: Optional[int] = Field(default= None, primary_key=True)
    user_id: int = Field(foreign_key="user.id") #FK linking to User
    text: str = Field(max_length=255)
    done: bool = Field(default= False)

    #each todo belongs to one user
    user: User = Relationship(back_populates="todos")
    categories: List["Category"] = Relationship(back_populates="todos", link_model=TodoCategory)
    category_links: List["TodoCategory"] = Relationship(back_populates="todo")

    
    def toggle(self):
        """Toggle the done status of the todo"""
        self.done = not self.done

    def __str__(self) -> str:
        status = "Done" if self.done else "Not Done"
        return f"(Todo id={self.id}, user_id={self.user_id}, text= '{self.text}', status={status})"
    

