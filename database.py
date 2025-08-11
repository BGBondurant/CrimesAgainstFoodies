import os
import csv
from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError
from datetime import date

# Get the absolute path of the directory containing this file
basedir = os.path.abspath(os.path.dirname(__file__))
# Create a full path for the database file
db_path = os.path.join(basedir, 'crimes.db')

# Define the database connection URL
DATABASE_URL = f'sqlite:///{db_path}'

# --- SQLAlchemy Setup ---
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- SQLAlchemy Models ---
class DailyImage(Base):
    __tablename__ = 'daily_images'
    id = Column(Integer, primary_key=True)
    generation_date = Column(Date, unique=True, nullable=False)
    food_combination = Column(String(200), nullable=False)
    public_url = Column(String(255), nullable=False)

class Preparation(Base):
    __tablename__ = 'preparations'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

class Food(Base):
    __tablename__ = 'foods'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

class Suggestion(Base):
    __tablename__ = 'suggestions'
    id = Column(Integer, primary_key=True)
    item = Column(String, nullable=False)
    status = Column(String, nullable=False, default='pending')
    date = Column(String, nullable=False) # Storing date as string as in original schema
    type = Column(String, nullable=False, default='food')

    def __repr__(self):
        return f"<Suggestion(id={self.id}, item='{self.item}', status='{self.status}')>"

def get_db():
    """
    Dependency to get a DB session. This will be used in app.py.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initializes the database, creates tables, and populates them with
    initial data from a CSV file.
    """
    # In a real-world scenario, you'd use migrations (e.g., with Alembic)
    # but for this project, we'll keep it simple.
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")

    db = SessionLocal()
    try:
        # --- Add initial starter data from PF.csv ---
        # Check if data already exists to prevent re-populating
        if db.query(Preparation).first() is None and db.query(Food).first() is None:
            print("Populating database with initial data from PF.csv...")
            with open('PF.csv', 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header

                preparations_to_add = []
                foods_to_add = []

                for row in reader:
                    if row[0]:
                        preparations_to_add.append(Preparation(name=row[0]))
                    if row[1]:
                        foods_to_add.append(Food(name=row[1]))

            db.bulk_save_objects(preparations_to_add)
            db.bulk_save_objects(foods_to_add)
            db.commit()
            print("Database populated with starter data.")
        else:
            print("Database already contains data. Skipping population.")
    except Exception as e:
        db.rollback()
        print(f"An error occurred during DB initialization: {e}")
    finally:
        db.close()

if __name__ == '__main__':
    print("Initializing database...")
    # The user might run this script directly.
    # We should handle the case where the old DB exists.
    # For simplicity, we are not deleting the old db file,
    # create_all won't recreate existing tables.
    init_db()
    print("Database initialization complete.")