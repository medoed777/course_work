from typing import Any
from unittest.mock import patch

from src.views import main


def mock_get_expense_data(start_date: str, end_date: str) -> Any:
    return [
        {
            "Номер карты": ["1234 5678 9012 3456"],
            "Сумма платежа": [2000],
            "Дата платежа": [start_date],
            "Категория": ["Еда"],
            "Описание": ["Ресторан"],
        },
        {
            "Номер карты": ["1234 5678 9012 3456"],
            "Сумма платежа": [1000],
            "Дата платежа": [end_date],
            "Категория": ["Транспорт"],
            "Описание": ["Такси"],
        },
    ]


def mock_load_user_settings() -> Any:
    return {"currency": "RUB"}


def mock_generate_response(expense_data: Any, user_settings: Any) -> Any:
    total_expense = sum(item["Сумма платежа"] for item in expense_data)
    return {
        "greeting": "Добрый день",
        "total_expense": total_expense,
        "currency": user_settings["currency"],
        "cards": [{"last_digits": "3456", "total_spent": total_expense}],
    }


@patch("src.utils.get_expense_data", side_effect=mock_get_expense_data)
@patch("src.utils.load_user_settings", side_effect=mock_load_user_settings)
@patch("src.utils.generate_response", side_effect=mock_generate_response)
def test_main(mock_get_data: Any, mock_load_settings: Any, mock_generate_response: Any) -> Any:
    with patch("builtins.print") as mock_print:
        main("2023-10-01 00:00:00")

        output = [call[0][0] for call in mock_print.call_args_list]

    assert any("Добрый вечер" in line for line in output)
    assert any("currency" in line for line in output)
    assert any("cards" in line for line in output)
