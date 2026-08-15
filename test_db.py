from app.core.database import engine, Base
from app.modules.user.models import User

def test_database_creation():
    print("Connecting to database and creating tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Success! Table 'users' has been created successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_database_creation()
