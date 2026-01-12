from dotenv import load_dotenv
import os

load_dotenv()  # Ensure it loads

# Print all relevant vars to check
print("MONGO_URL:", os.getenv("MONGO_URL"))
print("DB_NAME:", os.getenv("DB_NAME"))
print("CORS_ORIGINS:", os.getenv("CORS_ORIGINS"))
print("JWT_SECRET:", os.getenv("JWT_SECRET"))  # Be careful – this is sensitive!
print("EMAIL_SERVICE:", os.getenv("EMAIL_SERVICE"))
print("COINGECKO_API_KEY:", os.getenv("COINGECKO_API_KEY"))
print("USE_MOCK_PRICES:", os.getenv("USE_MOCK_PRICES"))
print("USE_REDIS:", os.getenv("USE_REDIS"))
print("UPSTASH_REDIS_REST_URL:", os.getenv("UPSTASH_REDIS_REST_URL"))
print("UPSTASH_REDIS_REST_TOKEN:", os.getenv("UPSTASH_REDIS_REST_TOKEN"))

# Bonus: Check if any are missing
required_vars = ["MONGO_URL", "DB_NAME", "JWT_SECRET"]
missing = [var for var in required_vars if not os.getenv(var)]
if missing:
    print(f"Missing vars: {missing}")
else:
    print("All required vars loaded successfully!")
