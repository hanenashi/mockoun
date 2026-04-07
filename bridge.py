import os
from dotenv import load_dotenv

# Load the environment variables from .env
load_dotenv()

# Grab the user and club (with fallbacks just in case)
user = os.getenv("OKOUN_USER", "default_user")
club = os.getenv("OKOUN_CLUB", "nepotrebny_pokus")

# Write them into a JavaScript module
with open("env_config.js", "w", encoding="utf-8") as f:
    f.write(f"export const ENV_USER = '{user}';\n")
    f.write(f"export const ENV_CLUB = '{club}';\n")

print(f"Bridge complete: env_config.js generated for user '{user}' and club '{club}'.")