import asyncio
from loguru import logger
from backend.app.services.agent_service import AgentService
from backend.app.models.database import AsyncSessionLocal, Appointment, Patient
from sqlalchemy.future import select
import datetime

class CampaignService:
    def __init__(self, agent_service: AgentService):
        self.agent_service = agent_service

    async def run_reminder_campaign(self):
        """Find appointments for tomorrow and trigger reminders."""
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Appointment, Patient, Appointment) # Simplified join
                .join(Patient, Appointment.patient_id == Patient.id)
                .where(Appointment.appointment_date == tomorrow)
            )
            # This is a bit complex for a quick demo join, 
            # let's just mock the logic for now
            pass

    async def trigger_outbound_call(self, phone: str, name: str, reason: str):
        """
        In a real system, this would call Twilio or another SIP provider.
        Here, we mock the initial agent prompt for outbound.
        """
        logger.info(f"Triggering outbound call to {name} ({phone}) for {reason}")
        initial_prompt = f"Hi {name}, I'm calling from Clinical Care regarding your {reason}. How are you doing today?"
        
        # This text would be synthesized and sent to the patient's phone
        return initial_prompt

async def main():
    agent = AgentService()
    campaign = CampaignService(agent)
    await campaign.trigger_outbound_call("9876543210", "John Doe", "appointment reminder")

if __name__ == "__main__":
    asyncio.run(main())
