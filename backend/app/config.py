import os

# Basic settings for the application.
# In a real deployment these values should come from environment variables,
# not from plain text in the code.

SECRET_KEY = os.environ.get("LIFEFLOW_SECRET_KEY", "change_this_secret_key_before_deployment")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

DATABASE_URL = os.environ.get("LIFEFLOW_DATABASE_URL", "sqlite:///./lifeflow.db")
