# request_window.py

from PySide6.QtWidgets import QDialog, QGridLayout, QLabel

class RequestWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Requisição")
        self.setMinimumSize(400, 300)
        layout = QGridLayout()
        layout.addWidget(QLabel("Aqui vai a interface da requisição"))
        self.setLayout(layout)