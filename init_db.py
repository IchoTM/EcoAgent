"""Initialize the database and create tables"""
from database import Base, engine

def init_database():
    Base.metadata.create_all(engine)
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_database()
