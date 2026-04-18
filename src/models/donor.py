from sqlalchemy import DECIMAL, TIMESTAMP, Boolean, Column, Integer, String, ForeignKey, DateTime, Text, func, Date
from sqlalchemy.orm import relationship
from src.db.base import Base

class Unit(Base):
    __tablename__ = "donor_food_unit"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)

class DeliveryPreference(Base):
    __tablename__ = "donor_food_delivery_preferences"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)

class DonorCategory(Base):
    __tablename__ = "donor_categories"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(String(50), unique=True, nullable=False)
    category_type = Column(String(100), nullable=False)
    backgroundColor = Column(String(50), nullable=True)
    icon = Column(String(255), nullable=True)

class FoodDonation(Base):
    __tablename__ = "food_donations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("donor_categories.id"), nullable=False)

    donation_title = Column(String(255), nullable=False)

    delivery_preference_id = Column(Integer, ForeignKey("donor_food_delivery_preferences.id"))
    preferred_date = Column(Date)

    verification_document_id = Column(Integer, ForeignKey("attachments.id"))

    notes = Column(Text)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class FoodDonationDetail(Base):
    __tablename__ = "donor_food_donation_details"

    id = Column(Integer, primary_key=True, index=True)
    food_donation_id = Column(Integer, ForeignKey("food_donations.id", ondelete="CASCADE"))
    items = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_id = Column(Integer, ForeignKey("donor_food_unit.id"), nullable=False)

# Clothes donation models would be similar to the above structure, with appropriate changes to fields and relationships.

class DonorClothesCategory(Base):
    __tablename__ = "donor_cloth_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

class DonorClothesSize(Base):
    __tablename__ = "donor_cloth_sizes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

class DonorClothesCondition(Base):
    __tablename__ = "donor_cloth_conditions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

class ClothesDonation(Base):
    __tablename__ = "clothes_donations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    category_id = Column(Integer, ForeignKey("donor_categories.id"), nullable=False)
    
    description = Column(Text, nullable=False)

    pickup_type_id = Column(Integer, ForeignKey("donor_food_delivery_preferences.id", ondelete="SET NULL"), nullable=True)
    available_date = Column(Date, nullable=True)

    verification_image_id = Column(Integer, ForeignKey("attachments.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    details = relationship("ClothesDonationDetail", back_populates="donation", cascade="all, delete")

class ClothesDonationDetail(Base):
    __tablename__ = "donor_clothes_donation_details"

    id = Column(Integer, primary_key=True, autoincrement=True)

    clothes_donation_id = Column(Integer, ForeignKey("clothes_donations.id", ondelete="CASCADE"))

    category_id = Column(Integer, ForeignKey("donor_cloth_categories.id"))
    size_id = Column(Integer, ForeignKey("donor_cloth_sizes.id"))
    condition_id = Column(Integer, ForeignKey("donor_cloth_conditions.id"))

    quantity = Column(Integer, nullable=False)

    donation = relationship("ClothesDonation", back_populates="details")

# medical equipment donation models would be similar to the above structure, with appropriate changes to fields and relationships.

class MedicalDonationCategory(Base):
    __tablename__ = "medical_donation_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255))
    icon = Column(String(100))
    size = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

class DonorStemcellDonation(Base):
    __tablename__ = "donor_stemcell_donations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False)

class DonorTissueDonation(Base):
    __tablename__ = "donor_tissue_donations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False)

class DonorOrganDonation(Base):
    __tablename__ = "donor_organ_donations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False)

class DonorConsentType(Base):
    __tablename__ = "donor_consent_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False)

class DonorAvailabilityType(Base):
    __tablename__ = "donor_availability_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False)

class MedicalDonation(Base):
    __tablename__ = "medical_donations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("donor_categories.id"))
    medical_donation_category_id = Column(Integer, ForeignKey("medical_donation_categories.id"))
    full_name = Column(String(150), nullable=False)
    age_group = Column(String(150), nullable=False)
    gender_id = Column(Integer, ForeignKey("gender.id"), nullable=False)
    contact_number = Column(String(20), nullable=False)
    blood_group_id = Column(Integer, ForeignKey("blood_groups.id"))
    milk_volume = Column(Integer)
    baby_age_months = Column(Integer)
    supply_type = Column(String(150))
    quantity = Column(Integer)
    weight_kg = Column(DECIMAL(5,2))
    major_illness = Column(Boolean, default=False)
    recent_surgery = Column(Boolean, default=False)
    last_donation_date = Column(Date)
    currently_on_medication = Column(Boolean, default=False)
    donation_type = Column(String(20), nullable=False)
    availability_type_id = Column(Integer, ForeignKey("donor_availability_types.id"))
    consent_type_id = Column(Integer, ForeignKey("donor_consent_types.id"))
    preferred_hospital = Column(String(200))
    donation_location = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    organs = relationship("MedicalDonationOrganMap", back_populates="donation")
    tissues = relationship("MedicalDonationTissueMap", back_populates="donation")
    stemcells = relationship("MedicalDonationStemcellMap", back_populates="donation")

class MedicalDonationOrganMap(Base):
    __tablename__ = "medical_donation_organ_map"
    medical_donation_id = Column(Integer, ForeignKey("medical_donations.id"), primary_key=True)
    donor_organ_donation_id = Column(Integer, ForeignKey("donor_organ_donations.id"), primary_key=True)
    donation = relationship("MedicalDonation", back_populates="organs")

class MedicalDonationTissueMap(Base):
    __tablename__ = "medical_donation_tissue_map"
    medical_donation_id = Column(Integer, ForeignKey("medical_donations.id"), primary_key=True)
    donor_tissue_donation_id = Column(Integer, ForeignKey("donor_tissue_donations.id"), primary_key=True)
    donation = relationship("MedicalDonation", back_populates="tissues")

class MedicalDonationStemcellMap(Base):
    __tablename__ = "medical_donation_stemcell_map"
    medical_donation_id = Column(Integer, ForeignKey("medical_donations.id"), primary_key=True)
    donor_stemcell_donation_id = Column(Integer, ForeignKey("donor_stemcell_donations.id"), primary_key=True)
    donation = relationship("MedicalDonation", back_populates="stemcells")