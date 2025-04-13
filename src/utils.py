import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Union

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

log_dir = "../logs"
os.makedirs(log_dir, exist_ok=True)

logger = logging.getLogger("utils")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(os.path.join(log_dir, "utils.log"), mode="w")
file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s: %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)


def load_user_settings() -> Any:
    """Функция для получения пользовательских настроек из JSON файла."""
    try:
        with open("user_settings.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("Файл user_settings.json не найден.")
    except json.JSONDecodeError:
        logger.error("Ошибка декодирования JSON в user_settings.json.")
    return {}


def get_expense_data(start_date: Union[str, datetime], end_date: Union[str, datetime], file_path: str) -> pd.DataFrame:
    """Функция для получения данных о расходах из Excel файла."""
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных: {e}")
        return pd.DataFrame()

    if "Дата платежа" not in df.columns:
        logger.error('Столбец "Дата платежа" отсутствует в данных.')
        return pd.DataFrame()

    df["Дата платежа"] = pd.to_datetime(df["Дата платежа"], errors="coerce", dayfirst=True)

    start_date = pd.to_datetime(start_date, dayfirst=True) if isinstance(start_date, str) else start_date
    end_date = pd.to_datetime(end_date, dayfirst=True) if isinstance(end_date, str) else end_date

    filtered_df = df[(df["Дата платежа"] >= start_date) & (df["Дата платежа"] <= end_date)]

    if filtered_df.empty:
        logger.info("Нет данных за указанный период.")

    return filtered_df


def get_stock_prices(stocks: list[str]) -> Any:
    """Функция для получения курса акций."""
    stock_prices = []
    base_url = "https://www.alphavantage.co/query"
    apikey = os.getenv("API_KEY_ALPHA")

    for stock in stocks:
        params = {"function": "TIME_SERIES_INTRADAY", "symbol": stock, "interval": "5min", "apikey": apikey}

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()

            data = response.json()
            if "Time Series (5min)" in data:
                latest_time = sorted(data["Time Series (5min)"].keys())[0]
                price = float(data["Time Series (5min)"][latest_time]["4. close"])
                rounded_price = round(price, 2)
                stock_prices.append({"stock": stock, "price": rounded_price})
            else:
                logger.error(f"Нет данных для {stock}. Ответ: {data}")
                stock_prices.append({"stock": stock, "price": None})

        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP ошибка при получении цены для {stock}: {http_err}")
            stock_prices.append({"stock": stock, "price": None})
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Ошибка сети при получении цены для {stock}: {req_err}")
            stock_prices.append({"stock": stock, "price": None})
        except KeyError as key_err:
            logger.error(f"Ошибка доступа к данным для {stock}: {key_err}")
            stock_prices.append({"stock": stock, "price": None})
        except Exception as e:
            logger.error(f"Произошла ошибка при получении цены для {stock}: {e}")
            stock_prices.append({"stock": stock, "price": None})

    return stock_prices


def get_currency_rate(currencies: list[str]) -> Any:
    """Возвращает список словарей курсов валют по отношению к рублю."""
    apikey = os.getenv("API_KEY_APILAYER")
    headers = {"apikey": f"{apikey}"}
    currency_rates = []

    try:
        response = requests.get("https://api.apilayer.com/exchangerates_data/latest?base=RUB", headers=headers)
        response.raise_for_status()
        data = response.json()

        rates = data.get("rates", {})

        for currency in currencies:
            if currency in rates:
                rate = 1 / rates[currency]
                rounded_rate = round(rate, 2)
                currency_rates.append({"currency": currency, "rate": rounded_rate})
            else:
                logger.warning(f"Курс для валюты {currency} не найден.")
                currency_rates.append({"currency": currency, "rate": None})

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP ошибка при получении курса валюты: {http_err}")
    except Exception as err:
        logger.error(f"Произошла ошибка при получении курса валюты: {err}")
        return []

    return currency_rates


def generate_response(expense_data: pd.DataFrame, user_settings: Dict[str, Any]) -> str:
    """Создает ответ, содержащий информацию о расходах, включая топ-транзакции,
    приветствие, сводку по картам, курсы валют и цены акций."""

    current_time = datetime.now()
    hour = current_time.hour

    if hour < 6:
        greeting = "Доброй ночи"
    elif hour < 12:
        greeting = "Доброе утро"
    elif hour < 18:
        greeting = "Добрый день"
    else:
        greeting = "Добрый вечер"

    response: Dict[str, Any] = {
        "greeting": greeting,
        "cards": [],
        "top_transactions": [],
        "currency_rates": [],
        "stock_prices": [],
    }

    card_summaries: List[Dict[str, Union[str, float]]] = []

    for last_digits, group in expense_data.groupby("Номер карты"):
        last_digits_str = str(last_digits)
        total_spent_card = group["Сумма платежа"].sum()
        cashback_card = total_spent_card * 0.01

        card_summaries.append(
            {
                "last_digits": last_digits_str[-4:],
                "total_spent": round(abs(total_spent_card), 2),
                "cashback": round(abs(cashback_card), 2),
            }
        )
    response["cards"] = card_summaries

    top_transactions = expense_data.nlargest(5, "Сумма платежа")
    top_transactions_list: List[Dict[str, Union[str, float]]] = []
    for index, row in top_transactions.iterrows():
        top_transactions_list.append(
            {
                "date": row["Дата платежа"].strftime("%d.%m.%Y"),
                "amount": row["Сумма платежа"],
                "category": row["Категория"],
                "description": row["Описание"],
            }
        )

    response["top_transactions"] = top_transactions_list

    currency_rates: List[Dict[str, Union[str, float, None]]] = get_currency_rate(
        user_settings.get("user_currencies", [])
    )
    stock_prices: List[Dict[str, Union[str, float, None]]] = get_stock_prices(user_settings.get("user_stocks", []))

    response["currency_rates"] = currency_rates
    response["stock_prices"] = stock_prices

    return json.dumps(response, ensure_ascii=False)
