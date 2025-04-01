from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Create a single instance of SQLAlchemy
db = SQLAlchemy(model_class=Base)