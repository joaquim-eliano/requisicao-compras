# views\main_window.py

import json, sys, os, locale
from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QAbstractItemView, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, Signal

from views.buy_window import BuyWindow
from views.request_window import RequestWindow
from views.stock_off_window import StockOffWindow
from views.movement import MovementWindow
from views.login_window import LoginWindow
from views.report_window import ReportWindow

# Configure Brazilian locale for currency formatting
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')  # Fallback for Windows


# Helper function to format currency
def format_currency(value):
    """Formata um valor como moeda brasileira"""
    try:
        return locale.currency(value, grouping=True, symbol=True)
    except (TypeError, ValueError):
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# Diretório onde o script está
if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Diretório raiz do projeto (sobe um nível a partir do script)
# PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Caminhos absolutos para os arquivos na raiz do projeto
# ESTOQUE_ALMOX_JSON = os.path.join(PROJECT_ROOT, "almoxarifado.json")
# ESTOQUE_SETOR_JSON = os.path.join(PROJECT_ROOT, "setor.json")
ESTOQUE_ALMOX_JSON = os.path.join(SCRIPT_DIR, "almoxarifado.json")
ESTOQUE_SETOR_JSON = os.path.join(SCRIPT_DIR, "setor.json")



class MainWindow(QMainWindow):
    logout_requested = Signal()  # Sinal para solicitar logout

    def __init__(self, role, username, name):
        super().__init__()
        self.role = role
        self.username = username
        self.name = name
        self.setup_ui()
        self.configure_by_role()

        # Verificar notificações após a janela ser mostrada
        self.showEvent = self.on_show_event

    def on_show_event(self, event):
        """Evento chamado quando a janela é mostrada"""
        super().showEvent(event)
        self.check_purchase_notifications()

    def check_purchase_notifications(self):
        """Verifica e mostra notificações de compras pendentes"""
        # Apenas para funcionários (roles 1 e 2)
        if self.role not in (1, 2):
            return

        # Carregar requisições compradas não visualizadas
        purchased_requests = self.load_purchased_requests()
        if not purchased_requests:
            return

        # Construir mensagem
        message = "<b>Requisições compradas aguardando envio:</b><br><br>"
        req_ids = []

        for req in purchased_requests:
            if not req.get("viewed", False):
                req_ids.append(str(req["id"]))

        if not req_ids:
            return

        message += ", ".join(req_ids)

        # Mostrar pop-up
        QMessageBox.information(self, "Novas Requisições Compradas", message)

        # Marcar como visualizadas
        self.mark_requests_as_viewed(req_ids)

    def load_purchased_requests(self):
        """Carrega requisições compradas do arquivo"""
        try:
            # Caminho para o arquivo de requisições compradas
            purchased_file = os.path.join(PROJECT_ROOT, "requisicoes_compradas.json")

            if os.path.exists(purchased_file):
                with open(purchased_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar requisições compradas: {e}")
        return []

    def mark_requests_as_viewed(self, req_ids):
        """Marca as requisições como visualizadas"""
        try:
            purchased_file = os.path.join(PROJECT_ROOT, "requisicoes_compradas.json")

            if os.path.exists(purchased_file):
                with open(purchased_file, "r", encoding="utf-8") as f:
                    purchased_requests = json.load(f)

                # Atualizar o status de visualização
                for req in purchased_requests:
                    if str(req["id"]) in req_ids:
                        req["viewed"] = True

                # Salvar de volta
                with open(purchased_file, "w", encoding="utf-8") as f:
                    json.dump(purchased_requests, f, indent=4, ensure_ascii=False)

        except Exception as e:
            print(f"Erro ao marcar requisições como visualizadas: {e}")

    def setup_ui(self):
        self.setWindowTitle("Estoque")
        self.setMinimumSize(900, 500)

        # Criar menus
        self.create_menus()

        # Configurar docks
        self.setup_docks()

        # Barra de status para notificações
        self.status_bar = self.statusBar()
        self.status_bar.showMessage(f"Bem-vindo, {self.name}!")

    def create_menus(self):
        menu_bar = self.menuBar()

        # Menu Arquivo
        file_menu = menu_bar.addMenu("Arquivos")
        file_menu.addAction(self.create_action("Sobre", self.show_about))
        file_menu.addAction(self.create_action("Logout", self.logout))  # Novo item de logout
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
        move_menu.addAction(self.create_action("Movimentar",
                                               lambda: self.permission("movement")))

        # Menu Compras
        buy_menu = menu_bar.addMenu("Compras")
        buy_menu.addAction(self.create_action("Comprar",
                                              lambda: self.permission("buy")))

        # Menu Relatórios
        reports_menu = menu_bar.addMenu("Relatórios")
        reports_menu.addAction(self.create_action("Gerar Relatório", self.show_report_window))

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
            self.load_data(ESTOQUE_ALMOX_JSON, self.table_wherehouse)
            self.table_wherehouse.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # type: ignore

    def toggle_sector(self, checked):
        self.dock_sector.setVisible(checked)
        if checked:
            self.stock_wherehouse_action.setChecked(False)
            self.dock_wherehouse.setVisible(False)
            self.load_data(ESTOQUE_SETOR_JSON, self.table_sector)
            self.table_sector.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # type: ignore

    def permission(self, action: str):
        permissions = {
            "request": (0, 1, 2),
            "stock_off": (0, 1, 2),
            "buy": (0, 3),
            "movement": (0, 1, 2, 3)
        }

        action_windows = {
            "request": lambda: RequestWindow(parent=self, role=self.role).show(),
            "stock_off": lambda: StockOffWindow(self).exec(),
            "buy": lambda: self.open_buy_window(),
            "movement": lambda: MovementWindow(self, self.role).exec()
        }

        if self.role in permissions[action]:
            window = action_windows[action]()
            if hasattr(window, 'finished'):
                window.finished.connect(self.refresh_stocks) # type: ignore
        else:
            action_name = action.replace("_", " ").title()
            QMessageBox.warning(self, "Permissão negada",
                                f"Você não pode acessar {action_name}.")

    def open_buy_window(self):
        """Abre janela de compra e conecta sinais"""
        buy_window = BuyWindow(self)
        buy_window.purchase_completed.connect(self.notify_purchase)
        buy_window.exec()
        return buy_window

    def logout(self):
        """Realiza logout e fecha todas as janelas"""
        self.logout_requested.emit()
        self.close()

    def notify_purchase(self, req_id):
        message = f"Requisição {req_id} comprada! Aguardando envio."

        # Adicionar notificação persistente
        self.notifications.append(message)
        self.update_notifications()

        # Mostrar mensagem imediatamente na barra de status
        self.status_bar.showMessage(message)

    def update_notifications(self):
        """Atualiza área de notificações"""
        notification_text = "\n".join(self.notifications)
        self.status_bar.showMessage(notification_text)

    def show_report_window(self):
        report_window = ReportWindow(self)
        report_window.exec()

    def configure_by_role(self):
        if self.role in (0, 3):  # Admin ou Comprador
            self.toggle_wherehouse(True)
        elif self.role in (1, 2):  # Funcionário ou Gerente
            self.toggle_sector(True)

        # Inicializar lista de notificações
        self.notifications = []

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

            # Preencher dados com formatação de moeda
            for row, item in enumerate(data):
                # Item
                widget.setItem(row, 0, QTableWidgetItem(str(item.get('item', ''))))

                # Quantidade
                qtd = item.get('quantidade', 0)
                widget.setItem(row, 1, QTableWidgetItem(str(qtd)))

                # Valor Unitário (formatado como moeda)
                unit_value = item.get('valor_unitario', 0.0)
                unit_value_str = format_currency(unit_value)
                widget.setItem(row, 2, QTableWidgetItem(unit_value_str))

                # Valor Total (formatado como moeda)
                total_value = item.get('valor_total', 0.0)
                # Se não existir, calcula: quantidade * valor unitário
                if total_value == 0 and qtd != 0 and unit_value != 0:
                    total_value = qtd * unit_value
                total_value_str = format_currency(total_value)
                widget.setItem(row, 3, QTableWidgetItem(total_value_str))

            # Ajustar colunas
            widget.resizeColumnsToContents()

        except FileNotFoundError:
            QMessageBox.warning(self, "Arquivo não encontrado",
                                f"O arquivo {filename} não foi encontrado.")
        except json.JSONDecodeError:
            QMessageBox.warning(self, "Erro de leitura",
                                f"O arquivo {filename} está corrompido ou em formato inválido.")
        except Exception as e:
            QMessageBox.warning(self, "Erro ao carregar", f"{str(e)}")

    def refresh_stocks(self):
        """Refresh visible stock docks when child windows close"""
        if self.dock_wherehouse.isVisible():
            self.load_data(ESTOQUE_ALMOX_JSON, self.table_wherehouse)
        if self.dock_sector.isVisible():
            self.load_data(ESTOQUE_SETOR_JSON, self.table_sector)

    def closeEvent(self, event):
        """Refresh stocks when main window closes"""
        self.refresh_stocks()
        super().closeEvent(event)

if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication

    app = QApplication([])

    # Simular login
    login_window = LoginWindow()
    if login_window.exec() == QDialog.Accepted and login_window.valid_login: # type: ignore
        window = MainWindow(role=login_window.role, username=login_window.username, name=login_window.name)
        window.show()
        app.exec()