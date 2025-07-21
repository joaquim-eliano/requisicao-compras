# stock_off_window.py

from PySide6.QtWidgets import QDialog, QGridLayout, QLabel

class StockOffWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Baixa de Estoque")
        self.setMinimumSize(400, 300)
        layout = QGridLayout()
        layout.addWidget(QLabel("Aqui vai a interface de baixa de estoque"))
        self.setLayout(layout)
