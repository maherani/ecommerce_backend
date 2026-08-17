from pydantic import BaseModel
from typing import Optional

# ==========================
# Category Schemas
# ==========================
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int

    class Config:
        from_attributes = True

# ==========================
# Product Schemas
# ==========================
class ProductBase(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    is_active: bool = True
    category_id: int

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    category: Optional[CategoryResponse] = None

    class Config:
        from_attributes = True
