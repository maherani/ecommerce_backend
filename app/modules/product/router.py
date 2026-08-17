from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.modules.product import models, schemas
from app.modules.user.router import get_current_admin_user

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
def get_products(db: Session = Depends(get_db)):
    """دریافت لیست تمام محصولات (عمومی)"""
    return db.query(models.Product).all()

@router.post("/products/", response_model=schemas.ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db),
    admin_user = Depends(get_current_admin_user)
):
    """ساخت محصول جدید (فقط مدیر)"""
    # بررسی وجود دسته‌بندی
    category = db.query(models.Category).filter(models.Category.id == product.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
        
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product
