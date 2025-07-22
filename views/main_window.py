import json
from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QAbstractItemView, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QEvent

from views.buy_window import BuyWindow
from views.request_window import RequestWindow
from views.stock_off_window import StockOffWindow
from views.movement import MovementWindow  # New import


class MainWindow(QMainWindow):
    def __init__(self, role):
        super().__init__()
        self.role = role
        self.setup_ui()
        self.configure_by_role()

    def setup_ui(self):
        self.setWindowTitle("Estoque")
        self.setMinimumSize(900, 500)

        # Criar menus
        self.create_menus()

        # Configurar docks
        self.setup_docks()

    def create_menus(self):
        menu_bar = self.menuBar()

        # Menu Arquivo
        file_menu = menu_bar.addMenu("Arquivos")
        file_menu.addAction(self.create_action("Sobre", self.show_about))
        file_menu.addAction(self.create_action("Sair", self.close))

        # Menu Estoque
        stock_menu = menu_bar.addMenu("Estoque")
        self.stock_wherehouse_action = self.create_action(
            "Estoque do Almoxarifado", self.toggle_wherehouse, checkable=True
        )
        self.stock_sector_action = self.create_action(
            "Estoque do Setor", self.toggle_sector, checkable=True
        )
        stock_menu.addActions([self.stock_wherehouse_action, self.stock_sector_action])

        # Menu Movimentação
        move_menu = menu_bar.addMenu("Movimentação")
        move_menu.addAction(self.create_action("Baixa de Estoque",
                                               lambda: self.permission("stock_off")))
        move_menu.addAction(self.create_action("Requisição",
                                               lambda: self.permission("request")))
        # New movement action
        move_menu.addAction(self.create_action("Movimentar",
                                               lambda: self.permission("movement")))

        # Menu Compras
        buy_menu = menu_bar.addMenu("Compras")
        buy_menu.addAction(self.create_action("Comprar",
                                              lambda: self.permission("buy")))

        # Menu Relatórios
        menu_bar.addMenu("Relatórios")

    def create_action(self, text, slot, **kwargs):
        action = QAction(text, self, **kwargs)
        action.triggered.connect(slot)
        return action

    def setup_docks(self):
        # Dock Almoxarifado
        self.dock_wherehouse = QDockWidget("Estoque do Almoxarifado", self)
        self.table_wherehouse = QTableWidget()
        self.table_wherehouse.setEditTriggers(QAbstractItemView.NoEditTriggers)  # type: ignore
        self.dock_wherehouse.setWidget(self.table_wherehouse)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_wherehouse)  # type: ignore
        self.dock_wherehouse.setVisible(False)
        self.table_wherehouse.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # type: ignore
        self.dock_wherehouse.visibilityChanged.connect(
            lambda visible: self.stock_wherehouse_action.setChecked(visible)
        )

        # Dock Setor
        self.dock_sector = QDockWidget("Estoque do Setor", self)
        self.table_sector = QTableWidget()
        self.table_sector.setEditTriggers(QAbstractItemView.NoEditTriggers)  # type: ignore
        self.table_sector.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # type: ignore
        self.dock_sector.setWidget(self.table_sector)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_sector)  # type: ignore
        self.dock_sector.setVisible(False)
        self.dock_sector.visibilityChanged.connect(
            lambda visible: self.stock_sector_action.setChecked(visible)
        )

    def show_about(self):
        QMessageBox.information(self, "Sobre",
                                "Sistema de Estoque v1.0\nDesenvolvido por Joaquim 😎")

    def toggle_wherehouse(self, checked):
        self.dock_wherehouse.setVisible(checked)
        if checked:
            self.stock_sector_action.setChecked(False)
            self.dock_sector.setVisible(False)
            self.load_data("almoxarifado.json", self.table_wherehouse)
            self.table_wherehouse.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # type: ignore

    def toggle_sector(self, checked):
        self.dock_sector.setVisible(checked)
        if checked:
            self.stock_wherehouse_action.setChecked(False)
            self.dock_wherehouse.setVisible(False)
            self.load_data("setor.json", self.table_sector)
            self.table_sector.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # type: ignore

    def permission(self, action: str):
        # Updated permissions mapping
        permissions = {
            "request": (0, 1, 2),
            "stock_off": (0, 1, 2),
            "buy": (0, 3),
            "movement": (0, 1, 2, 3)  # Everyone can access
        }

        # Updated action windows mapping
        action_windows = {
            "request": lambda: RequestWindow(parent=self, role=self.role).show(),
            "stock_off": lambda: StockOffWindow(self).exec(),
            "buy": lambda: BuyWindow(self).exec(),
            "movement": lambda: MovementWindow(self, self.role).exec()  # New window
        }

        if self.role in permissions[action]:
            # Execute window and refresh stocks when it closes
            window = action_windows[action]()
            if hasattr(window, 'finished'):
                window.finished.connect(self.refresh_stocks)
        else:
            action_name = action.replace("_", " ").title()
            QMessageBox.warning(self, "Permissão negada",
                                f"Você não pode acessar {action_name}.")

    def configure_by_role(self):
        if self.role in (0, 3):  # Admin ou Comprador
            self.toggle_wherehouse(True)
        elif self.role in (1, 2):  # Funcionário ou Gerente
            self.toggle_sector(True)

    def load_data(self, filename, widget):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

                # Limpar e configurar tabela
                widget.clear()
                widget.setColumnCount(4)
                headers = ["Item", "Quantidade", "Valor Unitário", "Valor Total"]
                widget.setHorizontalHeaderLabels(headers)
                widget.setRowCount(len(data))

                # Preencher dados
                for row, item in enumerate(data):
                    widget.setItem(row, 0, QTableWidgetItem(str(item.get('item', ''))))
                    widget.setItem(row, 1, QTableWidgetItem(str(item.get('quantidade', ''))))
                    widget.setItem(row, 2, QTableWidgetItem(str(item.get('valor_unitario', ''))))
                    widget.setItem(row, 3, QTableWidgetItem(str(item.get('valor_total', ''))))

                # Ajustar colunas
                widget.resizeColumnsToContents()

        except Exception as e:
            QMessageBox.warning(self, "Erro ao carregar", str(e))

    def refresh_stocks(self):
        """Refresh visible stock docks when child windows close"""
        if self.dock_wherehouse.isVisible():
            self.load_data("almoxarifado.json", self.table_wherehouse)
        if self.dock_sector.isVisible():
            self.load_data("setor.json", self.table_sector)

    def closeEvent(self, event):
        """Refresh stocks when main window closes"""
        self.refresh_stocks()
        super().closeEvent(event)


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication

    app = QApplication([])
    window = MainWindow(role=0)
    window.show()
    app.exec()