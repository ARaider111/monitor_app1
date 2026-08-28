import psutil
from workers.base_worker import BaseWorker


class CpuUsageWorker(BaseWorker):
    """Поток проверки загрузки процессора (Общая и поядерная)."""

    def __init__(self, row_index: int = 5, interval: float = 1.0, parent=None):
        super().__init__(row_index=row_index, interval=interval, parent=parent)
        # Первичная инициализация внутреннего счетчика времени
        psutil.cpu_percent(percpu=True)

    def fetch_data(self) -> str:
        # Получение загрузки по каждому ядру
        per_core = psutil.cpu_percent(interval=None, percpu=True)
        
        # Общая средняя загрузка
        total_load = sum(per_core) / len(per_core) if per_core else 0.0

        # Форматирование поядерного вывод
        # Если ядер больше 4, компактно выводим первые 4 или общий срез
        cores_str = ", ".join([f"C{i+1}: {val:.0f}%" for i, val in enumerate(per_core[:6])])
        if len(per_core) > 6:
            cores_str += f", +{len(per_core) - 6} ядер"

        return f"Загрузка CPU: {total_load:.1f}% [{cores_str}]"