from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)

    # رابطه یک به چند با محصولات
    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # کلید خارجی برای اتصال به جدول دسته‌بندی‌ها
    category_id = Column(Integer, ForeignKey("categories.id"))

    # رابطه با دسته‌بندی
    category = relationship("Category", back_populates="products")
