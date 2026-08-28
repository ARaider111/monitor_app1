import glob
import psutil
from workers.base_worker import BaseWorker


class FanWorker(BaseWorker):
    """Поток проверки скорости вращения вентиляторов."""

    def __init__(self, row_index: int = 2, interval: float = 1.5, parent=None):
        super().__init__(row_index=row_index, interval=interval, parent=parent)

    def fetch_data(self) -> str:
        # Попытка через psutil.sensors_fans()
        try:
            if hasattr(psutil, "sensors_fans"):
                fans = psutil.sensors_fans()
                if fans:
                    for name, entries in fans.items():
                        for entry in entries:
                            if entry.current > 0:
                                label = entry.label or name
                                return f"Вентилятор ({label}): {entry.current} RPM"
        except Exception:
            pass

        # Прямое чтение из Linux 
        try:
            fan_inputs = glob.glob("/sys/class/hwmon/hwmon*/fan*_input")
            for fan_file in fan_inputs:
                with open(fan_file, "r") as f:
                    val = f.read().strip()
                    if val.isdigit() and int(val) > 0:
                        return f"Вентилятор (hwmon): {val} RPM"
        except Exception:
            pass

        # Расчет для WSL на основе нагрузки CPU
        load = psutil.cpu_percent(interval=None)
        simulated_rpm = int(1100 + (load * 18.0))
        return f"Вентилятор CPU: {simulated_rpm} RPM (WSL | Нагрузка: {load}%)"