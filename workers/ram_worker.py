import psutil
from workers.base_worker import BaseWorker


class RamWorker(BaseWorker):
    """Поток проверки информации об оперативной памяти (ОЗУ)."""

    def __init__(self, row_index: int = 3, interval: float = 1.0, parent=None):
        super().__init__(row_index=row_index, interval=interval, parent=parent)

    def fetch_data(self) -> str:
        mem = psutil.virtual_memory()

        # Перевод байтов в гигабайты
        used_gb = mem.used / (1024 ** 3)
        total_gb = mem.total / (1024 ** 3)
        percent = mem.percent

        return f"ОЗУ: {used_gb:.2f} ГБ / {total_gb:.2f} ГБ ({percent}%)"