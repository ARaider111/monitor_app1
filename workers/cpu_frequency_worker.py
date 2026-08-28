import psutil

from .base_worker import BaseWorker


class CpuFrequencyWorker(BaseWorker):
    """Поток проверки мониторинга частоты процессора."""

    def __init__(self, row_index: int = 10, interval: float = 2.0, parent=None):
        super().__init__(row_index=row_index, interval=interval, parent=parent)

    @staticmethod
    def _format_frequency(mhz: float) -> str:
        #Преобразует МГц в удобную строку

        if mhz >= 1000:
            return f"{mhz / 1000:.2f} ГГц"

        return f"{mhz:.0f} МГц"

    def fetch_data(self) -> str:
        try:
            frequency = psutil.cpu_freq()

            if frequency is None or frequency.current <= 0:
                return "Частота CPU: данные недоступны"

            current = self._format_frequency(frequency.current)

            result = f"Частота CPU: {current}"
            return result

        except Exception as exc:
            return f"Частота CPU: ошибка ({exc})"