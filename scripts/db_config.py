from pathlib import Path
import os
import psycopg2
from dotenv import load_dotenv
from sqlalchemy import create_engine
from urllib.parse import quote_plus

load_dotenv(Path(__file__).parent.parent / ".env")


def get_connection():
    """Raw psycopg2 connection — use for INSERT, UPDATE, TRUNCATE operations."""
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    return conn




# --- TEMPORARY DEBUG - remove after fix ---
print("USER    :", os.getenv("DB_USER"))
print("PASSWORD:", os.getenv("DB_PASSWORD"))
print("HOST    :", os.getenv("DB_HOST"))
print("PORT    :", os.getenv("DB_PORT"))
print("DBNAME  :", os.getenv("DB_NAME"))
# ------------------------------------------


def get_engine():
    user     = os.getenv("DB_USER")
    password = quote_plus(os.getenv("DB_PASSWORD"))  # ← encode special chars
    host     = os.getenv("DB_HOST")
    port     = os.getenv("DB_PORT")
    dbname   = os.getenv("DB_NAME")

    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
    return create_engine(url, connect_args={"host": host, "port": int(port)})

