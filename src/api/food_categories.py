from typing import Any, Optional

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

import logging

# Configure logging
logger = logging.getLogger("api.types")
logging.basicConfig(level=logging.INFO)

# Global response helpers
def success_response(data: Any = None, message: str = "Success"):
    return {"success": True, "message": message, "data": data if data is not None else {}}

def error_response(message: str = "Error", error: Any = None):
    return {"success": False, "message": message, "error": error}

# 🔹 GET APIs
router = APIRouter(
    prefix="/api/v1/food", 
    tags=["Food Categories"], 
    # dependencies=[Depends(get_current_user_id)]
)

@router.get("/food-types", response_model=dict)
async def get_food_types(db: Session = Depends(get_db)):
    try:
        result = await db.execute(select(FoodType))
        food_types = result.scalars().all()
        return success_response(
            data=[{"id": ft.id, "name": ft.name} for ft in food_types],
            message="Fetched food types"
        )
    except Exception as e:
        logger.error(f"Error in get_food_types: {e}")
        return error_response(message="Failed to fetch food types", error=str(e))


@router.get("/meal-types", response_model=dict)
async def get_meal_types(db: Session = Depends(get_db)):
    try:
        result = await db.execute(select(FoodMealType))
        meal_types = result.scalars().all()
        return success_response(
            data=[{"id": mt.id, "name": mt.name} for mt in meal_types],
            message="Fetched meal types"
        )
    except Exception as e:
        logger.error(f"Error in get_meal_types: {e}")
        return error_response(message="Failed to fetch meal types", error=str(e))


@router.get("/time-slots", response_model=dict)
async def get_time_slots(db: Session = Depends(get_db)):
    try:
        result = await db.execute(select(FoodTimeSlot))
        time_slots = result.scalars().all()
        return success_response(
            data=[{"id": ts.id, "name": ts.name} for ts in time_slots],
            message="Fetched time slots"
        )
    except Exception as e:
        logger.error(f"Error in get_time_slots: {e}")
        return error_response(message="Failed to fetch time slots", error=str(e))


@router.get("/urgency-levels", response_model=dict)
async def get_urgency_levels(db: Session = Depends(get_db)):
    try:
        result = await db.execute(select(FoodUrgencyLevel))
        urgency_levels = result.scalars().all()
        return success_response(
            data=[{"id": ul.id, "name": ul.name} for ul in urgency_levels],
            message="Fetched urgency levels"
        )
    except Exception as e:
        logger.error(f"Error in get_urgency_levels: {e}")
        return error_response(message="Failed to fetch urgency levels", error=str(e))


@router.get("/delivery-required", response_model=dict)
async def get_delivery_required(db: Session = Depends(get_db)):
    try:
        result = await db.execute(select(DeliveryRequired))
        delivery_required = result.scalars().all()
        return success_response(
            data=[{"id": dr.id, "name": dr.name} for dr in delivery_required],
            message="Fetched delivery required options"
        )
    except Exception as e:
        logger.error(f"Error in get_delivery_required: {e}")
        return error_response(message="Failed to fetch delivery required options", error=str(e))

# 🔹 AGE GROUPS
@router.get("/age-groups", response_model=dict)
async def get_age_groups(db: Session = Depends(get_db)):
    try:
        result = await db.execute(select(FoodAgeGroup))
        age_groups = result.scalars().all()
        return success_response(
            data=[{"id": ag.id, "name": ag.name} for ag in age_groups],
            message="Fetched age groups"
        )
    except Exception as e:
        logger.error(f"Error in get_age_groups: {e}")
        return error_response(message="Failed to fetch age groups", error=str(e))


# 🔹 SPECIAL NEEDS
@router.get("/special-needs", response_model=dict)
async def get_special_needs(db: Session = Depends(get_db)):
    try:
        result = await db.execute(select(FoodSpecialNeed))
        special_needs = result.scalars().all()
        return success_response(
            data=[{"id": sn.id, "name": sn.name} for sn in special_needs],
            message="Fetched special needs"
        )
    except Exception as e:
        logger.error(f"Error in get_special_needs: {e}")
        return error_response(message="Failed to fetch special needs", error=str(e))


# 🔹 MEAL FREQUENCY
@router.get("/meal-frequencies", response_model=dict)
async def get_meal_frequencies(db: Session = Depends(get_db)):
    try:
        result = await db.execute(select(FoodMealFrequency))
        meal_frequencies = result.scalars().all()
        return success_response(
            data=[{"id": mf.id, "name": mf.name} for mf in meal_frequencies],
            message="Fetched meal frequencies"
        )
    except Exception as e:
        logger.error(f"Error in get_meal_frequencies: {e}")
        return error_response(message="Failed to fetch meal frequencies", error=str(e))


# 🔹 DURATION
@router.get("/durations", response_model=dict)
async def get_durations(db: Session = Depends(get_db)):
    try:
        result = await db.execute(select(FoodDuration))
        durations = result.scalars().all()
        return success_response(
            data=[{"id": d.id, "name": d.name} for d in durations],
            message="Fetched durations"
        )
    except Exception as e:
        logger.error(f"Error in get_durations: {e}")
        return error_response(message="Failed to fetch durations", error=str(e))

# 🔹 GROCERY UNIT OPTIONS
@router.get("/grocery-units", response_model=dict)
async def get_grocery_units(db: Session = Depends(get_db)):
    try:
        result = await db.execute(select(GroceryUnitOption))
        grocery_units = result.scalars().all()
        return success_response(
            data=[{"id": unit.id, "name": unit.name} for unit in grocery_units],
            message="Fetched grocery units"
        )
    except Exception as e:
        logger.error(f"Error in get_grocery_units: {e}")
        return error_response(message="Failed to fetch grocery units", error=str(e))


# 🔹 PRIORITY LEVELS
@router.get("/grocery-priority-levels", response_model=dict)
async def get_priority_levels(db: Session = Depends(get_db)):
    try:
        result = await db.execute(select(GroceryPriorityLevel))
        priority_levels = result.scalars().all()
        return success_response(
            data=[{"id": level.id, "name": level.name} for level in priority_levels],
            message="Fetched grocery priority levels"
        )
    except Exception as e:
        logger.error(f"Error in get_priority_levels: {e}")
        return error_response(message="Failed to fetch grocery priority levels", error=str(e))


# 🔹 GROCERY ITEMS
@router.get("/grocery-items", response_model=dict)
async def get_grocery_items(db: Session = Depends(get_db)):
    try:
        result = await db.execute(select(GroceryItemMaster))
        grocery_items = result.scalars().all()
        return success_response(
            data=[{"id": item.id, "name": item.name} for item in grocery_items],
            message="Fetched grocery items"
        )
    except Exception as e:
        logger.error(f"Error in get_grocery_items: {e}")
        return error_response(message="Failed to fetch grocery items", error=str(e))

@router.get("/food-request-categories", response_model=dict)
async def get_food_request_categories(db: Session = Depends(get_db)):
    try:
        result = await db.execute(select(FoodRequestCategory))
        food_request_categories = result.scalars().all()
        return success_response(
            data=[
                {
                    "id": c.id,
                    "name": c.food_type,
                    "description": c.food_type_description,
                    "icon": c.icon,
                    "size": c.size,
                    "value": c.value
                }
                for c in food_request_categories
            ],
            message="Fetched food request categories"
        )
    except Exception as e:
        logger.error(f"Error in get_food_request_categories: {e}")
        return error_response(message="Failed to fetch food request categories", error=str(e))

@router.post("/food-cooked", response_model=dict)
async def create_cooked_food(cooked_food: CookedFoodCreate, db: Session = Depends(get_db)):
    try:
        cooked_food_data = cooked_food.dict(exclude={"user_id"})
        new_cooked_food = FoodRequestsCookedFood(user_id=cooked_food.user_id, **cooked_food_data)
        db.add(new_cooked_food)
        await db.commit()
        await db.refresh(new_cooked_food)
        return success_response(data={"cooked_food": {"id": new_cooked_food.id, "name": new_cooked_food.name}}, message="Cooked food created successfully")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in create_cooked_food: {e}")
        return error_response(message="Failed to create cooked food", error=str(e))

@router.post("/daily-meal", response_model=dict)
async def create_daily_meal_request(daily_meal_request: FoodDailyMealRequestPayload, db: Session = Depends(get_db)):
    try:
        daily_meal_request_data = daily_meal_request.dict(exclude={"user_id"})
        new_daily_meal_request = FoodDailyMealRequest(user_id=daily_meal_request.user_id, **daily_meal_request_data)
        db.add(new_daily_meal_request)
        await db.commit()
        await db.refresh(new_daily_meal_request)
        return success_response(data={"daily_meal_request": {"id": new_daily_meal_request.id, "name": new_daily_meal_request.name}}, message="Daily meal request created successfully")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in create_daily_meal_request: {e}")
        return error_response(message="Failed to create daily meal request", error=str(e))

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
            delivery_required=payload.delivery_required,
            amount_requested=payload.amount_requested
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
        return success_response(data={"request_id": new_request.id}, message="Grocery request created successfully")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in create_grocery_request: {e}")
        return error_response(message="Failed to create grocery request", error=str(e))

