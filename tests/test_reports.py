import pandas as pd
from datetime import datetime
from typing import Optional
from unittest.mock import patch, Mock
from src.reports import spending_by_category


def test_spending_by_category_no_transactions() -> None:
    transactions = pd.DataFrame(columns=["Дата платежа", "Сумма платежа", "Категория"])
    result = spending_by_category(transactions, "Продукты")
    assert result.empty is True


def test_spending_by_category_wrong_category() -> None:
    data = {
        "Дата платежа": ["2023-09-15", "2023-09-20"],
        "Сумма платежа": [100, 200],
        "Категория": ["Продукты", "Подарки"],
    }
    transactions = pd.DataFrame(data)

    result = spending_by_category(transactions, "Развлечение", "2023-09-30")
    assert result.empty is True
