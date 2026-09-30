"""Create the dev restaurant for local manual testing.

Safe to run more than once: if it already exists, does nothing.
Run: .venv/Scripts/python.exe scripts/seed_dev.py
Then put the printed id in .env as DEV_RESTAURANT_ID.
"""

from app.db import SessionLocal
from app.models import Restaurant

DEV_RESTAURANT_NAME = "Dev Restaurant"


def main() -> None:
    with SessionLocal() as db:
        existing = db.query(Restaurant).filter_by(name=DEV_RESTAURANT_NAME).first()
        if existing is not None:
            print(f"Dev restaurant already exists: id={existing.id}")
            return

        restaurant = Restaurant(
            name=DEV_RESTAURANT_NAME,
            address="Via Roma 1, Napoli",
            timezone="Europe/Rome",
        )
        db.add(restaurant)
        db.commit()
        db.refresh(restaurant)

        print(f"Created dev restaurant: id={restaurant.id}")
        print(f"Put this in .env: DEV_RESTAURANT_ID={restaurant.id}")


if __name__ == "__main__":
    main()
