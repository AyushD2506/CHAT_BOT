import asyncio
from database import init_db, AsyncSessionLocal
from models import User
from auth_utils import get_password_hash

async def create_demo_users():
    """Create demo admin and user accounts for testing"""
    await init_db()
    
    async with AsyncSessionLocal() as db:
        # Check if users already exist
        from sqlalchemy import select
        existing_admin = await db.execute(select(User).where(User.username == "admin"))
        if existing_admin.scalar_one_or_none():
            print("Demo users already exist!")
            return
        
        # Create admin user
        admin = User(
            username="admin",
            email="admin@example.com",
            password_hash=get_password_hash("admin123"),
            is_admin=True
        )
        db.add(admin)
        
        # Create regular user
        user = User(
            username="user",
            email="user@example.com",
            password_hash=get_password_hash("user123"),
            is_admin=False
        )
        db.add(user)
        
        await db.commit()
        print("Demo users created successfully!")
        print("=================================")
        print("Admin credentials:")
        print("Username: admin")
        print("Password: admin123")
        print()
        print("User credentials:")
        print("Username: user")
        print("Password: user123")
        print("=================================")

if __name__ == "__main__":
    asyncio.run(create_demo_users())