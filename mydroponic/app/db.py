from databases import Database
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://myuser:mypassword@mydroponic-db:5432/mydroponic")
database = Database(DATABASE_URL)
