# views\request_window.py

from PySide6.QtWidgets import (
    QMainWindow, QApplication, QToolBar, QLineEdit, QTableWidget,
    QTableWidgetItem, QMessageBox, QGridLayout, QWidget, QLabel,
    QPushButton, QVBoxLayout, QHeaderView
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QEvent
import sys
import json
import os

# Diretório onde o script está
if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Diretório raiz do projeto (sobe um nível a partir do script)
# PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Caminhos absolutos para os arquivos na raiz do projeto
# REQUISICOES_JSON = os.path.join(PROJECT_ROOT, "requisicoes.json")

REQUISICOES_JSON = os.path.join(SCRIPT_DIR, "requisicoes.json")


class RequestWindow(QMainWindow):
    def __init__(self, parent=None, role=None):
        super().__init__(parent)
        self.role = role
        self.setWindowTitle("Requisições")
        self.resize(800, 500)

        self.request_id = None
        self.current_state = "idle"
        self.requests = self.load_requests()

        self.id_input = QLineEdit()
        self.status = QLineEdit()
        self.table = QTableWidget(0, 2)
        self.approve_button = QPushButton("Aprovar Requisição")
        self.repprove_button = QPushButton("Reprovar Requisição")

        self.init_ui()
        self.installEventFilter(self)  # Instalar filtro de eventos

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Barra de ferramentas
        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)
        self.create_toolbar()
        main_layout.addWidget(self.toolbar)

        # Campos da requisição
        form_layout = QGridLayout()
        form_layout.addWidget(QLabel("ID:"), 0, 0)
        self.id_input.setPlaceholderText("ID da requisição (digite para buscar)")
        form_layout.addWidget(self.id_input, 0, 1)

        form_layout.addWidget(QLabel("Status:"), 0, 2)
        self.status.setPlaceholderText("Status da requisição")
        self.status.setReadOnly(True)
        form_layout.addWidget(self.status, 0, 3)

        main_layout.addLayout(form_layout)

        # Tabela de itens
        self.table.setHorizontalHeaderLabels(["Item", "Quantidade"])  # Changed header
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) # type: ignore
        self.table.setEditTriggers(QTableWidget.NoEditTriggers) # type: ignore
        main_layout.addWidget(self.table)

        # Botão de aprovação e reprovação
        self.approve_button.clicked.connect(self.approve_request)
        self.approve_button.setEnabled(self.role == 0 or self.role == 2)
        form_layout.addWidget(self.approve_button, 0, 4)
        self.repprove_button.clicked.connect(self.repprove_request)
        self.repprove_button.setEnabled(self.role == 0 or self.role == 2)
        form_layout.addWidget(self.repprove_button, 0, 5)

    def create_toolbar(self):
        actions = [
            ("Criar", self.new_request),
            ("Salvar", self.save_request),
            ("Pesquisar", self.perform_search),
            ("Limpar", self.clear_interface),
            ("Sair", self.close)
        ]

        for text, slot in actions:
            action = QAction(text, self)
            action.triggered.connect(slot)
            self.toolbar.addAction(action)

    def eventFilter(self, obj, event):
        """Captura eventos de teclado para adicionar/remover linhas"""
        if event.type() == QEvent.KeyPress: # type: ignore
            # Enter adiciona nova linha
            if event.key() in (Qt.Key_Return, Qt.Key_Enter): # type: ignore
                self.add_row()
                return True
            # Ctrl+Delete remove linha
            elif event.key() == Qt.Key_Delete and (event.modifiers() & Qt.ControlModifier): # type: ignore
                self.remove_row()
                return True
        return super().eventFilter(obj, event)

    def new_request(self):
        """Inicia a criação de uma nova requisição"""
        self.current_state = "creating"
        self.table.setRowCount(0)
        self.table.setEditTriggers(QTableWidget.AllEditTriggers) # type: ignore
        self.request_id = self.get_new_id()
        self.id_input.setText(str(self.request_id))
        self.id_input.setReadOnly(True)
        self.status.setText("Pendente")
        self.add_row()  # Adiciona a primeira linha

    def add_row(self):
        """Adiciona uma nova linha à tabela"""
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(""))
        self.table.setItem(row, 1, QTableWidgetItem(""))
        # Focar na célula do nome da nova linha
        self.table.setCurrentCell(row, 0)

    def remove_row(self):
        """Remove a linha selecionada da tabela"""
        current_row = self.table.currentRow()
        # Não permite remover se só tiver uma linha
        if current_row >= 0 and self.table.rowCount() > 1:
            self.table.removeRow(current_row)

    def save_request(self):
        if not self.request_id:
            QMessageBox.warning(self, "Erro", "ID inválido.")
            return

        itens = []
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 0)
            qtd = self.table.item(row, 1)
            if name and qtd:
                if not name.text().strip():
                    QMessageBox.warning(self, "Erro", f"Item vazio na linha {row + 1}.")  # Changed text
                    return
                try:
                    qtd_value = int(qtd.text())
                except ValueError:
                    QMessageBox.warning(self, "Erro", f"Quantidade inválida na linha {row + 1}.")
                    return
                # Changed key to "item" for standardization
                itens.append({"item": name.text(), "quantidade": qtd_value})

        new_request = {
            "id": self.request_id,
            "itens": itens,
            "status": self.status.text()
        }

        existing_index = -1
        for i, req in enumerate(self.requests):
            if req["id"] == self.request_id:
                existing_index = i
                break

        if existing_index >= 0:
            self.requests[existing_index] = new_request
        else:
            self.requests.append(new_request)

        self.save_requests()
        QMessageBox.information(self, "Sucesso", "Requisição salva com sucesso.")
        self.clear_interface()

    def approve_request(self):
        """Aprova a requisição atual (apenas para Gerente do Setor)"""
        if self.status.text() != "Pendente":
            QMessageBox.warning(self, "Ação inválida",
                                "Apenas requisições pendentes podem ser aprovadas.")
            return

        self.status.setText("Aprovada")
        self.save_request()
        QMessageBox.information(self, "Aprovação",
                                "Requisição aprovada com sucesso!")

    def repprove_request(self):
        """Reprova a requisição atual (apenas para Gerente do Setor)"""
        if self.status.text() != "Pendente":
            QMessageBox.warning(self, "Ação inválida",
                                    "Apenas requisições pendentes podem ser reprovadas.")
            return

        self.status.setText("Reprovada")
        self.save_request()
        QMessageBox.information(self, "Reprovação",
                                    "Requisição reprovada com sucesso!")

    def get_new_id(self):
        if not self.requests:
            return 1
        return max(r["id"] for r in self.requests) + 1

    def perform_search(self):
        """Executa a busca usando o ID digitado no campo id_input"""
        text = self.id_input.text().strip()
        if not text:
            QMessageBox.warning(self, "Campo vazio", "Digite um ID para buscar")
            return

        try:
            req_id = int(text)
            self.search_request(req_id)
        except ValueError:
            QMessageBox.warning(self, "ID inválido", "O ID deve ser um número inteiro")

    def search_request(self, req_id):
        found_request = None
        for request in self.requests:
            if request["id"] == req_id:
                found_request = request
                break

        if not found_request:
            QMessageBox.information(self, "Requisição não encontrada!",
                                    f"A requisição {req_id} não foi cadastrada ainda")
            return

        self.current_state = "editing"
        self.request_id = req_id
        self.id_input.setText(str(req_id))
        self.id_input.setReadOnly(True)
        self.status.setText(found_request.get("status", "Pendente"))

        self.table.setRowCount(0)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers) # type: ignore

        for item in found_request.get("itens", []):
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Try "item" first, then "nome" for backward compatibility
            item_name = item.get("item") or item.get("nome", "")
            quantidade = item.get("quantidade") or item.get("Quantidade", 0)

            name_item = QTableWidgetItem(str(item_name))
            qtd_item = QTableWidgetItem(str(quantidade))

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, qtd_item)

    def clear_interface(self):
        """Reseta a interface para o estado inicial"""
        self.request_id = None
        self.id_input.clear()
        self.id_input.setReadOnly(False)
        self.status.clear()
        self.table.setRowCount(0)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers) # type: ignore
        self.current_state = "idle"
        self.requests = self.load_requests()

    def load_requests(self):
        """Carrega requisições do arquivo, cria se não existir"""
        if not os.path.exists(REQUISICOES_JSON):
            with open(REQUISICOES_JSON, "w", encoding="utf-8") as f:
                json.dump([], f, indent=4, ensure_ascii=False)
            return []

        try:
            with open(REQUISICOES_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
        except Exception as e:
            print(f"Erro ao carregar arquivo: {e}")
            return []

    def save_requests(self):
        """Salva as requisições no arquivo"""
        with open(REQUISICOES_JSON, "w", encoding="utf-8") as f:
            json.dump(self.requests, f, indent=4, ensure_ascii=False)

    def closeEvent(self, event):
        """Atualiza a lista de requisições ao fechar a janela"""
        self.requests = self.load_requests()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RequestWindow(role = 3)  # Teste como Gerente do Setor
    window.show()
    sys.exit(app.exec())