"""Pydantic schemas for request and response models."""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str


class UserRead(BaseModel):
    """Schema for reading user data in responses."""

    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        orm_mode = True


class Token(BaseModel):
    """Schema for JWT tokens."""

    access_token: str
    token_type: str = "bearer"


class RestaurantSchema(BaseModel):
    """Schema for restaurant data."""

    id: int
    name: str
    address: Optional[str] = None
    rating: float

    class Config:
        orm_mode = True


class DishSchema(BaseModel):
    """Schema for dish data."""

    id: int
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    rating: float
    restaurant_id: int

    class Config:
        orm_mode = True


class FavoriteSchema(BaseModel):
    """Schema for favorite relations."""

    id: int
    user_id: int
    dish_id: int
    dish: DishSchema

    class Config:
        orm_mode = True


class ScanResponse(BaseModel):
    """Schema for scan job response."""

    job_id: str


class ScanResult(BaseModel):
    """Schema for scan job result."""

    status: str
    results: Optional[List[DishSchema]] = None
