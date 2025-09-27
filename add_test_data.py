"""Add test data to the database"""
from datetime import datetime, timedelta
from database import Base, engine, User, ConsumptionData, get_session

def add_test_data():
    session = get_session()
    try:
        # Create test user if it doesn't exist
        test_user = session.query(User).filter_by(auth0_id='test_user').first()
        if not test_user:
            test_user = User(
                auth0_id='test_user',
                email='test@example.com',
                name='Test User'
            )
            session.add(test_user)
            session.commit()

        # Add some consumption data for the last 30 days
        start_date = datetime.now() - timedelta(days=30)
        for day in range(30):
            date = start_date + timedelta(days=day)
            consumption = ConsumptionData(
                user_id=test_user.id,
                timestamp=date,
                electricity=25.0 + day * 0.5,  # Slight increase each day
                gas=2.0,
                water=200.0,
                car_miles=30.0,
                diet='mixed',
                household_size=3
            )
            session.add(consumption)
        
        session.commit()
        print("Test data added successfully!")
        
    except Exception as e:
        print(f"Error adding test data: {str(e)}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    # Create tables first
    Base.metadata.create_all(engine)
    add_test_data()
