import time
import psutil
from workers.base_worker import BaseWorker


class NetworkTrafficWorker(BaseWorker):
    """Поток проверки сетевого трафика (Скорость RX/TX и счетчик пакетов)."""

    def __init__(self, row_index: int = 6, interval: float = 1.0, parent=None):
        super().__init__(row_index=row_index, interval=interval, parent=parent)
        self._last_net = psutil.net_io_counters()
        self._last_time = time.time()

    def fetch_data(self) -> str:
        current_net = psutil.net_io_counters()
        current_time = time.time()
        time_delta = current_time - self._last_time

        rx_speed_kb = 0.0
        tx_speed_kb = 0.0

        if self._last_net and current_net and time_delta > 0:
            bytes_recv = current_net.bytes_recv - self._last_net.bytes_recv
            bytes_sent = current_net.bytes_sent - self._last_net.bytes_sent
            
            rx_speed_kb = (bytes_recv / time_delta) / 1024
            tx_speed_kb = (bytes_sent / time_delta) / 1024

        self._last_net = current_net
        self._last_time = current_time

        total_packets = current_net.packets_recv + current_net.packets_sent

        # Динамическое форматирование: если скорость > 1024 КБ/с, выводится в МБ/с
        rx_str = f"{rx_speed_kb / 1024:.2f} МБ/с" if rx_speed_kb >= 1024 else f"{rx_speed_kb:.1f} КБ/с"
        tx_str = f"{tx_speed_kb / 1024:.2f} МБ/с" if tx_speed_kb >= 1024 else f"{tx_speed_kb:.1f} КБ/с"

        return f"Сеть: (Прием): {rx_str} | (Отдача):{tx_str} (Всего пакетов: {total_packets})"