from sqlalchemy import Boolean, Boolean, Date, DECIMAL
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, func
from src.db.base import Base

class FoodType(Base):
    __tablename__ = "food_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)


class FoodMealType(Base):
    __tablename__ = "food_meal_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)


class FoodTimeSlot(Base):
    __tablename__ = "food_time_slots"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)


class FoodUrgencyLevel(Base):
    __tablename__ = "food_urgency_levels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)


class DeliveryRequired(Base):
    __tablename__ = "delivery_required"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)

class FoodAgeGroup(Base):
    __tablename__ = "food_age_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True)


class FoodSpecialNeed(Base):
    __tablename__ = "food_special_needs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True)


class FoodMealFrequency(Base):
    __tablename__ = "food_meal_frequencies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True)


class FoodDuration(Base):
    __tablename__ = "food_durations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True)

# 🔹 GROCERY TABLES

class GroceryUnitOption(Base):
    __tablename__ = "grocery_unit_options"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)


class GroceryPriorityLevel(Base):
    __tablename__ = "grocery_priority_levels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)


class GroceryItemMaster(Base):
    __tablename__ = "grocery_item_master"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)

class FoodRequestCategory(Base):
    __tablename__ = "food_request_categories"

    id = Column(Integer, primary_key=True, index=True)
    food_type = Column(String(50), nullable=False)
    food_type_description = Column(String(255), nullable=False)
    icon = Column(String(255), nullable=True)
    size = Column(String(50), nullable=True)
    value = Column(String(50), nullable=True)


class FoodRequestsCookedFood(Base):
    __tablename__ = "food_requests_cooked_food"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    food_request_category_id = Column(Integer, ForeignKey("food_request_categories.id", ondelete="RESTRICT"), nullable=False)

    status_id = Column(Integer, ForeignKey("request_status_master.id", ondelete="SET NULL"), nullable=True)
    urgency_id = Column(Integer, ForeignKey("urgency_levels.id", ondelete="SET NULL"), nullable=True)

    request_title = Column(String(255), nullable=False)
    request_description = Column(Text, nullable=True)

    food_type_id = Column(Integer, ForeignKey("food_types.id", ondelete="RESTRICT"), nullable=False)
    meal_type_id = Column(Integer, ForeignKey("food_meal_types.id", ondelete="RESTRICT"), nullable=False)

    number_of_people = Column(Integer, nullable=False)
    plates_required = Column(Integer, nullable=False)

    required_date = Column(Date, nullable=False)
    time_slot_id = Column(Integer, ForeignKey("food_time_slots.id", ondelete="RESTRICT"), nullable=False)
    urgency_level_id = Column(Integer, ForeignKey("food_urgency_levels.id", ondelete="RESTRICT"), nullable=False)

    address = Column(String(255), nullable=False)
    landmark = Column(String(255), nullable=True)

    delivery_required = Column(Boolean, nullable=False, default=False)
    reject_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(), server_default=func.now())
    updated_at = Column(DateTime(), server_default=func.now(), onupdate=func.now())

class FoodDailyMealRequest(Base):
    __tablename__ = "food_daily_meal_requests"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    food_request_category_id = Column(Integer, ForeignKey("food_request_categories.id"), nullable=False)

    status_id = Column(Integer, ForeignKey("request_status_master.id"))
    urgency_id = Column(Integer, ForeignKey("urgency_levels.id"))

    request_title = Column(String(255), nullable=False)
    request_description = Column(Text)

    number_of_people = Column(Integer, nullable=False)

    age_group_id = Column(Integer, ForeignKey("food_age_groups.id"))
    special_need_id = Column(Integer, ForeignKey("food_special_needs.id"))

    meal_type_id = Column(Integer, ForeignKey("food_meal_types.id"), nullable=False)

    frequency_id = Column(Integer, ForeignKey("food_meal_frequencies.id"), nullable=False)
    duration_id = Column(Integer, ForeignKey("food_durations.id"), nullable=False)

    custom_days = Column(String(100))
    custom_date_range = Column(String(100))

    time_slot_id = Column(Integer, ForeignKey("food_time_slots.id"), nullable=False)

    address = Column(String(255), nullable=False)
    landmark = Column(String(255))

    delivery_required = Column(Boolean, default=False)
    amount_requested = Column(DECIMAL(10, 2))
    created_at = Column(DateTime(), server_default=func.now())
    updated_at = Column(DateTime(), server_default=func.now(), onupdate=func.now())


class GroceryEssentialsRequest(Base):
    __tablename__ = "grocery_essentials_requests"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    food_request_category_id = Column(Integer, ForeignKey("food_request_categories.id"), nullable=False)

    status_id = Column(Integer, ForeignKey("request_status_master.id"))
    urgency_id = Column(Integer, ForeignKey("urgency_levels.id"))

    request_title = Column(String(255), nullable=False)
    request_description = Column(Text)

    frequency_id = Column(Integer, ForeignKey("food_meal_frequencies.id"), nullable=False)

    address = Column(String(255), nullable=False)
    landmark = Column(String(255))

    delivery_required = Column(Boolean, default=False)
    amount_requested = Column(DECIMAL(10, 2))

    created_at = Column(DateTime(), server_default=func.now())
    updated_at = Column(DateTime(), server_default=func.now(), onupdate=func.now())


class GroceryEssentialsItem(Base):
    __tablename__ = "grocery_essentials_items"

    id = Column(Integer, primary_key=True, index=True)

    grocery_essentials_request_id = Column(
        Integer,
        ForeignKey("grocery_essentials_requests.id", ondelete="CASCADE"),
        nullable=False
    )

    item_master_id = Column(Integer, ForeignKey("grocery_item_master.id"))
    custom_item_name = Column(String(255))

    quantity = Column(DECIMAL(10, 2), nullable=False)

    unit_id = Column(Integer, ForeignKey("grocery_unit_options.id"), nullable=False)
    priority_id = Column(Integer, ForeignKey("grocery_priority_levels.id"), nullable=False)

    created_at = Column(DateTime(), server_default=func.now())
    updated_at = Column(DateTime(), server_default=func.now(), onupdate=func.now())