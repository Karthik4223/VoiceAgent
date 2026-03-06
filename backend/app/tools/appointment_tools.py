from datetime import datetime, date, time
from sqlalchemy.future import select
from sqlalchemy import and_
from backend.app.models.database import AsyncSessionLocal, Appointment, Doctor, Availability, Patient, AppointmentStatus
from loguru import logger

async def get_doctors():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Doctor))
        doctors = result.scalars().all()
        return [{"id": d.id, "name": d.name, "specialization": d.specialization} for d in doctors]

async def check_availability(doctor_id: int, target_date: str):
    # Parse date
    try:
        dt_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD."}

    day_of_week = dt_obj.weekday()

    async with AsyncSessionLocal() as session:
        # Check doctor general availability for that day
        avail_result = await session.execute(
            select(Availability).where(and_(Availability.doctor_id == doctor_id, Availability.day_of_week == day_of_week))
        )
        avail = avail_result.scalars().first()
        
        if not avail:
            return {"available": False, "message": "Doctor does not work on this day."}

        # Check existing appointments
        appt_result = await session.execute(
            select(Appointment).where(and_(
                Appointment.doctor_id == doctor_id, 
                Appointment.appointment_date == dt_obj,
                Appointment.status == AppointmentStatus.CONFIRMED
            ))
        )
        existing_appts = appt_result.scalars().all()
        booked_times = [a.appointment_time.strftime("%H:%M") for a in existing_appts]

        # Generate slots (simple 30-min slots)
        slots = []
        curr = datetime.combine(date.today(), avail.start_time)
        end = datetime.combine(date.today(), avail.end_time)
        while curr < end:
            t_str = curr.time().strftime("%H:%M")
            if t_str not in booked_times:
                slots.append(t_str)
            import datetime as dt
            curr += dt.timedelta(minutes=30)

        return {"available_slots": slots}

async def book_appointment(phone: str, doctor_id: int, appt_date: str, appt_time: str):
    try:
        dt_obj = datetime.strptime(appt_date, "%Y-%m-%d").date()
        tm_obj = datetime.strptime(appt_time, "%H:%M").time()
    except ValueError:
        return {"error": "Invalid date or time format."}

    async with AsyncSessionLocal() as session:
        # Check if patient exists
        pat_result = await session.execute(select(Patient).where(Patient.phone == phone))
        patient = pat_result.scalars().first()
        if not patient:
            # For simplicity, create patient if not found
            patient = Patient(phone=phone, name="Unknown")
            session.add(patient)
            await session.commit()
            await session.refresh(patient)

        # Check for conflicts again
        conflict_result = await session.execute(
            select(Appointment).where(and_(
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_date == dt_obj,
                Appointment.appointment_time == tm_obj,
                Appointment.status == AppointmentStatus.CONFIRMED
            ))
        )
        if conflict_result.scalars().first():
            return {"error": "This slot is already booked."}

        new_appt = Appointment(
            patient_id=patient.id,
            doctor_id=doctor_id,
            appointment_date=dt_obj,
            appointment_time=tm_obj,
            status=AppointmentStatus.CONFIRMED
        )
        session.add(new_appt)
        await session.commit()
        return {"status": "success", "appointment_id": new_appt.id}

async def cancel_appointment(appointment_id: int):
    async with AsyncSessionLocal() as session:
        appt_result = await session.execute(select(Appointment).where(Appointment.id == appointment_id))
        appt = appt_result.scalars().first()
        if not appt:
            return {"error": "Appointment not found."}
        appt.status = AppointmentStatus.CANCELLED
        await session.commit()
        return {"status": "success"}
