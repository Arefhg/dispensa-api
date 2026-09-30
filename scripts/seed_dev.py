"""Create the dev restaurant used by app.deps.DEV_RESTAURANT_ID.

Safe to run more than once: if it already exists, does nothing.
Run: .venv/Scripts/python.exe scripts/seed_dev.py
"""

from app.db import SessionLocal
from app.deps import DEV_RESTAURANT_ID
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
        if restaurant.id != DEV_RESTAURANT_ID:
            print(
                f"WARNING: app.deps.DEV_RESTAURANT_ID is {DEV_RESTAURANT_ID}, "
                f"but the created restaurant has id={restaurant.id}. "
                "Update DEV_RESTAURANT_ID to match, or start from an empty database."
            )


if __name__ == "__main__":
    main()
