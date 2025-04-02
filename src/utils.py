import json
import logging
import os
import pandas as pd
from typing import Any, Dict, List
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

def load_user_settings():
    """Функция для получения пользовательских настроек"""
    with open('user_settings.json', 'r', encoding='utf-8') as f:
        return json.load(f)


def get_expense_data(start_date, end_date, file_path):
    """Функция для получения данных о расходах из источника"""
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        print(f"Ошибка при загрузке данных: {e}")
        return pd.DataFrame()

    if 'Дата платежа' not in df.columns:
        print("Столбец 'Дата платежа' отсутствует в данных.")
        return pd.DataFrame()

    df['Дата платежа'] = pd.to_datetime(df['Дата платежа'], errors='coerce', dayfirst=True)

    if isinstance(start_date, str):
        start_date = pd.to_datetime(start_date, dayfirst=True)
    if isinstance(end_date, str):
        end_date = pd.to_datetime(end_date, dayfirst=True)

    filtered_df = df[(df['Дата платежа'] >= start_date) & (df['Дата платежа'] <= end_date)]

    if filtered_df.empty:
        print("Нет данных за указанный период.")

    return filtered_df


def get_stock_prices(stocks):
    """Функция для получения курса акций"""
    prices = {}
    base_url = 'https://www.alphavantage.co/query'
    APIKEY = os.getenv("API_KEY_ALPHA")

    for stock in stocks:
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': stock,
            'interval': '5min',
            'apikey': APIKEY
        }

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()

            data = response.json()
            if 'Time Series (5min)' in data:
                latest_time = sorted(data['Time Series (5min)'].keys())[0]
                prices[stock] = data['Time Series (5min)'][latest_time]['4. close']
            else:
                logging.error(f"Нет данных для {stock}. Ответ: {data}")

        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP ошибка при получении цены для {stock}: {http_err}")
        except requests.exceptions.RequestException as req_err:
            logging.error(f"Ошибка сети при получении цены для {stock}: {req_err}")
        except KeyError as key_err:
            logging.error(f"Ошибка доступа к данным для {stock}: {key_err}")
        except Exception as e:
            logging.error(f"Произошла ошибка при получении цены для {stock}: {e}")

    return prices