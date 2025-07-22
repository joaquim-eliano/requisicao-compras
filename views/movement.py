from PySide6.QtWidgets import (
    QDialog, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QMessageBox, QHeaderView,
    QAbstractItemView
)

import json
import os
import sys

# Diretório onde o script está
if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Diretório raiz do projeto (sobe um nível a partir do script)
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Caminhos absolutos para os arquivos na raiz do projeto
REQUISICOES_JSON = os.path.join(PROJECT_ROOT, "requisicoes.json")
ESTOQUE_ALMOX_JSON = os.path.join(PROJECT_ROOT, "almoxarifado.json")
ESTOQUE_SETOR_JSON = os.path.join(PROJECT_ROOT, "setor.json")


class MovementWindow(QDialog):
    def __init__(self, parent=None, role=None):
        super().__init__(parent)
        self.role = role
        self.setWindowTitle("Movimentar Requisições")
        self.resize(800, 500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Table for requests
        self.requests_table = QTableWidget()
        self.requests_table.setColumnCount(4)
        headers = ["ID", "Itens", "Quantidade", "Status"]
        self.requests_table.setHorizontalHeaderLabels(headers)
        self.requests_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # type: ignore
        self.requests_table.setSelectionBehavior(QAbstractItemView.SelectRows)  # type: ignore
        self.requests_table.setSelectionMode(QAbstractItemView.SingleSelection)  # type: ignore
        self.requests_table.setEditTriggers(QTableWidget.NoEditTriggers)  # type: ignore
        self.requests_table.itemSelectionChanged.connect(self.update_buttons)
        layout.addWidget(self.requests_table)

        # Buttons
        btn_layout = QHBoxLayout()

        self.send_button = QPushButton("Enviar Requisição")
        self.send_button.clicked.connect(self.send_request)
        self.send_button.setEnabled(False)
        btn_layout.addWidget(self.send_button)

        self.receive_button = QPushButton("Receber Requisição")
        self.receive_button.clicked.connect(self.receive_request)
        self.receive_button.setEnabled(False)
        btn_layout.addWidget(self.receive_button)

        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.close)
        btn_layout.addWidget(close_button)

        layout.addLayout(btn_layout)

        # Status label
        self.status_label = QLabel("Selecione uma requisição para movimentar")
        layout.addWidget(self.status_label)

        # Load requests
        self.load_requests()

    def load_requests(self):
        try:
            with open(REQUISICOES_JSON, "r", encoding="utf-8") as f:
                self.requests = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.requests = []
            return

        # Filter requests based on role
        if self.role == 3:  # Buyer - can send "Comprada" requests
            filtered_requests = [req for req in self.requests if req.get("status") == "Comprada"]
        elif self.role in (1, 2):  # Employee/Manager - can receive "Enviada" requests
            filtered_requests = [req for req in self.requests if req.get("status") == "Enviada"]
        else:  # Admin - can see both
            filtered_requests = [req for req in self.requests if req.get("status") in ("Comprada", "Enviada")]

        self.requests_table.setRowCount(len(filtered_requests))

        for row, req in enumerate(filtered_requests):
            self.requests_table.setItem(row, 0, QTableWidgetItem(str(req["id"])))

            # Format items list
            items_text = "\n".join([f"{item['item']} ({item['quantidade']})" for item in req["itens"]])
            self.requests_table.setItem(row, 1, QTableWidgetItem(items_text))

            # Total quantity
            total_qty = sum(item["quantidade"] for item in req["itens"])
            self.requests_table.setItem(row, 2, QTableWidgetItem(str(total_qty)))

            # Status
            self.requests_table.setItem(row, 3, QTableWidgetItem(req["status"]))

    # ADDED MISSING FUNCTION
    def update_buttons(self):
        """Update button states based on selected request"""
        selected_row = self.requests_table.currentRow()
        if selected_row < 0:
            self.send_button.setEnabled(False)
            self.receive_button.setEnabled(False)
            self.status_label.setText("Selecione uma requisição para movimentar")
            return

        status = self.requests_table.item(selected_row, 3).text()
        self.selected_id = int(self.requests_table.item(selected_row, 0).text())

        # Enable buttons based on status and role
        can_send = status == "Comprada" and self.role in (0, 3)  # Admin or Buyer
        can_receive = status == "Enviada" and self.role in (0, 1, 2)  # Admin, Employee or Manager

        self.send_button.setEnabled(can_send)
        self.receive_button.setEnabled(can_receive)

        self.status_label.setText(f"Requisição {self.selected_id} selecionada - Status: {status}")

    def send_request(self):
        """Send request from warehouse to sector"""
        # Find the request
        request = next((req for req in self.requests if req["id"] == self.selected_id), None)
        if not request:
            QMessageBox.warning(self, "Erro", "Requisição não encontrada!")
            return

        # Update stock
        if not self.update_stocks(request, direction="out"):
            return

        # Update request status
        request["status"] = "Enviada"
        self.save_requests()

        QMessageBox.information(self, "Sucesso", "Requisição enviada com sucesso!")
        self.load_requests()

    def receive_request(self):
        """Receive request in sector"""
        # Find the request
        request = next((req for req in self.requests if req["id"] == self.selected_id), None)
        if not request:
            QMessageBox.warning(self, "Erro", "Requisição não encontrada!")
            return

        # Update stock
        if not self.update_stocks(request, direction="in"):
            return

        # Update request status
        request["status"] = "Finalizada"
        self.save_requests()

        QMessageBox.information(self, "Sucesso", "Requisição recebida com sucesso!")
        self.load_requests()

    def update_stocks(self, request, direction):
        """Update warehouse and sector stocks"""
        try:
            # Load warehouse stock
            with open(ESTOQUE_ALMOX_JSON, "r", encoding="utf-8") as f:
                warehouse_stock = json.load(f)

            # Load sector stock
            with open(ESTOQUE_SETOR_JSON, "r", encoding="utf-8") as f:
                sector_stock = json.load(f)

            # Process each item
            for item in request["itens"]:
                item_name = item["item"]
                qty = item["quantidade"]

                if direction == "out":  # Sending from warehouse to sector
                    # Update warehouse stock
                    warehouse_item = next((i for i in warehouse_stock if i["item"] == item_name), None)
                    if not warehouse_item or warehouse_item["quantidade"] < qty:
                        QMessageBox.warning(self, "Erro",
                                            f"Estoque insuficiente de {item_name} no almoxarifado!")
                        return False
                    warehouse_item["quantidade"] -= qty
                    warehouse_item["valor_total"] = warehouse_item["quantidade"] * warehouse_item["valor_unitario"]

                    # Update sector stock
                    sector_item = next((i for i in sector_stock if i["item"] == item_name), None)
                    if not sector_item:
                        sector_stock.append({
                            "item": item_name,
                            "quantidade": qty,
                            "valor_unitario": warehouse_item["valor_unitario"],
                            "valor_total": qty * warehouse_item["valor_unitario"]
                        })
                    else:
                        sector_item["quantidade"] += qty
                        sector_item["valor_total"] = sector_item["quantidade"] * sector_item["valor_unitario"]

                else:  # Receiving in sector (already sent, so just confirm)
                    # Stock was already added during sending, no need to change
                    pass

            # Save updated stocks
            with open(ESTOQUE_ALMOX_JSON, "w", encoding="utf-8") as f:
                json.dump(warehouse_stock, f, indent=4, ensure_ascii=False)

            with open(ESTOQUE_SETOR_JSON, "w", encoding="utf-8") as f:
                json.dump(sector_stock, f, indent=4, ensure_ascii=False)

            return True

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao atualizar estoques: {str(e)}")
            return False

    def save_requests(self):
        """Save updated requests"""
        try:
            with open(REQUISICOES_JSON, "w", encoding="utf-8") as f:
                json.dump(self.requests, f, indent=4, ensure_ascii=False)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar requisições: {str(e)}")


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication([])
    window = MovementWindow(role=3)
    window.show()
    app.exec()