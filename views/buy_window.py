# views\buy_window.py

from PySide6.QtWidgets import (
    QDialog, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QPushButton, QMessageBox,
    QLabel, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor
import json
import os
import sys
import locale

# Configurar localização para formato brasileiro
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Obter o diretório do script (igual ao anterior)
if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

REQUISICOES_JSON = os.path.join(SCRIPT_DIR, "requisicoes.json")
ESTOQUE_JSON = os.path.join(SCRIPT_DIR, "almoxarifado.json")


def format_currency(value):
    """Formata um valor como moeda brasileira"""
    return locale.currency(value, grouping=True, symbol=True)


class BuyWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Compras")
        self.resize(1150, 650)

        # Layout principal
        main_layout = QGridLayout(self)

        # Tabela de requisições
        self.requests_table = QTableWidget()
        self.requests_table.setColumnCount(2)
        self.requests_table.setHorizontalHeaderLabels(["ID Requisição", "Status"])
        self.requests_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) # type: ignore
        self.requests_table.setSelectionBehavior(QAbstractItemView.SelectRows) # type: ignore
        self.requests_table.setSelectionMode(QAbstractItemView.SingleSelection) # type: ignore
        self.requests_table.itemSelectionChanged.connect(self.load_request_items)
        self.requests_table.setEditTriggers(QTableWidget.NoEditTriggers) # type: ignore

        # Tabela de itens
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(8)
        headers = [
            "Item",
            "Quantidade Solicitada",
            "Estoque Almoxarifado",
            "Quantidade Disponível",
            "Quantidade a Comprar",
            "Preço Unitário",
            "Valor Total",
            "Status"
        ]
        self.items_table.setHorizontalHeaderLabels(headers)
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) # type: ignore

        # Adicionar tabelas ao layout
        main_layout.addWidget(self.requests_table, 0, 0, 1, 2)
        main_layout.addWidget(self.items_table, 1, 0, 1, 2)

        # Área de totais
        total_layout = QHBoxLayout()

        self.total_label = QLabel("Total da Compra: R$ 0,00")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        total_layout.addWidget(self.total_label)

        main_layout.addLayout(total_layout, 2, 0, 1, 2)

        # Botões
        btn_layout = QHBoxLayout()

        self.buy_button = QPushButton("Registrar Compra")
        self.buy_button.clicked.connect(self.register_purchase)
        btn_layout.addWidget(self.buy_button)

        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.close)
        btn_layout.addWidget(close_button)

        main_layout.addLayout(btn_layout, 3, 0, 1, 2)

        # Carregar dados
        self.load_requests()
        self.load_stock()

    def load_stock(self):
        """Carrega o estoque do almoxarifado"""
        self.stock = {}
        try:
            if os.path.exists(ESTOQUE_JSON):
                with open(ESTOQUE_JSON, "r", encoding="utf-8") as f:
                    stock_data = json.load(f)
                    for item in stock_data:
                        item_name = item.get('item', '')
                        if item_name:
                            self.stock[item_name] = {
                                'quantidade': item.get('quantidade', 0),
                                'valor_unitario': item.get('valor_unitario', 0.0)
                            }
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Falha ao carregar estoque: {str(e)}")

    def load_requests(self):
        """Carrega requisições aprovadas"""
        try:
            with open(REQUISICOES_JSON, "r", encoding="utf-8") as f:
                requests = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            requests = []

        approved_requests = [req for req in requests if req.get("status") == "Aprovada"]
        self.requests_table.setRowCount(len(approved_requests))
        for row, req in enumerate(approved_requests):
            self.requests_table.setItem(row, 0, QTableWidgetItem(str(req["id"])))
            self.requests_table.setItem(row, 1, QTableWidgetItem(req["status"]))

    def load_request_items(self):
        """Carrega itens da requisição selecionada com campos editáveis"""
        selected_row = self.requests_table.currentRow()
        if selected_row < 0:
            return

        req_id = int(self.requests_table.item(selected_row, 0).text())
        self.current_req_id = req_id

        try:
            with open(REQUISICOES_JSON, "r", encoding="utf-8") as f:
                requests = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            requests = []

        selected_request = next((req for req in requests if req["id"] == req_id), None)
        if not selected_request:
            return

        items = selected_request.get("itens", [])
        self.items_table.setRowCount(len(items))

        total_compra = 0.0

        for row, item in enumerate(items):
            item_name = item["item"]
            qtd_solicitada = item["quantidade"]

            # Obter informações do estoque
            estoque_info = self.stock.get(item_name, {'quantidade': 0, 'valor_unitario': 0.0})
            estoque_disponivel = estoque_info['quantidade']
            qtd_disponivel = min(qtd_solicitada, estoque_disponivel)
            qtd_comprar = max(0, qtd_solicitada - qtd_disponivel)

            # Calcular status
            if qtd_comprar == 0:
                status = "Em estoque"
                bg_color = QBrush(QColor(220, 255, 220))  # Verde claro
            else:
                status = "Necessita compra"
                bg_color = QBrush(QColor(255, 220, 220))  # Vermelho claro

            # Item (não editável)
            item_cell = QTableWidgetItem(item_name)
            item_cell.setFlags(item_cell.flags() & ~Qt.ItemIsEditable) # type: ignore
            self.items_table.setItem(row, 0, item_cell)

            # Quantidade Solicitada (não editável)
            qtd_sol_cell = QTableWidgetItem(str(qtd_solicitada))
            qtd_sol_cell.setFlags(qtd_sol_cell.flags() & ~Qt.ItemIsEditable) # type: ignore
            self.items_table.setItem(row, 1, qtd_sol_cell)

            # Estoque Almoxarifado (não editável)
            estoque_cell = QTableWidgetItem(str(estoque_disponivel))
            estoque_cell.setFlags(estoque_cell.flags() & ~Qt.ItemIsEditable) # type: ignore
            self.items_table.setItem(row, 2, estoque_cell)

            # Quantidade Disponível (não editável)
            qtd_disp_cell = QTableWidgetItem(str(qtd_disponivel))
            qtd_disp_cell.setFlags(qtd_disp_cell.flags() & ~Qt.ItemIsEditable) # type: ignore
            self.items_table.setItem(row, 3, qtd_disp_cell)

            # Quantidade a Comprar (editável)
            qtd_comprar_cell = QTableWidgetItem(str(qtd_comprar))
            qtd_comprar_cell.setData(Qt.ItemDataRole, qtd_comprar)  # type: ignore
            self.items_table.setItem(row, 4, qtd_comprar_cell)

            # Preço Unitário (editável)
            preco_unit = estoque_info.get('valor_unitario', 0.0)
            preco_cell = QTableWidgetItem(format_currency(preco_unit))
            self.items_table.setItem(row, 5, preco_cell)

            # Valor Total (calculado)
            valor_total = qtd_comprar * preco_unit
            total_cell = QTableWidgetItem(format_currency(valor_total))
            total_cell.setFlags(total_cell.flags() & ~Qt.ItemIsEditable) # type: ignore
            self.items_table.setItem(row, 6, total_cell)

            # Status (não editável)
            status_cell = QTableWidgetItem(status)
            status_cell.setFlags(status_cell.flags() & ~Qt.ItemIsEditable) # type: ignore
            status_cell.setBackground(bg_color)
            self.items_table.setItem(row, 7, status_cell)

            total_compra += valor_total

        # Conectar sinal para atualizar valores quando células forem editadas
        self.items_table.cellChanged.connect(self.update_values)


        # Atualizar total da compra
        self.total_label.setText(f"Total da Compra: {format_currency(total_compra)}")
        self.items_table.resizeColumnsToContents()

        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # type: ignore

    def update_values(self, row, column):
        """Atualiza valores quando células são editadas"""
        # Só nos interessa as colunas de quantidade a comprar (4) e preço unitário (5)
        if column not in (4, 5):
            return

        # Obter valores atuais
        try:
            qtd_comprar_item = self.items_table.item(row, 4)
            preco_item = self.items_table.item(row, 5)
            total_item = self.items_table.item(row, 6)

            # Converter valores
            qtd_comprar = int(qtd_comprar_item.text())
            preco_str = preco_item.text().replace("R$", "").replace(".", "").replace(",", ".").strip()
            preco_unit = float(preco_str)

            # Calcular novo total
            novo_total = qtd_comprar * preco_unit

            # Atualizar células
            total_item.setText(format_currency(novo_total))
            preco_item.setText(format_currency(preco_unit))  # Reformatar

            # Atualizar total geral
            self.update_total()

        except (ValueError, TypeError, AttributeError):
            pass

    def update_total(self):
        """Atualiza o total geral da compra"""
        total_compra = 0.0

        for row in range(self.items_table.rowCount()):
            total_item = self.items_table.item(row, 6)
            if total_item:
                try:
                    total_str = total_item.text().replace("R$", "").replace(".", "").replace(",", ".").strip()
                    total_compra += float(total_str)
                except ValueError:
                    pass

        self.total_label.setText(f"Total da Compra: {format_currency(total_compra)}")

    purchase_completed = Signal(int)  # Novo sinal

    def register_purchase(self):
        """Registra a compra e atualiza o estoque"""
        if not hasattr(self, 'current_req_id'):
            QMessageBox.warning(self, "Nenhuma requisição selecionada",
                                "Selecione uma requisição antes de registrar a compra.")
            return

        # Atualizar estoque com as compras
        for row in range(self.items_table.rowCount()):
            item_name = self.items_table.item(row, 0).text()

            # Obter quantidade a comprar
            qtd_comprar_item = self.items_table.item(row, 4)
            qtd_comprar = int(qtd_comprar_item.text())

            if qtd_comprar > 0:
                # Obter preço unitário
                preco_item = self.items_table.item(row, 5)
                preco_str = preco_item.text().replace("R$", "").replace(".", "").replace(",", ".").strip()
                preco_unit = float(preco_str)

                # Atualizar estoque
                if item_name in self.stock:
                    self.stock[item_name]['quantidade'] += qtd_comprar
                    # Atualizar preço médio ponderado
                    estoque_atual = self.stock[item_name]['quantidade'] - qtd_comprar
                    valor_atual = estoque_atual * self.stock[item_name]['valor_unitario']
                    valor_compra = qtd_comprar * preco_unit
                    novo_valor_unit = (valor_atual + valor_compra) / (estoque_atual + qtd_comprar)
                    self.stock[item_name]['valor_unitario'] = novo_valor_unit
                else:
                    self.stock[item_name] = {
                        'quantidade': qtd_comprar,
                        'valor_unitario': preco_unit
                    }

        # Salvar estoque atualizado
        self.save_stock()

        # Atualizar status da requisição
        self.update_request_status(self.current_req_id, "Comprada")

        # Emitir sinal ao finalizar compra
        self.purchase_completed.emit(self.current_req_id)

        QMessageBox.information(self, "Compra registrada",
                                "A compra foi registrada com sucesso! O estoque foi atualizado.")
        self.close()

    def save_stock(self):
        """Salva o estoque atualizado no arquivo"""
        try:
            # Converter para formato de lista
            stock_data = []
            for item_name, info in self.stock.items():
                stock_data.append({
                    'item': item_name,
                    'quantidade': info['quantidade'],
                    'valor_unitario': info['valor_unitario'],
                    'valor_total': info['quantidade'] * info['valor_unitario']
                })

            with open(ESTOQUE_JSON, "w", encoding="utf-8") as f:
                json.dump(stock_data, f, indent=4, ensure_ascii=False)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar estoque: {str(e)}")

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

        except Exception as e:
            QMessageBox.critical(self, "Erro",
                                 f"Falha ao atualizar status da requisição: {str(e)}")


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication([])
    window = BuyWindow()
    window.show()
    app.exec()