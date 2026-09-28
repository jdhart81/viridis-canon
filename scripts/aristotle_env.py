"""Read Aristotle credentials exclusively from the process environment."""

import os


def get_api_key() -> str:
    try:
        key = os.environ["ARISTOTLE_API_KEY"]
    except KeyError:
        raise SystemExit("ERROR: ARISTOTLE_API_KEY must be set in the environment.") from None
    if not key.strip():
        raise SystemExit("ERROR: ARISTOTLE_API_KEY must not be empty.")
    return key.strip()
