# TEMPORARY until real auth lands in week 6 (see ROADMAP.md).
# get_current_restaurant_id() is the ONLY place "whose data is this request
# for" gets decided. Every router depends on it instead of trusting a
# restaurant_id from the request body or URL. When real auth arrives, only
# this function changes (JWT -> restaurant_id) -- no router changes.
DEV_RESTAURANT_ID = 1


def get_current_restaurant_id() -> int:
    return DEV_RESTAURANT_ID
