"""Script to seed the database with sample restaurants and dishes."""

from sqlalchemy.orm import Session

from .database import Base, engine, SessionLocal
from .models import Restaurant, Dish



def seed() -> None:
    """Populate the database with some example restaurants and dishes."""
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        # Only seed if there are no restaurants yet
        if db.query(Restaurant).count() == 0:
            # Create sample restaurants
            r1 = Restaurant(name="Cafe Roma", address="123 Main St, New York", rating=4.5)
            r2 = Restaurant(name="Sushi House", address="456 Elm St, New York", rating=4.2)
            r3 = Restaurant(name="Taco Town", address="789 Oak St, New York", rating=4.0)
            db.add_all([r1, r2, r3])
            db.flush()  # ensure IDs are generated
            # Create sample dishes
            dishes = [
                Dish(name="Margherita Pizza", description="Classic pizza with tomatoes and mozzarella", rating=4.6, restaurant_id=r1.id),
                Dish(name="Spaghetti Carbonara", description="Spaghetti with eggs, cheese and pancetta", rating=4.3, restaurant_id=r1.id),
                Dish(name="California Roll", description="Crab, avocado and cucumber", rating=4.1, restaurant_id=r2.id),
                Dish(name="Dragon Roll", description="Eel and cucumber inside, avocado on top", rating=4.4, restaurant_id=r2.id),
                Dish(name="Beef Taco", description="Spiced beef with lettuce and cheese", rating=4.0, restaurant_id=r3.id),
                Dish(name="Chicken Burrito", description="Grilled chicken with rice and beans", rating=4.2, restaurant_id=r3.id),
            ]
            db.add_all(dishes)
            db.commit()
            print("Database seeded with sample data.")
        else:
            print("Database already contains data; skipping seeding.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
