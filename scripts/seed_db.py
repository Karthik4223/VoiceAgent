import asyncio
from datetime import time
from backend.app.models.database import AsyncSessionLocal, Doctor, Availability, init_db

async def seed():
    await init_db()
    async with AsyncSessionLocal() as session:
        # Check if already seeded
        from sqlalchemy.future import select
        result = await session.execute(select(Doctor))
        if result.scalars().first():
            print("Database already seeded.")
            return

        doctors = [
            Doctor(name="Dr. Smith", specialization="Cardiologist", department="Cardiology"),
            Doctor(name="Dr. Sharma", specialization="Dermatologist", department="Dermatology"),
            Doctor(name="Dr. Patel", specialization="General Physician", department="General Medicine"),
        ]
        session.add_all(doctors)
        await session.commit()
        
        # Add availability for all doctors Mon-Fri 9 AM to 5 PM
        for doc in doctors:
            for day in range(5): # Mon-Fri
                avail = Availability(
                    doctor_id=doc.id,
                    day_of_week=day,
                    start_time=time(9, 0),
                    end_time=time(17, 0)
                )
                session.add(avail)
        await session.commit()
        print("Database seeded successfully.")

if __name__ == "__main__":
    asyncio.run(seed())
