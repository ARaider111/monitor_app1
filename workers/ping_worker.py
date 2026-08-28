import sys
import re
import subprocess
from .base_worker import BaseWorker


class PingWorker(BaseWorker):
    """Поток проверки сетевого отклика."""

    def __init__(self, row_index: int = 1, host: str = "8.8.8.8", interval: float = 2.0, parent=None):
        super().__init__(row_index=row_index, interval=interval, parent=parent)
        self.host = host

    def fetch_data(self) -> str:
        count_flag = "-n" if sys.platform == "win32" else "-c"
        timeout_flag = "-W" if sys.platform != "win32" else "-w"
        timeout_val = "2" if sys.platform != "win32" else "2000"

        cmd = ["ping", count_flag, "1", timeout_flag, timeout_val, self.host]

        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=3.0,
            )

            if proc.returncode == 0:
                match = re.search(r"time[=<](\d+(?:\.\d+)?)\s*ms", proc.stdout, re.IGNORECASE)
                if match:
                    return f"Ping ({self.host}): Доступен (RTT = {match.group(1)} мс)"
                return f"Ping ({self.host}): Доступен"
            return f"Ping ({self.host}): Недоступен (Превышен таймаут)"
        except subprocess.TimeoutExpired:
            return f"Ping ({self.host}): Недоступен (Timeout)"
        except Exception as e:
            return f"Ping ({self.host}): Ошибка ({e})"