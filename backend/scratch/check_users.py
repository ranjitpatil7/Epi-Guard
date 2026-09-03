import asyncio
from app.db.session import AsyncSessionLocal
from app.models.users import User
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as db:
        users = (await db.execute(select(User))).scalars().all()
        print(f"Found {len(users)} users:")
        for u in users:
            print(f"- {u.username} ({u.role})")

if __name__ == "__main__":
    asyncio.run(run())
