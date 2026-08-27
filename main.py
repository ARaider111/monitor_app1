import sys
import time
import psutil
import shutil
import subprocess
from PySide6.QtCore import Signal, QThread, Slot
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel

class CpuTempWorker(QThread):
    # Сигнал для передачи строки с температурой 
    temperature_updated = Signal(str)

    def __init__(self, interval: float = 1.0, parent=None):
        super().__init__(parent)
        self.interval = interval
        self._is_running = True

    def run(self):
        while self._is_running:
            temp_str = self._get_cpu_temperature()
            self.temperature_updated.emit(temp_str)

            slept = 0.0
            while self._is_running and slept < self.interval:
                time.sleep(0.1)
                slept += 0.1

    def stop(self):
        self._is_running = False

    def _get_cpu_temperature(self) -> str:
        # 1. Попытка запросить температуру у хостовой Windows через WSL-интероп
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

        # 2. Стандартная попытка Linux-датчиков (для bare-metal систем)
        try:
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    for entries in temps.values():
                        if entries:
                            return f"Температура CPU: {entries[0].current:.1f} °C"
        except Exception:
            pass

        # 3. Динамический расчет на базе реальной загрузки CPU (база 40°C + нагрузка)
        load = psutil.cpu_percent(interval=None)
        est_temp = 40.0 + (load * 0.4)
        return f"Температура CPU: {est_temp:.1f} °C (WSL эмуляция | Загрузка: {load}%)"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Главное окно")
        self.setGeometry(100, 100, 400, 150)

        self.worker: CpuTempWorker | None = None

        # Кнопка
        self.button = QPushButton("Старт", self)
        self.button.setCheckable(True)        
        self.button.toggled.connect(self.toggle_text)

        self.label_info = QLabel("Статус: остановлено", self)

        # Окно
        central = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.button)
        layout.addWidget(self.label_info)
        central.setLayout(layout)
        self.setCentralWidget(central)

    def toggle_text(self, checked: bool):
        if checked:
            self.button.setText("Стоп")
            self.label_info.setText("Получение данных...")

            self.worker = CpuTempWorker(interval=1.0)
            self.worker.temperature_updated.connect(self.update_temperature_label)
            self.worker.start()
        else:
            self.button.setText("Старт")

            if self.worker is not None:
                self.worker.stop()
                self.worker.wait()
                self.worker = None

            self.label_info.setText("Статус: остановлено")

    @Slot(str)
    def update_temperature_label(self, text: str):
        self.label_info.setText(text)

    def closeEvent(self, event):
        if self.worker is not None:
            self.worker.stop()
            self.worker.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())