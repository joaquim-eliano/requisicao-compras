# buy_window.py

from PySide6.QtWidgets import (
    QDialog, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QPushButton, QMessageBox

)
from PySide6.QtCore import Qt, QEvent
import json
import os
import sys

# Obter o diretório do script (igual ao anterior)
if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

REQUISICOES_JSON = os.path.join(SCRIPT_DIR, "requisicoes.json")
ESTOQUE_JSON = os.path.join(SCRIPT_DIR, "estoque.json")


class BuyWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Compras")
        self.resize(800, 600)

        # Layout Vertical
        main_layout = QGridLayout(self)

                # Tabela de requisições
        self.requests_table = QTableWidget()
        self.requests_table.setColumnCount(2)
        self.requests_table.setHorizontalHeaderLabels(["ID Requisição", "Status"])
        self.requests_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) # type: ignore
        self.requests_table.setSelectionBehavior(QAbstractItemView.SelectRows) # type: ignore
        self.requests_table.setSelectionMode(QAbstractItemView.SingleSelection) # type: ignore
        self.requests_table.itemSelectionChanged.connect(self.load_request_items)
        self.requests_table.setEditTriggers(QTableWidget.NoEditTriggers)  # type: ignore

        # Tabela de itens
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(2)
        self.items_table.setHorizontalHeaderLabels(["Item", "Quantidade"])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) # type: ignore
        self.items_table.setEditTriggers(QTableWidget.NoEditTriggers) # type: ignore

        # Adicionar tabelas ao divisor
        main_layout.addWidget(self.requests_table, 0, 0, 3, 3)
        main_layout.addWidget(self.items_table, 3, 0, 1, 3)

        # Botões
        self.buy_button = QPushButton("Registrar Compra")
        self.buy_button.clicked.connect(self.register_purchase)
        main_layout.addWidget(self.buy_button, 0, 4, 1, 1)

        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.close)
        main_layout.addWidget(close_button, 1, 4, 1, 1)


        # Carregar dados
        self.load_requests()

        # Atalhos de teclado
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        """Atalhos de teclado para adicionar/remover itens"""
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

    def load_requests(self):
        """Carrega requisições aprovadas"""
        try:
            with open(REQUISICOES_JSON, "r", encoding="utf-8") as f:
                requests = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            requests = []

        # Filtrar apenas requisições aprovadas
        approved_requests = [req for req in requests if req.get("status") == "Aprovada"]

        self.requests_table.setRowCount(len(approved_requests))
        for row, req in enumerate(approved_requests):
            self.requests_table.setItem(row, 0, QTableWidgetItem(str(req["id"])))
            self.requests_table.setItem(row, 1, QTableWidgetItem(req["status"]))

    def load_request_items(self):
        """Carrega itens da requisição selecionada"""
        selected_row = self.requests_table.currentRow()
        if selected_row < 0:
            return

        req_id = int(self.requests_table.item(selected_row, 0).text())

        try:
            with open(REQUISICOES_JSON, "r", encoding="utf-8") as f:
                requests = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            requests = []

        # Encontrar a requisição selecionada
        selected_request = None
        for req in requests:
            if req["id"] == req_id:
                selected_request = req
                break

        if not selected_request:
            return

        # Preencher tabela de itens
        items = selected_request.get("itens", [])
        self.items_table.setRowCount(len(items))
        for row, item in enumerate(items):
            self.items_table.setItem(row, 0, QTableWidgetItem(item["nome"]))
            self.items_table.setItem(row, 1, QTableWidgetItem(str(item["quantidade"])))

    def add_row(self):
        """Adiciona nova linha na tabela de itens"""
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        self.items_table.setItem(row, 0, QTableWidgetItem(""))
        self.items_table.setItem(row, 1, QTableWidgetItem(""))

    def remove_row(self):
        """Remove linha selecionada na tabela de itens"""
        current_row = self.items_table.currentRow()
        if current_row >= 0:
            self.items_table.removeRow(current_row)

    def register_purchase(self):
        """Registra a compra no estoque"""
        selected_row = self.requests_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Nenhuma requisição selecionada",
                                "Selecione uma requisição para comprar.")
            return

        req_id = int(self.requests_table.item(selected_row, 0).text())

        # Processar itens comprados
        purchased_items = []
        for row in range(self.items_table.rowCount()):
            name_item = self.items_table.item(row, 0)
            qtd_item = self.items_table.item(row, 1)

            if name_item and qtd_item:
                name = name_item.text().strip()
                try:
                    qtd = int(qtd_item.text())
                except ValueError:
                    continue

                if name and qtd > 0:
                    purchased_items.append({"nome": name, "quantidade": qtd})

        if not purchased_items:
            QMessageBox.warning(self, "Nenhum item comprado",
                                "Adicione itens à compra antes de registrar.")
            return

        # Atualizar estoque
        try:
            # Carregar estoque atual
            if os.path.exists(ESTOQUE_JSON):
                with open(ESTOQUE_JSON, "r", encoding="utf-8") as f:
                    estoque = json.load(f)
            else:
                estoque = []

            # Atualizar itens
            for item in purchased_items:
                found = False
                for e in estoque:
                    if e["nome"] == item["nome"]:
                        e["quantidade"] += item["quantidade"]
                        found = True
                        break

                if not found:
                    estoque.append({
                        "nome": item["nome"],
                        "quantidade": item["quantidade"],
                        "valor_unitario": 0.0  # Será atualizado posteriormente
                    })

            # Salvar estoque atualizado
            with open(ESTOQUE_JSON, "w", encoding="utf-8") as f:
                json.dump(estoque, f, indent=4, ensure_ascii=False)

            # Atualizar status da requisição
            self.update_request_status(req_id, "Comprada")

            QMessageBox.information(self, "Compra registrada",
                                    "Itens adicionados ao estoque com sucesso!")
            self.close()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao registrar compra: {str(e)}")

    def update_request_status(self, req_id, new_status):
        """Atualiza o status de uma requisição"""
        try:
            with open(REQUISICOES_JSON, "r", encoding="utf-8") as f:
                requests = json.load(f)

            for req in requests:
                if req["id"] == req_id:
                    req["status"] = new_status
                    break

            with open(REQUISICOES_JSON, "w", encoding="utf-8") as f:
                json.dump(requests, f, indent=4, ensure_ascii=False)

        except Exception:
            pass


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication([])
    window = BuyWindow()
    window.show()
    app.exec()