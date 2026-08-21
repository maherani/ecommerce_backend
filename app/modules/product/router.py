import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.modules.product import models, schemas
from app.modules.user.router import get_current_admin_user
from app.core.cache import redis_client  # اتصال کلاینت ردیس

router = APIRouter(tags=["Catalog"])

# ==========================
# Category Routes
# ==========================
@router.get("/categories/", response_model=List[schemas.CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    """دریافت لیست تمام دسته‌بندی‌ها (عمومی)"""
    return db.query(models.Category).all()

@router.post("/categories/", response_model=schemas.CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    admin_user = Depends(get_current_admin_user)
):
    """ساخت دسته‌بندی جدید (فقط مدیر)"""
    db_category = models.Category(name=category.name, description=category.description)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

# ==========================
# Product Routes
# ==========================
@router.get("/products/", response_model=List[schemas.ProductResponse])
def get_products(
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """دریافت لیست تمام محصولات با قابلیت جستجو، فیلتر، صفحه‌بندی و کش ردیس"""
    # ۱. تولید کلید کش منحصر‌به‌فرد بر اساس تمام پارامترهای ورودی
    cache_key = f"products_list:{skip}:{limit}:{search}:{category_id}"
    
    # ۲. بررسی وجود دیتا در کش ردیس
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    # ۳. در صورت نبودن در کش، خواندن از دیتابیس
    query = db.query(models.Product)

    if search:
        query = query.filter(models.Product.title.ilike(f"%{search}%"))
        
    if category_id:
        query = query.filter(models.Product.category_id == category_id)

    products = query.offset(skip).limit(limit).all()

    # ۴. تبدیل اشیای دیتابیس به فرمت JSON (با mode='json' جهت تبدیل صحیح تاریخ و قیمت)
    products_data = [
        schemas.ProductResponse.model_validate(p).model_dump(mode='json') 
        for p in products
    ]

    # ۵. ذخیره در کش به مدت ۵ دقیقه (۳۰۰ ثانیه)
    redis_client.setex(cache_key, 300, json.dumps(products_data))

    return products

@router.post("/products/", response_model=schemas.ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db),
    admin_user = Depends(get_current_admin_user)
):
    """ساخت محصول جدید (فقط مدیر)"""
    category = db.query(models.Category).filter(models.Category.id == product.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
        
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    # باطل کردن کش‌های قبلی لیست محصولات جهت نمایش محصول جدید
    for key in redis_client.scan_iter("products_list:*"):
        redis_client.delete(key)

    return db_product