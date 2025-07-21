# buy_window.py

from PySide6.QtWidgets import QDialog, QGridLayout, QLabel

class BuyWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Compras")
        self.setMinimumSize(400, 300)
        layout = QGridLayout()
        layout.addWidget(QLabel("Aqui vai a interface de compras"))
        self.setLayout(layout)