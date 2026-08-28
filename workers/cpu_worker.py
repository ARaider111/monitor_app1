import shutil
import subprocess
import psutil
from .base_worker import BaseWorker


class CpuTempWorker(BaseWorker):
    """Поток проверки температуры процессора."""

    def __init__(self, row_index: int = 0, interval: float = 1.0, parent=None):
        super().__init__(row_index=row_index, interval=interval, parent=parent)

    def fetch_data(self) -> str:
        # Проверка через PowerShell (WSL / Win32)
        ps_path = shutil.which("powershell.exe")
        if ps_path:
            try:
                cmd = [
                    ps_path,
                    "-NoProfile",
                    "-Command",
                    "(Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature).CurrentTemperature",
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=1.5)
                out = res.stdout.strip()
                if out and out.replace(".", "").isdigit():
                    kelvin_tenths = float(out.split()[0])
                    celsius = (kelvin_tenths - 2732.0) / 10.0
                    if 15.0 <= celsius <= 115.0:
                        return f"Температура CPU (Host WMI): {celsius:.1f} °C"
            except Exception:
                pass

        # Прямые Linux-датчики 
        try:
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    for entries in temps.values():
                        if entries:
                            return f"Температура CPU: {entries[0].current:.1f} °C"
        except Exception:
            pass

        # Фоллбек по загрузке
        load = psutil.cpu_percent(interval=None)
        est_temp = 40.0 + (load * 0.4)
        return f"Температура CPU: {est_temp:.1f} °C (WSL эмуляция | Загрузка: {load}%)"