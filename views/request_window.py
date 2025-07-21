# request_window.py

from PySide6.QtWidgets import (
    QMainWindow, QApplication, QToolBar, QLineEdit, QTableWidget,
    QTableWidgetItem, QMessageBox, QGridLayout, QWidget, QLabel
)
from PySide6.QtGui import QIcon, QAction
import json
import os

ARCHIVE_JSON = "requisicoes.json"


class RequestWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Requisições")
        self.resize(500, 400)

        self.request_id = None
        self.current_state = "idle"  # Estados: "idle", "creating", "editing"

        self.id_input = QLineEdit()
        self.status = QLineEdit()
        self.table = QTableWidget(0, 2)
        self.init_ui()

    def init_ui(self):
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        new_action = QAction(QIcon(), "Criar", self)
        new_action.triggered.connect(self.new_request)
        toolbar.addAction(new_action)

        save_action = QAction(QIcon(), "Salvar", self)
        save_action.triggered.connect(self.save_request)
        toolbar.addAction(save_action)

        search_action = QAction(QIcon(), "Pesquisar", self)
        search_action.triggered.connect(self.perform_search)
        toolbar.addAction(search_action)

        # Adicionando ação para limpar
        clear_action = QAction(QIcon(), "Limpar", self)
        clear_action.triggered.connect(self.clear_interface)
        toolbar.addAction(clear_action)

        leave_action = QAction(QIcon(), "Sair", self)
        leave_action.triggered.connect(self.close)
        toolbar.addAction(leave_action)

        # Campos da Requisição
        self.id_input.setPlaceholderText("ID da requisição (digite para buscar)")
        self.status.setPlaceholderText("Status da requisição")
        self.status.setReadOnly(True)

        # Tabela de Itens
        self.table.setHorizontalHeaderLabels(["Nome do item", "Quantidade"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # type: ignore

        layout = QGridLayout()
        layout.addWidget(QLabel("ID:"), 0, 0)
        layout.addWidget(self.id_input, 0, 1)
        layout.addWidget(QLabel("Status:"), 0, 2)
        layout.addWidget(self.status, 0, 3)
        layout.addWidget(self.table, 1, 0, 1, 4)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def new_request(self):
        """Inicia a criação de uma nova requisição"""
        self.current_state = "creating"
        self.table.setRowCount(0)
        self.table.setEditTriggers(QTableWidget.AllEditTriggers)  # type: ignore
        self.request_id = self.get_new_id()
        self.id_input.setText(str(self.request_id))
        self.id_input.setReadOnly(True)  # Impede edição durante criação/edição
        self.status.setText("Pendente")
        self.add_row()

    def save_request(self):
        if not self.request_id:
            QMessageBox.warning(self, "Erro", "ID inválido.")
            return

        itens = []
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 0)
            qtd = self.table.item(row, 1)
            if name and qtd:
                # Validação de nome
                if not name.text().strip():
                    QMessageBox.warning(self, "Erro", f"Nome vazio na linha {row + 1}.")
                    return
                try:
                    qtd_value = int(qtd.text())
                except ValueError:
                    QMessageBox.warning(self, "Erro", f"Quantidade inválida na linha {row + 1}.")
                    return
                itens.append({"nome": name.text(), "quantidade": qtd_value})

        new_request = {
            "id": self.request_id,
            "itens": itens,
            "status": self.status.text()
        }

        requests = self.load_file()

        # Verificar se é edição ou nova
        existing_index = -1
        for i, req in enumerate(requests):
            if req["id"] == self.request_id:
                existing_index = i
                break

        if existing_index >= 0:
            requests[existing_index] = new_request
        else:
            requests.append(new_request)

        self.save_file(requests)

        QMessageBox.information(self, "Sucesso", "Requisição salva com sucesso.")
        self.clear_interface()  # Limpa após salvar

    def add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(""))
        self.table.setItem(row, 1, QTableWidgetItem(""))

    def get_new_id(self):
        requests = self.load_file()
        if not requests:
            return 1
        return max(r["id"] for r in requests) + 1

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
        requests = self.load_file()
        found_request = None
        for request in requests:
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
        self.id_input.setReadOnly(True)  # Torna somente leitura durante edição
        self.status.setText(found_request.get("status", "Pendente"))

        # Limpar tabela antes de preencher
        self.table.setRowCount(0)
        self.table.setEditTriggers(QTableWidget.AllEditTriggers)  # type: ignore

        # Compatibilidade com maiúsculas/minúsculas
        for item in found_request.get("itens", []):
            row = self.table.rowCount()
            self.table.insertRow(row)

            name = item.get("nome") or item.get("Nome", "")
            quantidade = item.get("quantidade") or item.get("Quantidade", 0)

            name_item = QTableWidgetItem(str(name))
            qtd_item = QTableWidgetItem(str(quantidade))

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, qtd_item)

        QMessageBox.information(self, "Requisição Encontrada",
                                f"Requisição {req_id} carregada com sucesso!")

    def clear_interface(self):
        """Reseta a interface para o estado inicial"""
        self.request_id = None
        self.id_input.clear()
        self.id_input.setReadOnly(False)  # Permite editar para nova busca
        self.status.clear()
        self.table.setRowCount(0)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # type: ignore
        self.current_state = "idle"

    @staticmethod
    def load_file():
        if not os.path.exists(ARCHIVE_JSON):
            return []
        try:
            with open(ARCHIVE_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
        except Exception as e:
            print(f"Erro ao carregar arquivo: {e}")
            return []

    @staticmethod
    def save_file(data):
        with open(ARCHIVE_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = RequestWindow()
    window.show()
    sys.exit(app.exec())