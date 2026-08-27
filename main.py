import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Главное окно")
        self.setGeometry(100, 100, 400, 150)

        # Кнопка
        self.button = QPushButton("Старт", self)
        self.button.setCheckable(True)        
        self.button.toggled.connect(self.toggle_text)

        # Окно
        central = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.button)
        central.setLayout(layout)
        self.setCentralWidget(central)

    def toggle_text(self, checked: bool):
        if checked:
            self.button.setText("Старт")
        else:
            self.button.setText("Стоп")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())