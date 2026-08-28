import sys
import time
import psutil
import shutil
import re
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
        #Попытка запросить температуру у хостовой Windows через WSL
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

        #Стандартная попытка Linux-датчиков 
        try:
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    for entries in temps.values():
                        if entries:
                            return f"Температура CPU: {entries[0].current:.1f} °C"
        except Exception:
            pass

        #Динамический расчет на базе реальной загрузки CPU 
        load = psutil.cpu_percent(interval=None)
        est_temp = 40.0 + (load * 0.4)
        return f"Температура CPU: {est_temp:.1f} °C (WSL эмуляция | Загрузка: {load}%)"

class PingWorker(QThread):
    #Сигнал для передачи строки с температурой сетевой доступности и RTT
    ping_updated = Signal(str)

    def __init__(self, host: str = "8.8.8.8", interval: float = 2.0, parent=None):
        super().__init__(parent)
        self.host = host
        self.interval = interval
        self._is_running = True

    def run(self):
        while self._is_running:
            ping_str = self._ping_host()
            self.ping_updated.emit(ping_str)

            slept = 0.0
            while self._is_running and slept < self.interval:
                time.sleep(0.1)
                slept += 0.1

    def stop(self):
        self._is_running = False

    def _ping_host(self) -> str:
        # Определение флага количества пакетов (-n для Win32, -c для Linux/WSL)
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
                output = proc.stdout
                # Поиск времени RTT 
                match = re.search(r"time[=<](\d+(?:\.\d+)?)\s*ms", output, re.IGNORECASE)
                if match:
                    rtt = match.group(1)
                    return f"Ping ({self.host}): Доступен (RTT = {rtt} мс)"
                return f"Ping ({self.host}): Доступен"
            else:
                return f"Ping ({self.host}): Недоступен (Превышен таймаут)"
        except subprocess.TimeoutExpired:
            return f"Ping ({self.host}): Недоступен (Timeout)"
        except Exception as e:
            return f"Ping ({self.host}): Ошибка выполнения ({e})"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Главное окно")
        self.setGeometry(100, 100, 480, 200)

        # Список для управления всеми активными потоками
        self.workers: list[QThread] = []

        # Кнопка
        self.button = QPushButton("Старт", self)
        self.button.setCheckable(True)
        self.button.toggled.connect(self.toggle_text)

        # Строки вывода информации
        self.label_cpu = QLabel("Строка 1 (CPU): Остановлен", self)
        self.label_ping = QLabel("Строка 2 (Ping): Остановлен", self)

        # Окно и компоновка
        central = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.button)
        layout.addWidget(self.label_cpu)
        layout.addWidget(self.label_ping)
        central.setLayout(layout)
        self.setCentralWidget(central)

    def toggle_text(self, checked: bool):
        if checked:
            self.button.setText("Стоп")
            self.label_cpu.setText("Строка 1 (CPU): Получение данных...")
            self.label_ping.setText("Строка 2 (Ping): Пинг узла...")

            # 1. Создание потока CPU
            cpu_worker = CpuTempWorker(interval=1.0)
            cpu_worker.temperature_updated.connect(self.update_cpu_label)
            self.workers.append(cpu_worker)

            # 2. Создание потока Ping (8.8.8.8)
            ping_worker = PingWorker(host="8.8.8.8", interval=2.0)
            ping_worker.ping_updated.connect(self.update_ping_label)
            self.workers.append(ping_worker)

            # Запуск всех потоков
            for worker in self.workers:
                worker.start()
        else:
            self.button.setText("Старт")
            self._stop_all_workers()
            self.label_cpu.setText("Строка 1 (CPU): Остановлен")
            self.label_ping.setText("Строка 2 (Ping): Остановлен")

    def _stop_all_workers(self):
        for worker in self.workers:
            if hasattr(worker, "stop"):
                worker.stop()
            worker.quit()
            worker.wait()
        self.workers.clear()

    @Slot(str)
    def update_cpu_label(self, text: str):
        self.label_cpu.setText(f"Строка 1: {text}")

    @Slot(str)
    def update_ping_label(self, text: str):
        self.label_ping.setText(f"Строка 2: {text}")

    def closeEvent(self, event):
        self._stop_all_workers()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())