import time
from abc import abstractmethod
from PySide6.QtCore import QThread, Signal


class BaseWorker(QThread):
    """Базовый поток с общим сигналом и циклом опроса."""
    data_updated = Signal(int, str)  

    def __init__(self, row_index: int, interval: float = 1.0, parent=None):
        super().__init__(parent)
        self.row_index = row_index
        self.interval = interval
        self._is_running = True

    def run(self):
        while self._is_running:
            try:
                result = self.fetch_data()
            except Exception as e:
                result = f"Ошибка потока: {e}"

            self.data_updated.emit(self.row_index, result)

            # Пошаговый сон для быстрой остановки
            slept = 0.0
            while self._is_running and slept < self.interval:
                time.sleep(0.1)
                slept += 0.1

    def stop(self):
        self._is_running = False

    @abstractmethod
    def fetch_data(self) -> str:
        pass