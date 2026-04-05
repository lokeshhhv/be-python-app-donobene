from http.client import HTTPException

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional

from src.models.medical import BloodGroup
from src.models.medical import MedicalRequestCategory
from src.models.medical import MedicalSupportType
from src.db.session import get_db

from src.models.medical import PatientSupportType
from src.models.medical import HospitalDetails
from src.models.medical import MedicalRequest
from src.models.medical import Patient
from src.schemas import MedicalRequestPayload
from src.schemas.MedicalRequestPayload import MedicalRequestPayload
from src.core.dependencies import get_current_user_id

router = APIRouter(
    prefix="/api/v1/categories",
    tags=["Medical Categories"],
    dependencies=[Depends(get_current_user_id)],
)

@router.get("/medical-categories", response_model=list[dict])
async def get_medical_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MedicalRequestCategory))
    medical_categories = result.scalars().all()
    return [
        {"id": mc.id, "name": mc.name} for mc in medical_categories
    ]

@router.get("/medical-support-types", response_model=list[dict])
async def get_support_types(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MedicalSupportType))
    support_types = result.scalars().all()
    return [
        {"id": st.id, "name": st.name} for st in support_types
    ]

@router.get("/medical-blood-groups", response_model=list[dict])
async def get_blood_groups(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BloodGroup))
    blood_groups = result.scalars().all()
    return [
        {"id": bg.id, "name": bg.name} for bg in blood_groups
    ]


@router.post("/medical-request", response_model=dict)
async def create_medical_request(
    payload: MedicalRequestPayload,
    db: AsyncSession = Depends(get_db)
):
    try:
        new_request = MedicalRequest(
            user_id=payload.user_id,
            category_id=payload.category_id,
            request_title=payload.request_title,
            request_description=payload.request_description,
            status_id=payload.status_id,
            urgency_id=payload.urgency_id
        )
        db.add(new_request)
        await db.flush()

        for p in payload.patients:
            new_patient = Patient(
                medical_request_id=new_request.id,
                patient_name=p.patient_name,
                age=p.age,
                gender_id=p.gender_id,
                medical_condition=p.medical_condition,
                blood_group_id=p.blood_group_id,
                medical_category_id=p.medical_category_id
            )
            db.add(new_patient)
            await db.flush()

            # support types
            for st in p.support_types:
                db.add(
                    PatientSupportType(
                        patient_id=new_patient.id,
                        support_type_id=st.support_type_id
                    )
                )

            # hospital
            hd = p.hospital_details
            db.add(
                HospitalDetails(
                    patient_id=new_patient.id,
                    hospital_name=hd.hospital_name,
                    hospital_address=hd.hospital_address,
                    doctor_name=hd.doctor_name,
                    financial_information=hd.financial_information,
                    amount_paid=hd.amount_paid,
                    amount_requested=hd.amount_requested,
                    funds_needed_by=hd.funds_needed_by,
                    contact_information=hd.contact_information,
                    emergency_contact_name=hd.emergency_contact_name,
                    attachment_id=hd.attachment_id,
                    prescription_id=hd.prescription_id,
                    estimation_id=hd.estimation_id
                )
            )

        await db.commit()

        return {
            "message": "Medical request created successfully",
            "request_id": new_request.id
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/medical-request", response_model=list[dict])
async def get_medical_requests(
    user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(MedicalRequest)

    if user_id:
        query = query.where(MedicalRequest.user_id == user_id)

    result = await db.execute(query)
    requests = result.scalars().all()

    response = []

    for r in requests:
        patients = (await db.execute(
            select(Patient).where(Patient.medical_request_id == r.id)
        )).scalars().all()

        patient_data = []

        for p in patients:
            supports = (await db.execute(
                select(PatientSupportType).where(PatientSupportType.patient_id == p.id)
            )).scalars().all()

            hospital = (await db.execute(
                select(HospitalDetails).where(HospitalDetails.patient_id == p.id)
            )).scalars().first()

            patient_data.append({
                "patient_name": p.patient_name,
                "age": p.age,
                "gender_id": p.gender_id,
                "medical_condition": p.medical_condition,
                "blood_group_id": p.blood_group_id,
                "medical_category_id": p.medical_category_id,
                "support_types": [
                    {"support_type_id": s.support_type_id} for s in supports
                ],
                "hospital_details": {
                    "hospital_name": hospital.hospital_name if hospital else None,
                    "attachment_id": hospital.attachment_id if hospital else None
                }
            })

        response.append({
            "id": r.id,
            "user_id": r.user_id,
            "request_title": r.request_title,
            "patients": patient_data
        })

    return response