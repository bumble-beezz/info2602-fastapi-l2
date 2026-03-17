from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()

class User(SQLModel, table=False):
    """Base User class that isn't stored in its own table"""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    password: str
    role: str = ""
    
    def set_password(self, password):
        """Set the user's password with hashing"""
        self.password = password_hash.hash(password)

    def __str__(self) -> str:
        return f"(User id={self.id}, username={self.username} ,email={self.email})"

class Admin(User, table=True):
    """Admin user who can access all todos in the application"""
    role: str = "admin"
    staff_id: str = Field(default=None, max_length=50)
    
    def get_json(self):
        """Return admin data as JSON"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "staff_id": self.staff_id,
            "role": self.role
        }
    
    def get_all_todos_json(self):
        """Get all todos in the system as JSON"""
        # This will be implemented with database access
        pass

class RegularUser(User, table=True):
    """Regular user who can create and manage their own todos"""
    role: str = "regular_user"
    
    todos: List["Todo"] = Relationship(back_populates="user")
    categories: List["Category"] = Relationship(back_populates="user")
    
    def add_todo(self, text: str):
        """Add a new todo for this user"""
        # This will be implemented with database access
        pass
    
    def delete_todo(self, todo_id):
        """Delete a todo belonging to this user"""
        # This will be implemented with database access
        pass
    
    def toggle_todo(self, todo_id):
        """Toggle the done status of a todo"""
        # This will be implemented with database access
        pass
    
    def update_todo(self, todo_id, text: str):
        """Update a todo's text"""
        # This will be implemented with database access
        pass
    
    def add_todo_category(self, todo_id: int, category_text: str):
        """Add a category to a todo"""
        # This will be implemented with database access
        pass
    
    def get_num_done(self) -> int:
        """Get the number of completed todos"""
        # This will be implemented with database access
        return 0
    
    def get_num_todos(self) -> int:
        """Get the total number of todos"""
        # This will be implemented with database access
        return 0
    
    def get_json(self):
        """Return regular user data as JSON"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role
        }

class TodoCategory(SQLModel, table=True):
    """Association table for Todo and Category many-to-many relationship"""
    category_id: int = Field(foreign_key="category.id", primary_key=True)
    todo_id: int = Field(foreign_key="todo.id", primary_key=True)

class Category(SQLModel, table=True):
    """Category model for organizing todos"""
    id: Optional[int] = Field(primary_key=True, default=None)
    user_id: int = Field(foreign_key="regularuser.id")
    text: str

    user: "RegularUser" = Relationship(back_populates="categories")
    todos: List["Todo"] = Relationship(back_populates="categories", link_model=TodoCategory)

    def __str__(self) -> str:
        return f"(Category id={self.id}, text='{self.text}', user_id={self.user_id})"

class Todo(SQLModel, table=True):
    """Todo model for tasks"""
    id: Optional[int] = Field(primary_key=True, default=None)
    user_id: int = Field(foreign_key="regularuser.id")
    text: str
    done: bool = False

    user: "RegularUser" = Relationship(back_populates="todos")
    categories: List["Category"] = Relationship(back_populates="todos", link_model=TodoCategory)
    
    def toggle(self):
        """Toggle the done status of the todo"""
        self.done = not self.done

    def get_json(self):
        """Return todo data as JSON"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "text": self.text,
            "done": self.done
        }
    
    def get_cat_list(self):
        """Get comma-separated list of category names"""
        return ', '.join([category.text for category in self.categories])

    def __str__(self) -> str:
        status = "Done" if self.done else "Not Done"
        return f"(Todo id={self.id}, user_id={self.user_id}, text='{self.text}', status={status})"