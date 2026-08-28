import random
import secrets
from workers.base_worker import BaseWorker


class RandomDataWorker(BaseWorker):
    """Поток проверки генератор случайных чисел и энтропии."""

    def __init__(self, row_index: int = 7, interval: float = 1.0, parent=None):
        super().__init__(row_index=row_index, interval=interval, parent=parent)

    def fetch_data(self) -> str:
        # Генерируется 4 случайных числа от 10 до 99
        nums = [random.randint(10, 99) for _ in range(4)]
        nums_str = ", ".join(map(str, nums))
        total_sum = sum(nums)
        
        # Генерация короткого случайного hex-токена
        token = secrets.token_hex(3).upper()

        return f"Случайные числа: [{nums_str}] | Сумма: {total_sum} | Hash: 0x{token}"