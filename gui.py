import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QGridLayout,
    QPushButton,
    QLineEdit,
    QScrollArea,
    QVBoxLayout
)
from PySide6.QtCore import Qt

# Constantes
INPUT_MAX_WIDTH = 500
HYPOTHESES_MAX_HEIGHT = 200

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Estética
        self.setWindowTitle("Assistente de Dedução Natural")
        self.resize(1200,900)

        # Distribuição dos componentes
        container = QWidget()
        self.setCentralWidget(container)

        grid = QGridLayout(container)
        grid.setAlignment(Qt.AlignCenter)
        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(3, 1)
        grid.setColumnStretch(1,1)
        grid.setColumnStretch(2,1)

        # Labels
        label_goal = QLabel("Fórmula a provar:")
        label_hyp = QLabel("Hipóteses: ")

        label_goal.setAlignment(Qt.AlignRight)
        label_hyp.setAlignment(Qt.AlignRight)

        # Entrada de fórmula
        goal_box = QLineEdit()
        goal_box.setMaximumWidth(INPUT_MAX_WIDTH)
        goal_box.setAlignment(Qt.AlignLeft)

        # Entrada de hipóteses
        hyp_area = QScrollArea()
        hyp_area.setWidgetResizable(True)
        hyp_area.setMaximumWidth(INPUT_MAX_WIDTH)
        hyp_area.setMaximumHeight(HYPOTHESES_MAX_HEIGHT)

        hyp_container = QWidget()
        hyp_list = QVBoxLayout(hyp_container)
        hyp_list.setAlignment(Qt.AlignTop)

        first_hyp = QLineEdit()
        hyp_list.addWidget(first_hyp)

        hyp_area.setWidget(hyp_container)

        # Grid
        grid.addWidget(label_goal, 0, 0)
        grid.addWidget(goal_box, 0, 1)
        grid.addWidget(label_hyp, 1, 0)
        grid.addWidget(hyp_area, 1, 1)




if __name__ == '__main__':
    app = QApplication()
    window = MainWindow()
    window.show()
    app.exec()