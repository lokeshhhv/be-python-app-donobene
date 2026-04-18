from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List, Union

# Common Base
class NameBase(BaseModel):
    name: str


# Food Type
class FoodTypeCreate(NameBase):
    pass

class FoodTypeResponse(NameBase):
    id: int

    class Config:
        from_attributes = True


# Meal Type
class FoodMealTypeResponse(NameBase):
    id: int

    class Config:
        from_attributes = True


# Time Slot
class FoodTimeSlotResponse(NameBase):
    id: int

    class Config:
        from_attributes = True


# Urgency
class FoodUrgencyLevelResponse(NameBase):
    id: int

    class Config:
        from_attributes = True


# Delivery
class DeliveryRequiredResponse(NameBase):
    id: int

    class Config:
        from_attributes = True


# AGE GROUP
class FoodAgeGroupResponse(NameBase):
    id: int

    class Config:
        from_attributes = True


# SPECIAL NEEDS
class FoodSpecialNeedResponse(NameBase):
    id: int

    class Config:
        from_attributes = True


# MEAL FREQUENCY
class FoodMealFrequencyResponse(NameBase):
    id: int

    class Config:
        from_attributes = True


# DURATION
class FoodDurationResponse(NameBase):
    id: int

    class Config:
        from_attributes = True


# 🔹 GROCERY UNIT
class GroceryUnitOptionResponse(NameBase):
    id: int

    class Config:
        from_attributes = True


# 🔹 PRIORITY
class GroceryPriorityLevelResponse(NameBase):
    id: int

    class Config:
        from_attributes = True


# 🔹 ITEM MASTER
class GroceryItemMasterResponse(NameBase):
    id: int

    class Config:
        from_attributes = True

# 🔹 Base
class FoodRequestCategoryBase(BaseModel):
    food_type: str
    food_type_description: str

class FoodRequestBase(BaseModel):
    food_type: str
    food_type_description: str
    size: Optional[str] = None
    icon: Optional[str] = None
    value: Optional[str] = None


# 🔹 Create
class FoodRequestCategoryCreate(FoodRequestCategoryBase):
    pass


# 🔹 Response
class FoodRequestCategoryResponse(FoodRequestBase):
    id: int
    size: Union[str, int, None] = None

    class Config:
        from_attributes = True


# cooked food
class CookedFoodBase(BaseModel):
    user_id: Optional[int] = None
    food_request_category_id: int
    status_id: Optional[int] = None
    urgency_id: Optional[int] = None
    request_title: str
    request_description: Optional[str] = None
    food_type_id: int
    meal_type_id: int
    number_of_people: int
    plates_required: int
    required_date: date
    time_slot_id: int
    urgency_level_id: int
    address: str
    landmark: Optional[str] = None
    delivery_required: bool = False
    reject_reason: Optional[str] = None

class CookedFoodCreate(CookedFoodBase):
    pass

class CookedFoodUpdate(CookedFoodBase):
    pass

class CookedFoodResponse(CookedFoodBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FoodDailyMealRequestPayload(BaseModel):
    user_id: int
    food_request_category_id: int

    status_id: Optional[int] = None
    urgency_id: Optional[int] = None

    request_title: str
    request_description: Optional[str] = None

    number_of_people: int

    age_group_id: Optional[int] = None
    special_need_id: Optional[int] = None

    meal_type_id: int

    frequency_id: int
    duration_id: int

    custom_days: Optional[str] = None
    custom_date_range: Optional[str] = None

    time_slot_id: int

    address: str
    landmark: Optional[str] = None

    delivery_required: bool


class GroceryItemPayload(BaseModel):
    item_master_id: Optional[int] = None
    custom_item_name: Optional[str] = None

    quantity: float

    unit_id: int
    priority_id: int


class GroceryRequestPayload(BaseModel):
    user_id: int
    food_request_category_id: int

    status_id: Optional[int] = None
    urgency_id: Optional[int] = None

    request_title: str
    request_description: Optional[str] = None

    frequency_id: int

    address: str
    landmark: Optional[str] = None

    delivery_required: bool

    items: List[GroceryItemPayload] = Field(default_factory=list)