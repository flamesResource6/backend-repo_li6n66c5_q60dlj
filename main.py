import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Property, Offer, AdminSettings

app = FastAPI(title="Property Sale API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Property Sale API is running"}


@app.get("/schema")
def get_schema():
    return {
        "collections": ["property", "offer", "adminsettings"],
        "models": {
            "Property": Property.model_json_schema(),
            "Offer": Offer.model_json_schema(),
            "AdminSettings": AdminSettings.model_json_schema(),
        },
    }


# Utilities
class ObjectIdStr(BaseModel):
    id: str


def ensure_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")


# Seed dummy data endpoint
@app.post("/seed")
async def seed_dummy_data():
    # If collections empty, insert some docs
    counts = {
        "property": db["property"].count_documents({}) if db else 0,
        "offer": db["offer"].count_documents({}) if db else 0,
        "adminsettings": db["adminsettings"].count_documents({}) if db else 0,
    }

    # Settings
    if counts["adminsettings"] == 0:
        create_document(
            "adminsettings",
            AdminSettings(
                primary_color="#f97316",
                accent_color="#111827",
                hero_heading="Discover vibrant homes",
                hero_subheading="Browse, make offers, and manage listings seamlessly.",
                announcement="Welcome! This site uses demo data for preview.",
            ),
        )

    # Properties
    if counts["property"] == 0:
        demo_imgs = [
            "https://images.unsplash.com/photo-1505692794403-34d4982f88aa",
            "https://images.unsplash.com/photo-1568605114967-8130f3a36994",
            "https://images.unsplash.com/photo-1523217582562-09d0def993a6",
        ]
        props: List[Property] = [
            Property(
                title="Sunny Modern Loft",
                description="Open-plan loft with floor-to-ceiling windows and polished concrete floors.",
                address="123 Orange Ave",
                city="Los Angeles",
                state="CA",
                price=975000,
                bedrooms=2,
                bathrooms=1.5,
                area_sqft=1200,
                status="available",
                images=demo_imgs,
                tags=["loft", "downtown"],
            ),
            Property(
                title="Cozy Suburban Home",
                description="Family-friendly neighborhood, renovated kitchen, large backyard.",
                address="456 Grove St",
                city="Austin",
                state="TX",
                price=620000,
                bedrooms=3,
                bathrooms=2,
                area_sqft=1800,
                status="available",
                images=demo_imgs,
                tags=["suburbs", "yard"],
            ),
            Property(
                title="Penthouse with Skyline View",
                description="Top-floor penthouse featuring panoramic city views and a private terrace.",
                address="789 Skyline Blvd",
                city="Seattle",
                state="WA",
                price=1850000,
                bedrooms=4,
                bathrooms=3,
                area_sqft=2500,
                status="under_offer",
                images=demo_imgs,
                tags=["luxury", "view"],
            ),
        ]
        for p in props:
            create_document("property", p)

    return {"status": "ok"}


# Properties
@app.get("/properties")
async def list_properties(city: Optional[str] = None, status: Optional[str] = None):
    filter_q = {}
    if city:
        filter_q["city"] = city
    if status:
        filter_q["status"] = status
    docs = get_documents("property", filter_q)
    for d in docs:
        d["_id"] = str(d["_id"])  # serialize
    return docs


@app.get("/properties/{prop_id}")
async def get_property(prop_id: str):
    oid = ensure_object_id(prop_id)
    doc = db["property"].find_one({"_id": oid})
    if not doc:
        raise HTTPException(404, "Property not found")
    doc["_id"] = str(doc["_id"])  # serialize
    return doc


# Offers
@app.post("/offers")
async def submit_offer(offer: Offer):
    # Check property exists
    oid = ensure_object_id(offer.property_id)
    if not db["property"].find_one({"_id": oid}):
        raise HTTPException(404, "Property not found for this offer")
    offer_id = create_document("offer", offer)
    return {"id": offer_id, "status": "submitted"}


@app.get("/offers")
async def list_offers(property_id: Optional[str] = None):
    q = {}
    if property_id:
        q["property_id"] = property_id
    docs = get_documents("offer", q)
    for d in docs:
        d["_id"] = str(d["_id"])  # serialize
    return docs


# Admin
@app.get("/admin/settings")
async def read_settings():
    doc = db["adminsettings"].find_one({})
    if not doc:
        # return defaults if not set
        return AdminSettings().model_dump()
    doc["_id"] = str(doc["_id"])  # serialize
    return doc


class SettingsUpdate(BaseModel):
    primary_color: Optional[str] = None
    accent_color: Optional[str] = None
    hero_heading: Optional[str] = None
    hero_subheading: Optional[str] = None
    announcement: Optional[str] = None


@app.put("/admin/settings")
async def update_settings(payload: SettingsUpdate):
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_data:
        return await read_settings()
    db["adminsettings"].update_one({}, {"$set": update_data}, upsert=True)
    return await read_settings()


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            response["connection_status"] = "Connected"
            collections = db.list_collection_names()
            response["collections"] = collections[:10]
            response["database"] = "✅ Connected & Working"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
