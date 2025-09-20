import pytest
from datetime import datetime
from src.services import investment_bank


@pytest.mark.parametrize(
    "month, transactions, limit, expected",
    [
        (
            "2023-01",
            [
                {"Дата операции": "2023-01-01", "Сумма операции": 1712},
                {"Дата операции": "2023-01-15", "Сумма операции": 1234},
                {"Дата операции": "2023-01-20", "Сумма операции": 567},
            ],
            50,
            87,
        ),
        (
            "2023-01",
            [
                {"Дата операции": "2023-01-31", "Сумма операции": 200},
                {"Дата операции": "2023-02-01", "Сумма операции": 300},
            ],
            100,
            100,
        ),
        (
            "2023-02",
            [
                {"Дата операции": "2023-02-05", "Сумма операции": 1100},
                {"Дата операции": "2023-02-20", "Сумма операции": 1500},
            ],
            250,
            400,
        ),
    ],
)
def test_investment_bank(month, transactions, limit, expected):
    result = investment_bank(month, transactions, limit)
    assert result == expected
