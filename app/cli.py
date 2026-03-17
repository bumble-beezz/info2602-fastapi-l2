import typer
import csv
from tabulate import tabulate
from sqlmodel import select
from app.database import create_db_and_tables, get_cli_session, drop_all
from app.models import *
from app.auth import encrypt_password

cli = typer.Typer()

@cli.command()
def initialize():
    """Here we initialized the database by dropping all the tables and recreating them about defaults and loading todos from CSV"""
    with get_cli_session() as db: # Get a connection to the database
        drop_all() # delete all tables
        create_db_and_tables() #recreate all tables
        
        # Create sample users
        bob = RegularUser(username='bob', email='bob@mail.com')
        bob.set_password('bobpass')
        rick = RegularUser(username='rick', email='rick@mail.com')
        rick.set_password('rickpass')
        sally = RegularUser(username='sally', email='sally@mail.com')
        sally.set_password('sallypass')
        
        db.add_all([bob, rick, sally])  #add all can save multiple objects at once
        db.commit()
        db.refresh(bob)
        db.refresh(rick)
        db.refresh(sally)

        # Load todos from CSV if it exists
        try:
            with open('todos.csv') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    new_todo = Todo(text=row['text'])  #create object
                    #update fields based on records
                    new_todo.done = True if row['done'].lower() == 'true' else False
                    new_todo.user_id = int(row['user_id'])
                    db.add(new_todo)  #queue changes for saving
                db.commit()
            print("Loaded todos from todos.csv")
        except FileNotFoundError:
            print("No todos.csv found. Database initialized with users only.")
        except Exception as e:
            print(f"Error loading todos: {e}")

        print("Database Initialized !!")

@cli.command()
def get_user(username:str):
    """get a user by their exact username"""
    with get_cli_session() as db: # Get a connection to the database
        user = db.exec(select(RegularUser).where(RegularUser.username == username)).first()
        if not user:
            user = db.exec(select(Admin).where(Admin.username == username)).first()
        if not user:
            print(f'{username} not found!')
            return
        print(user)

@cli.command()
def get_all_users():
    """display all the users in the database"""
    with get_cli_session() as db:
        regular_users = db.exec(select(RegularUser)).all()
        admins = db.exec(select(Admin)).all()
        all_users = list(regular_users) + list(admins)
        if not all_users:
            print("No users found")
        else:
            data = []
            for user in all_users:
                user_type = "Admin" if isinstance(user, Admin) else "Regular"
                data.append([user.id, user.username, user.email, user.role, user_type])
            print(tabulate(data, headers=["ID", "Username", "Email", "Role", "Type"]))

@cli.command()
def change_email(username: str, new_email:str):
    """update a user's email address"""
    with get_cli_session() as db: # Get a connection to the database
        user = db.exec(select(RegularUser).where(RegularUser.username == username)).first()
        if not user:
            user = db.exec(select(Admin).where(Admin.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to update email.')
            return
        user.email = new_email
        db.add(user)
        db.commit()
        print(f"Updated {user.username}'s email to {user.email}")

@cli.command(name="find-user")
def find_user(search_term: str):
    """find users using a partial match of their email or their username"""
    with get_cli_session() as db:
        regular_users = db.exec(
            select(RegularUser).where(
                (RegularUser.username.contains(search_term)) | 
                (RegularUser.email.contains(search_term))
            )
        ).all()
        
        admins = db.exec(
            select(Admin).where(
                (Admin.username.contains(search_term)) | 
                (Admin.email.contains(search_term))
            )
        ).all()
        
        users = list(regular_users) + list(admins)
        
        if not users:
            print(f"No users found matching '{search_term}'")
            return
        
        print(f"Found {len(users)} user(s) matching '{search_term}':")
        data = []
        for user in users:
            user_type = "Admin" if isinstance(user, Admin) else "Regular"
            data.append([user.id, user.username, user.email, user_type])
        print(tabulate(data, headers=["ID", "Username", "Email", "Type"]))

@cli.command(name="list-users")
def list_users(
    limit: int = typer.Argument(10, help="Maximum number of users to return (default: 10)"),
    offset: int = typer.Argument(0, help="Number of users to skip (default: 0)")
):
    """list the first N users of the database"""
    with get_cli_session() as db:
        regular_users = db.exec(
            select(RegularUser).offset(offset).limit(limit)
        ).all()
        
        admins = db.exec(
            select(Admin).offset(offset).limit(limit)
        ).all()
        
        users = list(regular_users) + list(admins)
        
        if not users:
            print("No users found")
            return
        
        total_regular = len(db.exec(select(RegularUser)).all())
        total_admins = len(db.exec(select(Admin)).all())
        total_users = total_regular + total_admins
        
        print(f"Showing users {offset + 1} to {min(offset + limit, total_users)} of {total_users} total users:")
        data = []
        for user in users:
            user_type = "Admin" if isinstance(user, Admin) else "Regular"
            data.append([user.id, user.username, user.email, user_type])
        print(tabulate(data, headers=["ID", "Username", "Email", "Type"]))
                              
@cli.command()
def create_user(username: str, email:str, password: str):
    """create a new regular user with information provided"""
    with get_cli_session() as db: # Get a connection to the database
        newuser = RegularUser(username=username, email=email)
        newuser.set_password(password)
        try:
            db.add(newuser)
            db.commit()
            db.refresh(newuser)
        except Exception as e:
            db.rollback()
            print("Username or email already taken!")
        else:
            print(f"Created regular user: {newuser}")

@cli.command()
def create_admin(username: str, email:str, password: str, staff_id: str):
    """create a new admin user with information provided"""
    with get_cli_session() as db:
        newadmin = Admin(username=username, email=email, staff_id=staff_id)
        newadmin.set_password(password)
        try:
            db.add(newadmin)
            db.commit()
            db.refresh(newadmin)
        except Exception as e:
            db.rollback()
            print("Username or email already taken!")
        else:
            print(f"Created admin user: {newadmin}")

@cli.command()
def add_task(username:str, task:str):
    """add a task for a specific user"""
    with get_cli_session() as db:
        user = db.exec(select(RegularUser).where(RegularUser.username == username)).one_or_none()
        if not user:
            print("User doesn't exist")
            return
        todo = Todo(text=task, user_id=user.id)
        db.add(todo)
        db.commit()
        print(f"Task added for user {username}")

@cli.command()
def toggle_todo(todo_id:int, username:str):
    """toggle the done status of a todo"""
    with get_cli_session() as db:
        todo = db.exec(select(Todo).where(Todo.id == todo_id)).one_or_none()
        if not todo:
            print("This todo doesn't exist")
            return
        if todo.user.username != username:
            print(f"This todo doesn't belong to {username}")
            return

        todo.toggle()
        db.add(todo)
        db.commit()
        db.refresh(todo)

        print(f"Todo item's done state set to {todo.done}")

@cli.command()
def list_todo_categories(todo_id: int, username: str):
    """list all categories for a specific todo"""
    with get_cli_session() as db:
        # First verify the user exists
        user = db.exec(select(RegularUser).where(RegularUser.username == username)).one_or_none()
        if not user:
            print(f"User '{username}' not found!")
            return
        
        # Find the todo and verify it belongs to the user
        todo = db.exec(
            select(Todo).where(
                Todo.id == todo_id,
                Todo.user_id == user.id
            )
        ).one_or_none()
        
        if not todo:
            print(f"Todo with id {todo_id} doesn't exist for user '{username}'")
            return
        
        if not todo.categories:
            print(f"No categories found for todo '{todo.text}' (id: {todo_id})")
            return
        
        print(f"Categories for todo '{todo.text}':")
        data = []
        for category in todo.categories:
            data.append([category.id, category.text])
        print(tabulate(data, headers=["ID", "Category"]))

@cli.command()
def create_category(username:str, cat_text:str):
    """create a new category for a user"""
    with get_cli_session() as db: # Get a connection to the database
        user = db.exec(select(RegularUser).where(RegularUser.username == username)).one_or_none()
        if not user:
            print("User doesn't exist")
            return

        category = db.exec(select(Category).where(Category.text == cat_text, Category.user_id == user.id)).one_or_none()
        if category:
            print("Category exists! Skipping creation")
            return
        
        category = Category(text=cat_text, user_id=user.id)
        db.add(category)
        db.commit()
        db.refresh(category)

        print(f"Category '{cat_text}' added for user {username}")

@cli.command()
def list_user_categories(username:str):
    """list all categories for a user"""
    with get_cli_session() as db: # Get a connection to the database
        user = db.exec(select(RegularUser).where(RegularUser.username == username)).one_or_none()
        if not user:
            print("User doesn't exist")
            return
        categories = db.exec(select(Category).where(Category.user_id == user.id)).all()
        
        if not categories:
            print(f"No categories found for user {username}")
            return
        
        data = []
        for category in categories:
            data.append([category.id, category.text])
        print(tabulate(data, headers=["ID", "Category"]))

@cli.command()
def assign_category_to_todo(username: str, todo_id: int, category_text: str):
    """assign a category to a todo (creates category if it doesn't exist)"""
    with get_cli_session() as db:
        user = db.exec(select(RegularUser).where(RegularUser.username == username)).one_or_none()
        if not user:
            print("User doesn't exist")
            return
        
        # Find or create the category
        category = db.exec(
            select(Category).where(
                Category.text == category_text, 
                Category.user_id == user.id
            )
        ).one_or_none()
        
        if not category:
            category = Category(text=category_text, user_id=user.id)
            db.add(category)
            db.commit()
            db.refresh(category)
            print(f"Category '{category_text}' created for user")
        
        # Find the todo
        todo = db.exec(
            select(Todo).where(
                Todo.id == todo_id, 
                Todo.user_id == user.id
            )
        ).one_or_none()
        
        if not todo:
            print("Todo doesn't exist for user")
            return
        
        # Check if already assigned
        if category in todo.categories:
            print(f"Todo already has category '{category_text}'")
            return
        
        # Assign category to todo
        todo.categories.append(category)
        db.add(todo)
        db.commit()
        print(f"Added category '{category_text}' to todo")

@cli.command(name="list-all-todos")
def list_all_todos():
    """Output each todo's ID, text, username and done status"""
    with get_cli_session() as db:
        todos = db.exec(select(Todo).order_by(Todo.id)).all()
        
        if not todos:
            print("No todos found")
            return
        
        print("All Todos:")
        print("-" * 60)
        data = []
        for todo in todos:
            status = "✓" if todo.done else "○"
            data.append([todo.id, status, todo.user.username, todo.text, todo.get_cat_list()])
        print(tabulate(data, headers=["ID", "Status", "User", "Text", "Categories"]))

@cli.command(name="list-todos")
def list_todos():
    """List all todos in the app with their categories"""
    with get_cli_session() as db:
        todos = db.exec(select(Todo).order_by(Todo.id)).all()
        
        if not todos:
            print("No todos found")
            return
        
        data = []
        for todo in todos:
            data.append([
                todo.text,
                "True" if todo.done else "False",
                todo.user.username if todo.user else "Unknown",
                todo.get_cat_list()
            ])
        
        print(tabulate(data, headers=["Text", "Done", "User", "Categories"]))

@cli.command(name="delete-todo")
def delete_todo(todo_id: int, username: str = None):
    """Delete a todo by ID. Optionally verify it belongs to a specific user."""
    with get_cli_session() as db:
        # Find the todo
        query = select(Todo).where(Todo.id == todo_id)
        
        # If username provided, verify ownership
        if username:
            user = db.exec(select(RegularUser).where(RegularUser.username == username)).first()
            if not user:
                print(f"User '{username}' not found!")
                return
            query = query.where(Todo.user_id == user.id)
        
        todo = db.exec(query).first()
        
        if not todo:
            if username:
                print(f"Todo with ID {todo_id} not found for user '{username}'")
            else:
                print(f"Todo with ID {todo_id} not found")
            return
        
        # Store info for confirmation message
        todo_text = todo.text
        todo_user = todo.user.username
        
        # Delete the todo (cascading will handle TodoCategory links)
        db.delete(todo)
        db.commit()
        
        print(f"Deleted todo ID {todo_id}: '{todo_text}' (user: {todo_user})")

@cli.command(name="complete-all-todos")
def complete_all_todos(username: str):
    """Mark all of a user's todos as complete"""
    with get_cli_session() as db:
        # Find the user
        user = db.exec(select(RegularUser).where(RegularUser.username == username)).first()
        if not user:
            print(f"User '{username}' not found!")
            return
        
        # Get all incomplete todos for the user
        incomplete_todos = db.exec(
            select(Todo).where(
                Todo.user_id == user.id,
                Todo.done == False
            )
        ).all()
        
        if not incomplete_todos:
            print(f"User '{username}' has no incomplete todos")
            return
        
        # Mark each todo as complete
        count = 0
        for todo in incomplete_todos:
            todo.done = True
            db.add(todo)
            count += 1
        
        db.commit()
        
        print(f"Marked {count} todo(s) as complete for user '{username}':")
        for todo in incomplete_todos:
            print(f"  ✓ {todo.text}")

@cli.command(name="list-user-todos")
def list_user_todos(username: str, show_all: bool = False):
    """List all todos for a specific user. Use --show-all to include completed todos."""
    with get_cli_session() as db:
        # Find the user
        user = db.exec(select(RegularUser).where(RegularUser.username == username)).first()
        if not user:
            print(f"User '{username}' not found!")
            return
        
        # Build query
        query = select(Todo).where(Todo.user_id == user.id)
        if not show_all:
            query = query.where(Todo.done == False)
        
        todos = db.exec(query.order_by(Todo.id)).all()
        
        if not todos:
            if show_all:
                print(f"No todos found for user '{username}'")
            else:
                print(f"No incomplete todos found for user '{username}'")
            return
        
        # Count statistics
        total = db.exec(select(Todo).where(Todo.user_id == user.id)).all()
        completed = len([t for t in total if t.done])
        
        print(f"\nTodos for user '{username}':")
        print(f"Total: {len(total)} | Completed: {completed} | Pending: {len(total) - completed}")
        print("-" * 50)
        
        data = []
        for todo in todos:
            status = "✓" if todo.done else "○"
            data.append([todo.id, status, todo.text, todo.get_cat_list()])
        print(tabulate(data, headers=["ID", "Status", "Text", "Categories"]))

@cli.command()
def delete_user(username: str):
    """delete a user by their username"""
    with get_cli_session() as db:
        user = db.exec(select(RegularUser).where(RegularUser.username == username)).first()
        if not user:
            user = db.exec(select(Admin).where(Admin.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to delete user.')
            return
        db.delete(user)
        db.commit()
        print(f'{username} deleted')

if __name__ == "__main__":
    cli()