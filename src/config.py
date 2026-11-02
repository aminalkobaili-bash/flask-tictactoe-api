from datetime import timedelta
import os

from dotenv import load_dotenv

# Values come from the environment; a .env file next to the project root is loaded if present.
# See .env.example. Both settings are required: the app refuses to start without them.
load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
