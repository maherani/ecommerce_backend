from app.core.database import SessionLocal
from app.modules.user.schemas import UserCreate
from app.modules.user import crud

def test_create_and_get_user():
    print("Testing CRUD operations...")
    
    db = SessionLocal()
    
    try:
        test_email = "alborz.test@example.com"
        
        # ۱. چک کردن اینکه آیا کاربر از قبل وجود دارد یا خیر
        existing_user = crud.get_user_by_email(db, email=test_email)
        if existing_user:
            print(f"-> User {test_email} already exists in database. Skipping creation.")
        else:
            # ۲. ساخت کاربر جدید با ارسال صحیح پارامترها
            user_in = UserCreate(email=test_email, password="MySecurePassword123")
            new_user = crud.create_user(db=db, user=user_in)
            print(f"-> Success! User created with ID: {new_user.id} and Email: {new_user.email}")
            
        print("Success! CRUD test completed successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_create_and_get_user()
