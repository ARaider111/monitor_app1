import os
import time
import psutil
from workers.base_worker import BaseWorker


class DiskWorker(BaseWorker):
    """Поток проверки данные накопителя SSD/HDD (Занятое место + скорость чтения/записи)."""

    def __init__(self, row_index: int = 4, interval: float = 1.0, parent=None):
        super().__init__(row_index=row_index, interval=interval, parent=parent)
        # Сохраняем предыдущие значения для вычисления скорости 
        self._last_io = psutil.disk_io_counters()
        self._last_time = time.time()

    def fetch_data(self) -> str:
        # Корневой путь: 'C:\\' для Windows или '/' для Linux/WSL
        root_path = "C:\\" if os.name == "nt" else "/"
        
        # Заполненность диска
        usage = psutil.disk_usage(root_path)
        used_gb = usage.used / (1024 ** 3)
        total_gb = usage.total / (1024 ** 3)
        percent = usage.percent

        # Скорость чтения/записи
        current_io = psutil.disk_io_counters()
        current_time = time.time()
        time_delta = current_time - self._last_time

        read_speed_mb = 0.0
        write_speed_mb = 0.0

        if self._last_io and current_io and time_delta > 0:
            read_bytes_sec = (current_io.read_bytes - self._last_io.read_bytes) / time_delta
            write_bytes_sec = (current_io.write_bytes - self._last_io.write_bytes) / time_delta
            read_speed_mb = read_bytes_sec / (1024 ** 2)
            write_speed_mb = write_bytes_sec / (1024 ** 2)

        self._last_io = current_io
        self._last_time = current_time

        return (
            f"Диск ({root_path}): {used_gb:.1f}/{total_gb:.1f} ГБ ({percent}%) | "
            f"R: {read_speed_mb:.1f} МБ/с, W: {write_speed_mb:.1f} МБ/с"
        )