from dotenv import load_dotenv
import os

load_dotenv()

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")

settings = {
    "mongodb_uri": MONGODB_URI
}