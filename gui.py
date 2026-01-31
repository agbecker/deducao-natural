from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from PySide6.QtCore import Qt

class MainWindows(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Hello World')

        container = QWidget()
        self.setCentralWidget(container)

        layout = QGridLayout(container)

        label1 = QLabel('One')
        label1.setAlignment(Qt.AlignCenter)

        label2 = QLabel('Two')
        label2.setAlignment(Qt.AlignCenter)    

        label3 = QLabel('Trhee')
        label3.setAlignment(Qt.AlignCenter)    

        layout.addWidget(label1, 0, 0)
        layout.addWidget(label2, 1, 1)
        layout.addWidget(label3, 2, 0)

app = QApplication()
window = MainWindows()
window.show()

app.exec()