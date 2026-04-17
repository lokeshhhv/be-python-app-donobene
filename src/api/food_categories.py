from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from src.core.dependencies import get_current_user_id

from src.models.food import FoodAgeGroup, FoodDailyMealRequest, FoodDuration, FoodMealFrequency, FoodRequestCategory, FoodRequestsCookedFood, FoodSpecialNeed, FoodType, GroceryEssentialsItem, GroceryEssentialsRequest, GroceryItemMaster, GroceryPriorityLevel, GroceryUnitOption
from src.models.food import FoodMealType
from src.models.food import FoodTimeSlot
from src.models.food import FoodUrgencyLevel
from src.models.food import DeliveryRequired
from src.db.session import get_db
from src.schemas.FoodRequestPayload import CookedFoodCreate, CookedFoodResponse, FoodDailyMealRequestPayload, FoodRequestCategoryResponse, FoodTypeResponse, GroceryItemMasterResponse, GroceryPriorityLevelResponse, GroceryRequestPayload, GroceryUnitOptionResponse
from src.schemas.FoodRequestPayload import FoodMealTypeResponse
from src.schemas.FoodRequestPayload import FoodTimeSlotResponse
from src.schemas.FoodRequestPayload import FoodUrgencyLevelResponse
from src.schemas.FoodRequestPayload import DeliveryRequiredResponse
from src.schemas.FoodRequestPayload import FoodAgeGroupResponse
from src.schemas.FoodRequestPayload import FoodSpecialNeedResponse
from src.schemas.FoodRequestPayload import FoodMealFrequencyResponse
from src.schemas.FoodRequestPayload import FoodDurationResponse

# 🔹 GET APIs
router = APIRouter(
    prefix="/api/v1/food", 
    tags=["Food Categories"], 
    # dependencies=[Depends(get_current_user_id)]
)

@router.get("/food-types", response_model=list[FoodTypeResponse])
async def get_food_types(db: Session = Depends(get_db)):
    result = await db.execute(select(FoodType))
    food_types = result.scalars().all()
    return food_types


@router.get("/meal-types", response_model=list[FoodMealTypeResponse])
async def get_meal_types(db: Session = Depends(get_db)):
    result = await db.execute(select(FoodMealType))
    meal_types = result.scalars().all()
    return meal_types


@router.get("/time-slots", response_model=list[FoodTimeSlotResponse])
async def get_time_slots(db: Session = Depends(get_db)):
    result = await db.execute(select(FoodTimeSlot))
    time_slots = result.scalars().all()
    return time_slots


@router.get("/urgency-levels", response_model=list[FoodUrgencyLevelResponse])
async def get_urgency_levels(db: Session = Depends(get_db)):
    result = await db.execute(select(FoodUrgencyLevel))
    urgency_levels = result.scalars().all()
    return urgency_levels


@router.get("/delivery-required", response_model=list[DeliveryRequiredResponse])
async def get_delivery_required(db: Session = Depends(get_db)):
    result = await db.execute(select(DeliveryRequired))
    delivery_required = result.scalars().all()
    return delivery_required

# 🔹 AGE GROUPS
@router.get("/age-groups", response_model=list[FoodAgeGroupResponse])
async def get_age_groups(db: Session = Depends(get_db)):
    result = await db.execute(select(FoodAgeGroup))
    age_groups = result.scalars().all()
    return age_groups


# 🔹 SPECIAL NEEDS
@router.get("/special-needs", response_model=list[FoodSpecialNeedResponse])
async def get_special_needs(db: Session = Depends(get_db)):
    result = await db.execute(select(FoodSpecialNeed))
    special_needs = result.scalars().all()
    return special_needs


# 🔹 MEAL FREQUENCY
@router.get("/meal-frequencies", response_model=list[FoodMealFrequencyResponse])
async def get_meal_frequencies(db: Session = Depends(get_db)):
    result = await db.execute(select(FoodMealFrequency))
    meal_frequencies = result.scalars().all()
    return meal_frequencies


# 🔹 DURATION
@router.get("/durations", response_model=list[FoodDurationResponse])
async def get_durations(db: Session = Depends(get_db)):
    result = await db.execute(select(FoodDuration))
    durations = result.scalars().all()
    return durations

# 🔹 GROCERY UNIT OPTIONS
@router.get("/grocery-units", response_model=list[GroceryUnitOptionResponse])
async def get_grocery_units(db: Session = Depends(get_db)):
    result = await db.execute(select(GroceryUnitOption))
    grocery_units = result.scalars().all()
    return grocery_units


# 🔹 PRIORITY LEVELS
@router.get("/grocery-priority-levels", response_model=list[GroceryPriorityLevelResponse])
async def get_priority_levels(db: Session = Depends(get_db)):
    result = await db.execute(select(GroceryPriorityLevel))
    priority_levels = result.scalars().all()
    return priority_levels


# 🔹 GROCERY ITEMS
@router.get("/grocery-items", response_model=list[GroceryItemMasterResponse])
async def get_grocery_items(db: Session = Depends(get_db)):
    result = await db.execute(select(GroceryItemMaster))
    grocery_items = result.scalars().all()
    return grocery_items

@router.get("/food-request-categories", response_model=list[FoodRequestCategoryResponse])
async def get_food_request_categories(db: Session = Depends(get_db)):
    result = await db.execute(select(FoodRequestCategory))
    food_request_categories = result.scalars().all()
    return food_request_categories

@router.post("/food-cooked", response_model=list[CookedFoodResponse])
async def create_cooked_food(cooked_food: CookedFoodCreate, db: Session = Depends(get_db)):
    cooked_food_data = cooked_food.dict(exclude={"user_id"})
    new_cooked_food = FoodRequestsCookedFood(user_id=cooked_food.user_id, **cooked_food_data)
    db.add(new_cooked_food)
    await db.commit()
    await db.refresh(new_cooked_food)
    return [new_cooked_food]

# @router.get("/food-cooked", response_model=list[CookedFoodResponse])
# async def get_cooked_foods(user_id: Optional[int] = None, db: Session = Depends(get_db)):
#     query = select(FoodRequestsCookedFood)

#     if user_id:
#         query = query.where(FoodRequestsCookedFood.user_id == user_id)

#     result = await db.execute(query)
#     cooked_foods = result.scalars().all()
#     return cooked_foods

@router.post("/daily-meal", response_model=list[FoodDailyMealRequestPayload])
async def create_daily_meal_request(daily_meal_request: FoodDailyMealRequestPayload, db: Session = Depends(get_db)):
    daily_meal_request_data = daily_meal_request.dict(exclude={"user_id"})
    new_daily_meal_request = FoodDailyMealRequest(user_id=daily_meal_request.user_id, **daily_meal_request_data)
    db.add(new_daily_meal_request)
    await db.commit()
    await db.refresh(new_daily_meal_request)
    return [new_daily_meal_request]

# @router.get("/daily-meal", response_model=list[FoodDailyMealRequestPayload])
# async def get_daily_meal_requests( user_id: Optional[int] = None,db: Session = Depends(get_db)):
#     query = select(FoodDailyMealRequest)

#     if user_id:
#         query = query.where(FoodDailyMealRequest.user_id == user_id)

#     result = await db.execute(query)
#     daily_meal_requests = result.scalars().all()
#     return daily_meal_requests

@router.post("/grocery-essential", response_model=dict)
async def create_grocery_request(
    payload: GroceryRequestPayload,
    db: Session = Depends(get_db)
):
    try:
        # ✅ 1. Main request
        new_request = GroceryEssentialsRequest(
            user_id=payload.user_id,
            food_request_category_id=payload.food_request_category_id,
            status_id=payload.status_id,
            urgency_id=payload.urgency_id,
            request_title=payload.request_title,
            request_description=payload.request_description,
            frequency_id=payload.frequency_id,
            address=payload.address,
            landmark=payload.landmark,
            delivery_required=payload.delivery_required
        )
        db.add(new_request)
        await db.flush()

        # ✅ 2. Items loop (IMPORTANT 🔥)
        for item in payload.items:
            db.add(
                GroceryEssentialsItem(
                    grocery_essentials_request_id=new_request.id,
                    item_master_id=item.item_master_id,
                    custom_item_name=item.custom_item_name,
                    quantity=item.quantity,
                    unit_id=item.unit_id,
                    priority_id=item.priority_id
                )
            )

        await db.commit()

        return {
            "message": "Grocery request created successfully",
            "request_id": new_request.id
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# @router.get("/grocery-essential", response_model=list[dict])
# async def get_grocery_requests(
#     user_id: Optional[int] = None,
#     db: Session = Depends(get_db)
# ):
#     query = select(GroceryEssentialsRequest)

#     if user_id:
#         query = query.where(GroceryEssentialsRequest.user_id == user_id)

#     result = await db.execute(query)
#     requests = result.scalars().all()

#     response = []

#     for r in requests:
#         item_result = await db.execute(
#             select(GroceryEssentialsItem).where(
#                 GroceryEssentialsItem.grocery_essentials_request_id == r.id
#             )
#         )
#         items = item_result.scalars().all()

#         response.append({
#             "id": r.id,
#             "user_id": r.user_id,
#             "food_request_category_id": r.food_request_category_id,
#             "request_title": r.request_title,
#             "request_description": r.request_description,
#             "frequency_id": r.frequency_id,
#             "address": r.address,
#             "landmark": r.landmark,
#             "delivery_required": r.delivery_required,
#             "items": [
#                 {
#                     "id": i.id,
#                     "item_master_id": i.item_master_id,
#                     "custom_item_name": i.custom_item_name,
#                     "quantity": float(i.quantity),
#                     "unit_id": i.unit_id,
#                     "priority_id": i.priority_id
#                 }
#                 for i in items
#             ]
#         })

#     return response