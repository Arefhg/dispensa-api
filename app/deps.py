from app.config import settings

# TEMPORARY until real auth lands in week 6 (see ROADMAP.md).
# get_current_restaurant_id() is the ONLY place "whose data is this request
# for" gets decided. Every router depends on it instead of trusting a
# restaurant_id from the request body or URL. When real auth arrives, only
# this function changes (JWT -> restaurant_id) -- no router changes.


def get_current_restaurant_id() -> int:
    if settings.environment != "development":
        raise RuntimeError(
            "get_current_restaurant_id() is a development-only placeholder "
            f"and must never run with ENVIRONMENT={settings.environment!r}."
        )
    if settings.dev_restaurant_id is None:
        raise RuntimeError(
            "DEV_RESTAURANT_ID is not set. Run scripts/seed_dev.py and put the printed id in .env."
        )
    return settings.dev_restaurant_id
