from typing import List, Dict, Any
from datetime import datetime, timedelta


def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int) -> float:
    """Функция, для высчета даты, фильтра транзакций"""
    target_month_start = datetime.strptime(month, "%Y-%m")

    target_month_end = target_month_start.replace(day=1) + timedelta(days=31)
    target_month_end = target_month_end.replace(day=1)

    filtered_transactions = [
        transaction
        for transaction in transactions
        if target_month_start <= datetime.strptime(transaction["Дата операции"], "%Y-%m-%d") < target_month_end
    ]

    def calculate_investment(transaction: List[Dict[str, Any]]) -> float:
        """Функция для округления и вычисления доли, которая идет в инвесткопилку"""
        original_amount = transaction["Сумма операции"]
        rounded_amount = ((original_amount // limit) + 1) * limit
        return rounded_amount - original_amount

    total_investment = sum(map(calculate_investment, filtered_transactions))

    return total_investment
