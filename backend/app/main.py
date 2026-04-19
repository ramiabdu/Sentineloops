"""SentinelOps backend entrypoint.

Day 1 intentionally provides a lightweight executable module so the repository
has a credible starting point before the full FastAPI app lands on Day 2.
"""


def app_metadata() -> dict:
    return {
        "name": "SentinelOps",
        "stage": "day-1-foundation",
        "status": "scaffolded",
    }


if __name__ == "__main__":
    print(app_metadata())
