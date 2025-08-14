"""Main FastAPI application for the menu scan backend."""

import os
import time
import uuid
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import auth, models, schemas
from .database import Base, engine, get_db
from .dependencies import get_current_user


# Create database tables on startup.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Menu Scan Backend", openapi_url="/openapi.json")

# Configure CORS. Allow all origins by default or use comma-separated list in env.
origins_env = os.getenv("CORS_ALLOW_ORIGINS", "*")
origins = [o.strip() for o in origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for scan jobs. Keys are job IDs; values contain creation time and results.
jobs: dict[str, dict[str, object]] = {}


@app.post("/api/auth/signup", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
def signup(user_create: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user and return an access token."""
    existing_user = db.query(models.User).filter(models.User.email == user_create.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    hashed_password = auth.get_password_hash(user_create.password)
    user = models.User(email=user_create.email, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    # Issue JWT token with user id as subject
    access_token = auth.create_access_token({"sub": str(user.id)})
    return schemas.Token(access_token=access_token)


@app.post("/api/auth/login", response_model=schemas.Token)
def login(user_create: schemas.UserCreate, db: Session = Depends(get_db)):
    """Authenticate a user and issue a JWT token."""
    user = db.query(models.User).filter(models.User.email == user_create.email).first()
    if user is None or not auth.verify_password(user_create.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password")
    access_token = auth.create_access_token({"sub": str(user.id)})
    return schemas.Token(access_token=access_token)


@app.get("/api/me", response_model=schemas.UserRead)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    """Return the current authenticated user."""
    return current_user


@app.get("/api/restaurants", response_model=List[schemas.RestaurantSchema])
def list_restaurants(db: Session = Depends(get_db)):
    """Return a list of all restaurants."""
    restaurants = db.query(models.Restaurant).order_by(models.Restaurant.name).all()
    return restaurants


@app.get("/api/dishes", response_model=List[schemas.DishSchema])
def list_dishes(
    restaurant_id: Optional[int] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Return a list of dishes filtered by restaurant or search query."""
    query = db.query(models.Dish)
    if restaurant_id is not None:
        query = query.filter(models.Dish.restaurant_id == restaurant_id)
    if q:
        like_pattern = f"%{q.lower()}%"
        query = query.filter(models.Dish.name.ilike(like_pattern))
    return query.order_by(models.Dish.name).all()


@app.post("/api/favorites", response_model=schemas.FavoriteSchema)
def add_favorite(
    dish_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a dish as a favorite for the current user."""
    dish = db.query(models.Dish).filter(models.Dish.id == dish_id).first()
    if not dish:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dish not found")
    # Check if already favorited
    existing = db.query(models.Favorite).filter(
        models.Favorite.user_id == current_user.id, models.Favorite.dish_id == dish_id
    ).first()
    if existing:
        return existing
    favorite = models.Favorite(user_id=current_user.id, dish_id=dish_id)
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite


@app.get("/api/favorites", response_model=List[schemas.FavoriteSchema])
def list_favorites(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return all favorite dishes for the current user."""
    favs = (
        db.query(models.Favorite)
        .join(models.Dish)
        .filter(models.Favorite.user_id == current_user.id)
        .order_by(models.Favorite.created_at.desc())
        .all()
    )
    return favs


@app.post("/api/scan", response_model=schemas.ScanResponse)
def scan_menu(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Accept an image of a menu and return a job ID for processing. Results are simulated."""
    # For demonstration purposes, this endpoint does not actually process the image.
    job_id = str(uuid.uuid4())
    # Choose some dishes to return later. Use first three dishes if available.
    dishes = db.query(models.Dish).limit(5).all()
    jobs[job_id] = {"created_at": time.time(), "results": dishes}
    return schemas.ScanResponse(job_id=job_id)


@app.get("/api/scan/{job_id}", response_model=schemas.ScanResult)
def get_scan_result(job_id: str):
    """Check the status of a scan job and return results when complete."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    elapsed = time.time() - job["created_at"]
    if elapsed < 3:
        return schemas.ScanResult(status="processing")
    return schemas.ScanResult(status="completed", results=job["results"])
