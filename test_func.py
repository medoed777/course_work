import requests
import logging
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

APIKEY = os.getenv("API_KEY_TWELVE_DATA")

def get_stock_prices(stocks):
    """Функция для получения курса акций"""
    prices = {}

    base_url = 'https://api.twelvedata.com/time_series'

    for stock in stocks:
        params = {
            'symbol': stock,
            'interval': '1min',
            'apikey': APIKEY
        }

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()  # Проверка на ошибки HTTP

            data = response.json()
            if 'values' in data and len(data['values']) > 0:
                prices[stock] = data['values'][0]['close']  # Получаем цену закрытия последней записи
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


# Пример использования
if __name__ == "__main__":
    # logging.basicConfig(level=logging.ERROR)  # Настройка уровня логирования
    # stocks_to_check = ['AAPL', 'EUR/USD', 'CBQK']  # Пример списка акций
    # prices = get_stock_prices(stocks_to_check)
    # print(prices)
    print(f"API Key: {APIKEY}")