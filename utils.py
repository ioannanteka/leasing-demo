from collections.abc import Mapping
from typing import Any

import pandas as pd

FILTER_COLUMN_ALIASES = {
    "max_monthly_payment": "monthly_payment",
    "max_initial_payment": "deposit_amount",
    "max_annual_mileage": "annual_mileage",
}


def filter_deals(deals: pd.DataFrame, filters: Mapping[str, Any]) -> pd.DataFrame:
    filtered_deals = deals.copy()

    for filter_name, filter_value in filters.items():
        if filter_value is None:
            continue

        if filter_value == 'Any':
            continue


        column_name = FILTER_COLUMN_ALIASES.get(filter_name, filter_name)
        if column_name not in filtered_deals.columns:
            continue

        if filter_name.startswith("max_"):
            filtered_deals = filtered_deals[filtered_deals[column_name] <= filter_value]

        if isinstance(filter_value, str):
            filtered_deals = filtered_deals[filtered_deals[column_name] == filter_value]

        if isinstance(filter_value, list):
            filtered_deals = filtered_deals[filtered_deals[column_name].isin(filter_value)]

    return filtered_deals
