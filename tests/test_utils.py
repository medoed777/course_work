import json
import logging
from typing import Any
from unittest.mock import MagicMock, Mock, mock_open, patch
from datetime import datetime
import pandas as pd
import pytest
import requests
from pytest import MonkeyPatch

from src.utils import get_currency_rate, get_expense_data, get_stock_prices, load_user_settings, generate_response

log_dir = "../logs"
logger = logging.getLogger("utils")


def test_load_user_settings_success() -> None:
    mock_json_data = '{"setting1": "value1", "setting2": "value2"}'

    with patch("builtins.open", mock_open(read_data=mock_json_data)):
        with patch("json.load", return_value=json.loads(mock_json_data)):
            settings = load_user_settings()

    assert settings == {"setting1": "value1", "setting2": "value2"}


def test_load_user_settings_file_not_found() -> None:
    with patch("builtins.open", side_effect=FileNotFoundError):
        with patch("src.utils.logger") as mock_logger:
            settings = load_user_settings()

    assert settings == {}
    mock_logger.error.assert_called_once_with("Файл user_settings.json не найден.")


def test_load_user_settings_json_decode_error() -> None:
    with patch("builtins.open", mock_open(read_data="invalid json")):
        with patch("json.load", side_effect=json.JSONDecodeError("Expecting value", "", 0)):
            with patch("src.utils.logger") as mock_logger:
                settings = load_user_settings()

    assert settings == {}
    mock_logger.error.assert_called_once_with("Ошибка декодирования JSON в user_settings.json.")


@pytest.fixture
def mock_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Дата платежа": ["01.01.2022", "15.01.2022", "20.01.2022"],
            "Сумма": [100, 150, 200],
        }
    )


@patch("pandas.read_excel")
def test_get_expense_data_success(mock_read_excel: MagicMock, mock_data: pd.DataFrame) -> Any:
    mock_read_excel.return_value = mock_data

    start_date: str = "01.01.2022"
    end_date: str = "15.01.2022"
    result = get_expense_data(start_date, end_date, "fake_path.xlsx")

    assert not result.empty
    assert len(result) == 2


@patch("pandas.read_excel", side_effect=FileNotFoundError)
@patch("src.utils.logger")
def test_get_expense_data_file_not_found(mock_logger: MagicMock, mock_read_excel: MagicMock) -> None:
    result = get_expense_data("01.01.2022", "15.01.2022", "fake_path.xlsx")

    assert result.equals(pd.DataFrame())
    mock_logger.error.assert_called_once_with("Ошибка при загрузке данных: ")


@patch("pandas.read_excel")
def test_get_expense_data_missing_column(mock_read_excel: MagicMock) -> None:
    mock_read_excel.return_value = pd.DataFrame({"Сумма": [100, 150]})

    with patch("src.utils.logger") as mock_logger:
        result = get_expense_data("01.01.2022", "15.01.2022", "fake_path.xlsx")

        assert result.equals(pd.DataFrame())

        mock_logger.error.assert_called_once_with('Столбец "Дата платежа" отсутствует в данных.')


@patch("pandas.read_excel")
def test_get_expense_data_no_data_in_period(mock_read_excel: MagicMock, mock_data: pd.DataFrame) -> None:
    mock_read_excel.return_value = mock_data

    start_date = "25.01.2022"
    end_date = "30.01.2022"
    with patch("src.utils.logger") as mock_logger:
        result = get_expense_data(start_date, end_date, "fake_path.xlsx")

    assert result.empty
    mock_logger.info.assert_called_once_with("Нет данных за указанный период.")


@pytest.fixture(scope="function", autouse=True)
def mock_env(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY_ALPHA", "fake_api_key")


def test_get_stock_prices_success() -> None:
    stocks = ["AAPL", "MSFT"]
    mock_response = {
        "Time Series (5min)": {
            "2022-01-01 15:00:00": {
                "1. open": "150.00",
                "2. high": "155.00",
                "3. low": "149.00",
                "4. close": "150.00",
            },
            "2022-01-01 14:55:00": {
                "1. open": "149.00",
                "2. high": "150.00",
                "3. low": "148.00",
                "4. close": "150.00",
            },
        }
    }

    with patch("requests.get") as mock_get:
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_response)

        result = get_stock_prices(stocks)

        assert len(result) == 2
        assert result[0] == {"stock": "AAPL", "price": 150.00}
        assert result[1] == {"stock": "MSFT", "price": 150.00}


def test_get_stock_prices_no_data() -> None:
    stocks = ["INVALID"]
    mock_response: dict[str, dict] = {}

    with patch("requests.get") as mock_get:
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_response)

        result = get_stock_prices(stocks)

        assert len(result) == 1
        assert result[0] == {"stock": "INVALID", "price": None}


def test_get_stock_prices_http_error() -> None:
    stocks = ["AAPL"]

    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.HTTPError("HTTP error")

        result = get_stock_prices(stocks)

        assert len(result) == 1
        assert result[0] == {"stock": "AAPL", "price": None}


def test_get_stock_prices_request_exception() -> None:
    stocks = ["AAPL"]

    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.RequestException("Request error")

        result = get_stock_prices(stocks)

        assert len(result) == 1
        assert result[0] == {"stock": "AAPL", "price": None}


def test_get_stock_prices_key_error() -> None:
    stocks = ["AAPL"]
    mock_response = {
        "Time Series (5min)": {
            "2022-01-01 15:00:00": {"1. open": "150.00", "2. high": "155.00", "3. low": "149.00"},
        }
    }

    with patch("requests.get") as mock_get:
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_response)

        result = get_stock_prices(stocks)

        assert len(result) == 1
        assert result[0] == {"stock": "AAPL", "price": None}


@pytest.fixture(scope="function", autouse=True)
def mock_env_(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY_APILAYER", "fake_api_key")


@pytest.mark.parametrize(
    "currencies, mock_response, expected",
    [
        (
            ["EUR", "USD"],
            {"rates": {"EUR": 0.85, "USD": 0.75}, "base": "RUB", "date": "2023-01-01"},
            [{"currency": "EUR", "rate": 1.18}, {"currency": "USD", "rate": 1.33}],
        ),
        (
            ["EUR", "INVALID"],
            {"rates": {"EUR": 0.85, "USD": 0.75}, "base": "RUB", "date": "2023-01-01"},
            [{"currency": "EUR", "rate": 1.18}, {"currency": "INVALID", "rate": None}],
        ),
        ([], {"rates": {}, "base": "RUB", "date": "2023-01-01"}, []),
        (["EUR"], {"base": "RUB", "date": "2023-01-01"}, [{"currency": "EUR", "rate": None}]),
    ],
)
def test_get_currency_rate(currencies: list[str], mock_response: dict[str, Any], expected: Any) -> None:
    with patch("requests.get") as mock_get:
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_response)

        result = get_currency_rate(currencies)

        assert result == expected


def test_get_currency_rate_http_error() -> None:
    currencies = ["EUR"]

    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.HTTPError("HTTP error")

        result = get_currency_rate(currencies)

        assert result == []


def test_generate_response_with_no_expenses() -> None:
    expense_data = pd.DataFrame(columns=["Номер карты", "Сумма платежа", "Дата платежа", "Категория", "Описание"])
    expense_data["Сумма платежа"] = pd.to_numeric(expense_data["Сумма платежа"], errors="coerce")
    user_settings = {}

    result = generate_response(expense_data, user_settings)
    parsed_result = json.loads(result)

    assert parsed_result["greeting"] is not None
    assert parsed_result["cards"] == []
    assert parsed_result["top_transactions"] == []
    assert parsed_result["currency_rates"] == []
    assert parsed_result["stock_prices"] == []


def test_generate_response_with_expenses() -> None:
    expense_data = pd.DataFrame(
        {
            "Номер карты": ["1234567890123456", "1234567890123456", "9876543210123456"],
            "Сумма платежа": [100.50, 200.75, 50.25],
            "Дата платежа": [datetime(2023, 9, 29), datetime(2023, 9, 30), datetime(2023, 9, 30)],
            "Категория": ["Еда", "Транспорт", "Развлечения"],
            "Описание": ["Покупка еды", "Поездка на такси", "Поход в кино"],
        }
    )

    user_settings = {"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "GOOGL"]}

    with patch("src.utils.get_currency_rate", return_value=[{"currency": "USD", "rate": 73.50}]):
        with patch("src.utils.get_stock_prices", return_value=[{"stock": "AAPL", "price": 150.00}]):
            result = generate_response(expense_data, user_settings)
            parsed_result = json.loads(result)

            assert parsed_result["greeting"] is not None
            assert len(parsed_result["cards"]) == 2
            assert parsed_result["top_transactions"][0]["amount"] == 200.75
            assert len(parsed_result["currency_rates"]) == 1
            assert len(parsed_result["stock_prices"]) == 1
