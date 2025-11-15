"""
Database Schemas for Property Sale App

Each Pydantic model corresponds to a MongoDB collection (lowercased class name).
- Property -> "property"
- Offer -> "offer"
- AdminSettings -> "adminsettings"
"""
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl, EmailStr


class Property(BaseModel):
    title: str = Field(..., description="Listing title")
    description: str = Field(..., description="Detailed description")
    address: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State/Province/Region")
    price: int = Field(..., ge=0, description="Price in whole currency units")
    bedrooms: int = Field(..., ge=0)
    bathrooms: float = Field(..., ge=0)
    area_sqft: int = Field(..., ge=0, description="Area in square feet")
    status: str = Field("available", description="available | under_offer | sold")
    images: List[HttpUrl] = Field(default_factory=list, description="Image gallery URLs")
    tags: List[str] = Field(default_factory=list)


class Offer(BaseModel):
    property_id: str = Field(..., description="Associated property _id as string")
    full_name: str = Field(...)
    email: EmailStr
    phone: Optional[str] = None
    amount: int = Field(..., ge=0)
    message: Optional[str] = None
    status: str = Field("pending", description="pending | accepted | rejected")


class AdminSettings(BaseModel):
    primary_color: str = Field("#f97316", description="Hex color for primary brand (default orange)")
    accent_color: str = Field("#111827", description="Hex color for accent/dark text")
    hero_heading: str = Field("Find your next place", description="Hero headline copy")
    hero_subheading: str = Field("Modern homes, transparent offers, secure management.", description="Hero subtitle copy")
    announcement: Optional[str] = Field("New listings dropping weekly — submit an offer in minutes!", description="Site-wide announcement banner text")
