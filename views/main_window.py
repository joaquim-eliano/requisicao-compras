# views\main_window.py
import sys
import json
from PySide6.QtWidgets import (QMainWindow, QApplication, QDockWidget, QAbstractItemView,
QStyleFactory, QMessageBox, QTextEdit, QTableWidget, QTableWidgetItem)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self, role):
        super().__init__()
        self.setWindowTitle("Estoque")
        self.setMinimumSize(800, 600)
        self.role = role

        # menu
        menu_bar = self.menuBar()

        # janelas
        self.dock_wherehouse = QDockWidget("Estoque do Almoxarifado", self)
        self.dock_wherehouse.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea) # type: ignore
        self.table_wherehouse = QTableWidget()
        self.dock_wherehouse.setWidget(self.table_wherehouse)
        self.dock_wherehouse.setVisible(False)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_wherehouse) # type: ignore

        self.dock_sector = QDockWidget("Estoque do Setor", self)
        self.dock_sector.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)  # type: ignore
        self.table_sector = QTableWidget()
        self.dock_sector.setWidget(self.table_sector)
        self.dock_sector.setVisible(False)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_sector)  # type: ignore

        # menu arquivo
        arq = menu_bar.addMenu("Arquivos")
        about_action = QAction("Sobre", self)
        about_action.triggered.connect(self.show_about)
        leave_action = QAction("Sair", self)
        leave_action.triggered.connect(self.close)
        arq.addAction(about_action)
        arq.addSeparator()
        arq.addAction(leave_action)

        # menu estoque
        stock = menu_bar.addMenu("Estoque")
        self.stock_wherehouse = QAction("Estoque do Almoxarifado", self, checkable = True)
        self.stock_wherehouse.triggered.connect(self.toggle_wherehouse)
        self.stock_sector = QAction("Estoque do Setor", self, checkable = True)
        self.stock_sector.triggered.connect(self.toggle_sector)
        stock.addAction(self.stock_wherehouse)
        stock.addSeparator()
        stock.addAction(self.stock_sector)
        self.dock_wherehouse.visibilityChanged.connect(self.stock_wherehouse.setChecked)
        self.dock_sector.visibilityChanged.connect(self.stock_sector.setChecked)
        self.table_wherehouse.setEditTriggers(QAbstractItemView.NoEditTriggers)  # type: ignore
        self.table_sector.setEditTriggers(QAbstractItemView.NoEditTriggers)  # type: ignore

        self.configure_by_role()

        # menu movimentação
        movement = menu_bar.addMenu("Movimentação")
        stock_off = QAction("Baixa de Estoque", self)
        stock_off.triggered.connect(self.do_stock_off)
        request = QAction("Requisição", self)
        request.triggered.connect(self.do_request)
        movement.addAction(stock_off)
        movement.addAction(request)

        # menu relatórios
        rep = menu_bar.addMenu("Relatórios")


    def show_about(self):
        QMessageBox.information(self, "Sobre", "Sistema de Estoque v1.0\nDesenvolvido por Joaquim 😎")

    def toggle_wherehouse(self, checked):
        self.dock_wherehouse.setVisible(checked)
        self.stock_wherehouse.setChecked(checked)
        if checked:
            self.stock_sector.setChecked(False)  # <-- isso aqui desmarca o outro no menu
            self.dock_sector.setVisible(False)
            self.load_data("G:/Projetos/req/almoxarifado.json", self.table_wherehouse)

    def toggle_sector(self, checked):
        self.dock_sector.setVisible(checked)
        self.stock_sector.setChecked(checked)
        if checked:
            self.stock_wherehouse.setChecked(False)
            self.dock_wherehouse.setVisible(False)
            self.load_data("G:/Projetos/req/setor.json", self.table_sector)

    def do_stock_off(self):
        ...
    def do_request(self):
        ...

    def configure_by_role(self):
        if self.role in [0, 3]:  # Admin ou Comprador
            self.stock_wherehouse.setChecked(True)
            self.toggle_wherehouse(True)
        if self.role in [1, 2]:  # Funcionário ou Gerente
            self.stock_sector.setChecked(True)
            self.toggle_sector(True)

    def load_data(self, filename, widget):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(widget, QTextEdit):
                    widget.setText(json.dumps(data, indent=2, ensure_ascii=False))
                elif isinstance(widget, QTableWidget):
                    widget.clear()
                    widget.setColumnCount(len(data[0]))
                    widget.setHorizontalHeaderLabels(data[0].keys())
                    widget.setRowCount(len(data))
                    for row, item in enumerate(data):
                        for col, key in enumerate(item):
                            widget.setItem(row, col, QTableWidgetItem(str(item[key])))
                    widget.resizeColumnsToContents()
        except Exception as e:
            QMessageBox.warning(self, "Erro ao carregar", str(e))

    @staticmethod
    def create_table_widget(self, dados):
        table = QTableWidget()
        table.setColumnCount(len(dados[0]))
        table.setHorizontalHeaderLabels(dados[0].keys())
        table.setRowCount(len(dados))

        for row, item in enumerate(dados):
            for col, key in enumerate(item):
                table.setItem(row, col, QTableWidgetItem(str(item[key])))

        table.resizeColumnsToContents()
        return table




if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow(role = 0)
    window.show()
    style = QStyleFactory.create('Windows')
    QApplication.setStyle(style)
    QApplication.setPalette(style.standardPalette())
    sys.exit(app.exec())