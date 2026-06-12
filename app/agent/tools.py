from typing import Any, Dict, List, Optional

from langchain_core.tools import tool

from app.car_loader import CAR_DATASET


@tool
def search_cars_tool(
    budget: Optional[int] = None,
    transmission: Optional[str] = None,
    use_case: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Queries the car database using criteria extracted from the buyer profile.
    Budget is expected in INR as an integer (e.g. 1500000 for 15 lakhs).
    Returns up to 5 matching cars sorted by user rating descending.
    """
    results = []

    target_transmission = transmission.strip().lower() if transmission else None
    target_use_case = use_case.strip().lower().replace(" ", "_") if use_case else None

    for car in CAR_DATASET:
        # 1. Budget filter — convert INR to lakhs for comparison
        if budget is not None:
            try:
                budget_in_lakhs = budget / 100000.0
                if car.get("price_lakh", 0) > budget_in_lakhs:
                    continue
            except TypeError:
                pass

        # 2. Transmission filter
        if target_transmission and target_transmission != "no preference":
            car_transmission = car.get("transmission", "").lower()
            if target_transmission != car_transmission:
                continue

        # 3. Use case filter — partial match against use_case array
        if target_use_case:
            car_use_cases = [uc.lower() for uc in car.get("use_case", [])]
            if not any(
                target_use_case in uc or uc in target_use_case
                for uc in car_use_cases
            ):
                continue

        results.append(car)

    results.sort(key=lambda x: x.get("user_rating", 0.0), reverse=True)

    return results[:5]