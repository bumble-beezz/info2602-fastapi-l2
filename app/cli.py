import typer
from app.database import create_db_and_tables, get_session, drop_all
from app.models import User
from fastapi import Depends
from sqlmodel import select
from sqlalchemy.exc import IntegrityError

cli = typer.Typer()

@cli.command()
def initialize():
    """Here we initialized the database by dropping all the tables and recreating them about a default called bob"""
    with get_session() as db: # Get a connection to the database
        drop_all() # delete all tables
        create_db_and_tables() #recreate all tables
        bob = User('bob', 'bob@mail.com', 'bobpass') # Create a new user (in memory)
        db.add(bob) # Tell the database about this new data
        db.commit() # Tell the database persist the data
        db.refresh(bob) # Update the user (we use this to get the ID from the db)
        print("Database Initialized")

@cli.command()
def get_user(username:str):
    """ get a user by their exacttt username"""
    with get_session() as db: # Get a connection to the database
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found!')
            return
        print(user)

@cli.command()
def get_all_users():
    """display all the users in the database"""
    with get_session() as db:
        all_users = db.exec(select(User)).all()
        if not all_users:
            print("No users found")
        else:
            for user in all_users:
                print(user)

@cli.command()
def change_email(username: str, new_email:str):
    """update a user's email address"""
    with get_session() as db: # Get a connection to the database
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to update email.')
            return
        user.email = new_email
        db.add(user)
        db.commit()
        print(f"Updated {user.username}'s email to {user.email}")


@cli.command(name="find-user")
def find_user(search_term: str):
    """find users using a partial match of ther email or their username"""
    with get_session() as db:
        users = db.exec(
            select(User).where(
                (User.username.contains(search_term)) | 
                (User.email.contains(search_term))
            )
        ).all()
        
        if not users:
            print(f"No users found matching '{search_term}'")
            return
        
        print(f"Found {len(users)} user(s) matching '{search_term}':")
        for user in users:
            print(user)

@cli.command(name="list-users")
def list_users(
    limit: int = typer.Argument(10, help="Maximum number of users to return (default: 10)"),
    offset: int = typer.Argument(0, help="Number of users to skip (default: 0)")
):
    """list the first N users of the database"""
    with get_session() as db:
        users = db.exec(
            select(User).offset(offset).limit(limit)
        ).all()
        
        if not users:
            print("No users found")
            return
        
        total_users = db.exec(select(User)).all()
        print(f"Showing users {offset + 1} to {min(offset + limit, len(total_users))} of {len(total_users)} total users:")
        for user in users:
            print(user)
                              
@cli.command()
def create_user(username: str, email:str, password: str):
    """create a new user with infomation provided"""
    with get_session() as db: # Get a connection to the database
        newuser = User(username, email, password)
        try:
            db.add(newuser)
            db.commit()
        except IntegrityError as e:
            db.rollback() #let the database undo any previous steps of a transaction
            #print(e.orig) #optionally print the error raised by the database
            print("Username or email already taken!") #give the user a useful message
        else:
            print(newuser) # print the newly created user


@cli.command()
def delete_user(username: str):
    """delete a user by their username"""
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to delete user.')
            return
        db.delete(user)
        db.commit()
        print(f'{username} deleted')


if __name__ == "__main__":
    cli()