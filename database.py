"""Database models and utilities for EcoAgent"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Create the SQLAlchemy engine
engine = create_engine('sqlite:///ecoagent.db')
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    auth0_id = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    # Add cascade delete to ensure all related data is deleted
    consumption_data = relationship(
        "ConsumptionData",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

class ConsumptionData(Base):
    __tablename__ = 'consumption_data'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Energy data
    electricity = Column(Float)
    gas = Column(Float)
    water = Column(Float)
    
    # Transportation data
    car_miles = Column(Float)
    public_transport = Column(Float)
    
    # Household data
    household_size = Column(Integer)
    
    user = relationship("User", back_populates="consumption_data")

# Create all tables
Base.metadata.create_all(engine)

# Create a session factory
Session = sessionmaker(bind=engine)

def get_session():
    """Get a new database session"""
    return Session()
