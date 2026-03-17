from contextlib import contextmanager
from sqlmodel import Session, SQLModel, create_engine
from typing import Annotated
from fastapi import Depends
from . import models

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def drop_all():
    SQLModel.metadata.drop_all(bind=engine)

def _session_generator():
    with Session(engine) as session:
        yield session

def get_session():
    yield from _session_generator()

@contextmanager
def get_cli_session():
    yield from _session_generator()


SessionDep = Annotated[Session, Depends(get_session)]