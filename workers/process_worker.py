import psutil

from workers.base_worker import BaseWorker


class ProcessWorker(BaseWorker):
    """Поток проверки процесса с максимальным потреблением RAM."""

    def __init__(self, row_index: int = 9, interval: float = 5.0, parent=None):
        super().__init__(row_index=row_index, interval=interval, parent=parent)

    def fetch_data(self) -> str:
        try:
            processes_count = 0
            top_process = None

            for process in psutil.process_iter(["pid", "name", "memory_info"]):
                try:
                    info = process.info
                    memory_info = info["memory_info"]

                    if memory_info is None:
                        continue

                    processes_count += 1
                    ram_bytes = memory_info.rss

                    if top_process is None or ram_bytes > top_process["ram_bytes"]:
                        top_process = {
                            "pid": info["pid"],
                            "name": info["name"] or "Unknown",
                            "ram_bytes": ram_bytes,
                        }

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if top_process is None:
                return "Процессы: данные недоступны"

            ram_mb = top_process["ram_bytes"] / (1024 * 1024)

            return (
                f"Процессы: {processes_count} | "
                f"RAM-лидер: {top_process['name']} "
                f"(PID {top_process['pid']}, {ram_mb:.0f} МБ)"
            )

        except Exception as exc:
            return f"Процессы: ошибка ({exc})"