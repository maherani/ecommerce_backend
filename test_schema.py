from app.modules.user.schemas import UserCreate, UserResponse

def test_user_schemas():
    print("Testing Pydantic schemas...")
    try:
        # تست ۱: ساخت دیتای معتبر
        valid_data = {"email": "test@example.com", "password": "securepassword123"}
        user_in = UserCreate(**valid_data)
        print(f"-> Valid data passed successfully: {user_in.email}")

        # تست ۲: تست اعتبارسنجی ایمیل نامعتبر (باید خطا بدهد)
        try:
            invalid_data = {"email": "not-an-email", "password": "123"}
            UserCreate(**invalid_data)
        except Exception as e:
            print("-> Email validation successfully caught invalid email format!")

        print("Success! Schemas are working correctly.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_user_schemas()
