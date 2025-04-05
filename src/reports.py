import pandas as pd
import json
import logging
from datetime import datetime
from functools import wraps
from typing import Optional

log_dir = "../logs"

logger = logging.getLogger("utils")


def report_to_file(filename=None):
    """Декоратор для записи результатов отчета в файл"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if isinstance(result, pd.DataFrame):
                if filename is None:
                    filename = f'report_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                result.to_json(filename, orient="records", lines=True)
                logger.info(f"Отчет сохранен в файл: {filename}")
            else:
                logger.warning("Функция возвращает не DataFrame, отчет не сохранен.")
            return result

        return wrapper

    return decorator if filename else decorator


@report_to_file()
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    """Функция для получения трат по заданной категории за последние три месяца."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    date = pd.to_datetime(date)
    start_date = date - pd.DateOffset(months=3)

    filtered_transactions = transactions[
        (transactions["category"] == category) & (transactions["date"] >= start_date) & (transactions["date"] <= date)
    ]

    return filtered_transactions.groupby("category")["amount"].sum().reset_index()


data = {
    "date": pd.to_datetime(["2023-01-01", "2023-01-15", "2023-02-01", "2023-03-01", "2023-03-15"]),
    "category": ["food", "food", "transport", "food", "transport"],
    "amount": [100, 150, 50, 200, 80],
}
transactions_df = pd.DataFrame(data)

# Вызов функции
result = spending_by_category(transactions_df, "food")

# Проверка результата
print(result)
