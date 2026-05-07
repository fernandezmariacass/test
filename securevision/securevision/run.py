"""
run.py — Application entry point
Usage:
  Development : python run.py
  Production  : gunicorn "run:create_app('production')" -w 4 -b 0.0.0.0:8000
"""

import os
from app import create_app

app = create_app(os.environ.get("FLASK_ENV", "development"))

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=(os.environ.get("FLASK_ENV", "development") == "development"),
    )
