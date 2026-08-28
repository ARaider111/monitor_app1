from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QVBoxLayout,
    QWidget, QLabel, QFrame, )
from workers import ( BaseWorker, CpuTempWorker, PingWorker, FanWorker, RamWorker, 
DiskWorker, CpuUsageWorker, NetworkTrafficWorker, RandomDataWorker )


class MainWindow(QMainWindow):
    TOTAL_ROWS = 10

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Главное окно")
        self.setGeometry(100, 100, 520, 420)

        self.workers: list[BaseWorker] = []
        self.labels: list[QLabel] = []

        self._init_ui()

    def _init_ui(self):
        central = QWidget()
        layout = QVBoxLayout(central)

        # Кнопка переключения
        self.button = QPushButton("Старт", self)
        self.button.setCheckable(True)
        self.button.setFixedHeight(36)
        self.button.toggled.connect(self.toggle_state)
        layout.addWidget(self.button)

        # Создание строк вывода
        for i in range(self.TOTAL_ROWS):
            lbl = QLabel("Остановлен", self)
            lbl.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
            lbl.setStyleSheet("padding: 3px;")
            self.labels.append(lbl)
            layout.addWidget(lbl)

        self.setCentralWidget(central)

    def toggle_state(self, checked: bool):
        if checked:
            self.button.setText("Стоп")
            self._start_all_workers()
        else:
            self.button.setText("Старт")
            self._stop_all_workers()

    def _start_all_workers(self):
        # Сброс текста меток
        for i, lbl in enumerate(self.labels):
            lbl.setText("Запуск...")

        # Инициализация источников данных
        self.workers = [
            CpuTempWorker(row_index=0, interval=1.0),
            PingWorker(row_index=1, host="8.8.8.8", interval=2.0),
            FanWorker(row_index=2, interval=1.5),
            RamWorker(row_index=3, interval=1.0),
            DiskWorker(row_index=4, interval=1.0),
            CpuUsageWorker(row_index=5, interval=1.0),
            NetworkTrafficWorker(row_index=6, interval=1.0),
            RandomDataWorker(row_index=7, interval=3.0)
        ]

        # Подключение сигналов и запуск
        for worker in self.workers:
            worker.data_updated.connect(self.update_row_data)
            worker.start()

    def _stop_all_workers(self):
        for worker in self.workers:
            try:
                worker.data_updated.disconnect(self.update_row_data)
            except Exception:
                pass
            worker.stop()

        for worker in self.workers:
            worker.quit()
            worker.wait()
            
        self.workers.clear()

        for lbl in self.labels:
            lbl.setText("Остановлен")

    @Slot(int, str)
    def update_row_data(self, row_index: int, text: str):
        if 0 <= row_index < len(self.labels):
            self.labels[row_index].setText(text)

    def closeEvent(self, event):
        self._stop_all_workers()
        event.accept()