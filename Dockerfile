# استفاده از نسخه سبک پایتون به عنوان پایه
FROM python:3.12-slim

# جلوگیری از نوشتن فایل‌های کش پایتون و نمایش سریع لاگ‌ها
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# تنظیم دایرکتوری کاری داخل کانتینر
WORKDIR /app

# کپی کردن فقط فایل لیست وابستگی‌ها ابتدا (برای استفاده از کش داکر در صورت عدم تغییر کتابخانه‌ها)
COPY requirements.txt .

# نصب کتابخانه‌ها
RUN pip install --no-cache-dir -r requirements.txt

# کپی کردن بقیه فایل‌های پروژه
COPY . .

# دستوری که موقع اجرای کانتینر اجرا می‌شود
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
