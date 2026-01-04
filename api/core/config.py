from dotenv import load_dotenv
import os

load_dotenv()

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

settings = {
    "mongodb_uri": MONGODB_URI,
    "allowed_hosts": ALLOWED_HOSTS
}