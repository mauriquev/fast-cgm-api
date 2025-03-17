import os 
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

def clean_env(var_name):
    value = os.environ.get(var_name)
    if value is None:
        raise ValueError(f"Environment variable {var_name} is required but not set")
    # Remove surrounding quotes if present
    if isinstance(value, str) and value.startswith(("'", '"')) and value.endswith(("'", '"')):
        value = value[1:-1]
    return value

# from config import DB_PASSWORD, DB_USER, DB_HOST, DB_PORT, DB_NAME
DB_USER = clean_env("DB_USER")
DB_PASSWORD = clean_env("DB_PASSWORD")
DB_HOST = clean_env("DB_HOST")
DB_PORT = clean_env("DB_PORT")
DB_NAME = clean_env("DB_NAME")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Dependency function to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db  # The yield statement allows the function to be used as a dependency
    finally:
        db.close()