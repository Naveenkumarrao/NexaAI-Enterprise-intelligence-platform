import re
from typing import Union


def safe_calculate(expression: str) -> Union[float, str]:
    """Safely evaluate a mathematical expression."""
    allowed = re.compile(r'^[\d\s\+\-\*\/\.\(\)\%\^]+$')
    expression = expression.strip().replace('^', '**').replace('%', '/100')
    if not allowed.match(expression):
        return f"[Calculator] Invalid expression: {expression}"
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return round(float(result), 4)
    except Exception as e:
        return f"[Calculator error] {e}"


def compute_tco(costs: dict) -> dict:
    """
    Compute Total Cost of Ownership.
    costs = {
        'initial': float,
        'annual_maintenance': float,
        'years': int,
        'other_costs': float (optional)
    }
    """
    initial = costs.get('initial', 0)
    annual = costs.get('annual_maintenance', 0)
    years = costs.get('years', 1)
    other = costs.get('other_costs', 0)
    tco = initial + (annual * years) + other
    return {
        "initial_cost": initial,
        "annual_maintenance": annual,
        "years": years,
        "other_costs": other,
        "total_tco": round(tco, 2),
    }


def compare_numeric_values(values: dict) -> dict:
    """Compare numeric values across vendors/options."""
    if not values:
        return {}
    sorted_items = sorted(values.items(), key=lambda x: x[1])
    best = sorted_items[0]
    worst = sorted_items[-1]
    return {
        "values": values,
        "best": {"name": best[0], "value": best[1]},
        "worst": {"name": worst[0], "value": worst[1]},
        "range": round(worst[1] - best[1], 4),
    }
