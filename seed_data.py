import sys
import random
import string
from datetime import datetime, timedelta, timezone

import os
from dotenv import load_dotenv

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.models import DbModel, UserModel, RideModel, ParticipationModel



load_dotenv()

def seed(engine):
    with Session(engine) as session:
        print("🌱 Running default seed...")

        # Fixed user Vadim
        vadim = session.query(UserModel).filter_by(username="vadim").first()
        if not vadim:
            vadim = UserModel(username="vadim", password="123456")
            session.add(vadim)
            session.flush()
            print("👤 Created fixed user: vadim / 123456")
        else:
            print("✔ Fixed user 'vadim' already exists")

        # One simple ride
        ride = session.query(RideModel).filter_by(code="ABC123").first()
        if not ride:
            ride = RideModel(
                code="ABC123",
                title="Demo Ride",
                description="Automatically generated demo ride",
                start_time=datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc),
                created_by_user_id=vadim.id,
            )
            session.add(ride)
            session.flush()
            print("🚴 Created demo ride: ABC123")
        else:
            print("✔ Demo ride ABC123 already exists")

        # One participation
        part = (
            session.query(ParticipationModel)
            .filter_by(user_id=vadim.id, ride_id=ride.id)
            .first()
        )
        if not part:
            part = ParticipationModel(
                user_id=vadim.id,
                ride_id=ride.id,
                latitude=48.1351,
                longitude=11.5820,
                updated_at=datetime.now(timezone.utc),
            )
            session.add(part)
            print("📍 Created demo participation")
        else:
            print("✔ Demo participation already exists")

        session.commit()
        print("✅ Default seed completed!")




# ------------------------------
# Helpers
# ------------------------------
def random_username():
    return "user_" + "".join(random.choices(string.ascii_lowercase, k=6))


def random_password():
    return "".join(random.choices(string.ascii_letters + string.digits, k=10))


def random_ride_code():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def random_datetime():
    base = datetime(2025, 1, 1, tzinfo=timezone.utc)
    delta = timedelta(days=random.randint(0, 365), hours=random.randint(0, 23))
    return base + delta


def random_coordinates():
    # Munich region (~48.13, 11.58)
    lat = 48.0 + random.random() * 1.2
    lon = 11.0 + random.random() * 1.2
    return lat, lon


# ------------------------------
# Reset database
# ------------------------------
def reset_db(engine):
    print("⚠️ Dropping all tables...")
    DbModel.metadata.drop_all(engine)
    print("📦 Creating tables...")
    DbModel.metadata.create_all(engine)
    
    # Reset sequences (PostgreSQL only)
    if engine.dialect.name == 'postgresql':
        print("🔄 Resetting sequences...")
        with Session(engine) as session:
            session.execute(text("ALTER SEQUENCE users_id_seq RESTART WITH 1"))
            session.execute(text("ALTER SEQUENCE rides_id_seq RESTART WITH 1"))
            session.execute(text("ALTER SEQUENCE participations_id_seq RESTART WITH 1"))
            session.commit()
        print("✅ Sequences reset.")
    
    print("✅ Database reset complete.")


# ------------------------------
# Seed function
# ------------------------------
def seed_massive(engine, num_users=10, num_rides=20, num_participations=50):

    with Session(engine) as session:
        print(f"🚀 Seeding {num_users} users, {num_rides} rides, {num_participations} participations...")

        users = []
        rides = []

        # ---------------- FIXED USER ----------------
        vadim = session.query(UserModel).filter_by(username="vadim").first()
        if not vadim:
            vadim = UserModel(username="vadim", password="123456")
            session.add(vadim)
            session.flush()
            print("👤 Created user: vadim (fixed user)")
        else:
            print("✔ User 'vadim' already exists")

        users.append(vadim)

        # ---------------- USERS ----------------
        for _ in range(num_users):
            username = random_username()
            user = UserModel(username=username, password=random_password())
            session.add(user)
            session.flush()
            users.append(user)
        print(f"👤 Created {len(users)} users")

        # ---------------- RIDES ----------------
        created_pairs = set()
        for _ in range(num_rides):
            creator = random.choice(users)
            ride = RideModel(
                code=random_ride_code(),
                title=f"Ride {random.randint(1000, 9999)}",
                description="Auto-generated ride",
                start_time=random_datetime(),
                created_by_user_id=creator.id,
            )
            session.add(ride)
            session.flush()
            rides.append(ride)

            # Auto-add creator as participant
            creator_part = ParticipationModel(
                user_id=creator.id,
                ride_id=ride.id,
                latitude=48.0 + random.random(),
                longitude=11.0 + random.random(),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(creator_part)
            session.flush()
            created_pairs.add((creator.id, ride.id))
        print(f"🚴 Created {len(rides)} rides")

        # ------------- PARTICIPATIONS ----------
        # created_pairs is already initialized and populated with creators
        attempts = 0
        max_attempts = num_participations * 10
        
        while len(created_pairs) < num_participations and attempts < max_attempts:
            attempts += 1
            user = random.choice(users)
            ride = random.choice(rides)
            
            pair = (user.id, ride.id)
            if pair in created_pairs:
                continue
            
            created_pairs.add(pair)
            lat, lon = random_coordinates()

            participation = ParticipationModel(
                user_id=user.id,
                ride_id=ride.id,
                latitude=lat,
                longitude=lon,
                updated_at=random_datetime(),
            )
            session.add(participation)

        session.commit()
        print(f"📍 Created {len(created_pairs)} participations")
        print("🎉 Seeding completed!")


# ------------------------------
# CLI handling
# ------------------------------
if __name__ == "__main__":
    database_url = os.getenv("DATABASE_URL", "sqlite:///ride.db")
    engine = create_engine(database_url)
    print(f"(CONNECTED) Using database: {database_url.split('@')[-1] if '@' in database_url else database_url}")


    if "--reset" in sys.argv:
        reset_db(engine)
        sys.exit(0)

    if "--massive" in sys.argv:
        num_users = 10
        num_rides = 20
        num_participations = 50

        for arg in sys.argv:
            if arg.startswith("--users="):
                num_users = int(arg.split("=")[1])
            if arg.startswith("--rides="):
                num_rides = int(arg.split("=")[1])
            if arg.startswith("--participations="):
                num_participations = int(arg.split("=")[1])

        seed_massive(engine, num_users, num_rides, num_participations)
        sys.exit(0)

    # ✅ DEFAULT SEED (no import!)
    seed(engine)

