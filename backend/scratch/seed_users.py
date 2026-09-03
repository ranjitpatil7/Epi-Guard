import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.models.users import User, UserRole, UserStatus
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

async def seed_users():
    async with AsyncSessionLocal() as db:
        try:
            # Check if users already exist
            # Create users
            users_data = [
                {
                    "username": "admin",
                    "email": "admin@jalrakshak.gov.in",
                    "hashed_password": get_password_hash("admin123"),
                    "full_name": "System Administrator",
                    "role": UserRole.ADMINISTRATOR,
                    "region_id": None
                },
                {
                    "username": "dr.sharma",
                    "email": "sharma@jalrakshak.gov.in",
                    "hashed_password": get_password_hash("epi123"),
                    "full_name": "Dr. Priya Sharma",
                    "role": UserRole.EPIDEMIOLOGIST,
                    "region_id": None
                },
                {
                    "username": "collector.das",
                    "email": "das@jalrakshak.gov.in",
                    "hashed_password": get_password_hash("gov123"),
                    "full_name": "Shri Rajesh Das, IAS",
                    "role": UserRole.GOVERNMENT_OFFICIAL,
                    "region_id": 2 # Assam Region in our DB usually
                },
                {
                    "username": "officer.kumar",
                    "email": "kumar@jalrakshak.gov.in",
                    "hashed_password": get_password_hash("field123"),
                    "full_name": "Amit Kumar",
                    "role": UserRole.FIELD_OFFICER,
                    "region_id": 2 # Assam
                }
            ]
            
            for user_data in users_data:
                db.add(User(**user_data))
                
            await db.commit()
            print("Users seeded successfully!")
        except Exception as e:
            print(f"Error seeding users: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(seed_users())
