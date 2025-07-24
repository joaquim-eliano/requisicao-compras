from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QPushButton, QMessageBox,
    QInputDialog, QHBoxLayout, QLabel
)
from PySide6.QtCore import Qt
import json, sys, os, locale

# Configure Brazilian locale for currency formatting
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')  # Fallback for Windows


# Helper function to format currency
def format_currency(value):
    """Formata um valor como moeda brasileira"""
    try:
        # Se o valor já é string, converte para float
        if isinstance(value, str):
            # Remove símbolos e formatação existente
            value = value.replace('R$', '').replace('.', '').replace(',', '.').strip()
            value = float(value)
        return locale.currency(value, grouping=True, symbol=True)
    except (TypeError, ValueError):
        # Fallback para formatação manual
        try:
            value = float(value)
            return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            return "R$ 0,00"


# Obter o diretório do script
if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Diretório raiz do projeto (sobe um nível a partir do script)
# PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
# ESTOQUE_SETOR_JSON = os.path.join(PROJECT_ROOT, "setor.json")

ESTOQUE_SETOR_JSON = os.path.join(SCRIPT_DIR, "setor.json")

class StockOffWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Baixa de Estoque do Setor")
        self.resize(800, 500)
        self.setup_ui()
        self.load_stock()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Título
        title = QLabel("Estoque do Setor - Selecione os itens para dar baixa")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        # Tabela de estoque
        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(4)
        headers = ["Item", "Quantidade", "Valor Unitário", "Valor Total"]
        self.stock_table.setHorizontalHeaderLabels(headers)
        self.stock_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # type: ignore
        self.stock_table.setSelectionBehavior(QAbstractItemView.SelectRows)  # type: ignore
        self.stock_table.setSelectionMode(QAbstractItemView.MultiSelection)  # type: ignore
        self.stock_table.setEditTriggers(QTableWidget.NoEditTriggers)  # type: ignore
        layout.addWidget(self.stock_table)

        # Botões
        btn_layout = QHBoxLayout()

        self.stock_off_button = QPushButton("Dar Baixa nos Itens Selecionados")
        self.stock_off_button.clicked.connect(self.perform_stock_off)
        btn_layout.addWidget(self.stock_off_button)

        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.close)
        btn_layout.addWidget(close_button)

        layout.addLayout(btn_layout)

    def load_stock(self):
        """Carrega o estoque do setor do arquivo JSON"""
        try:
            with open(ESTOQUE_SETOR_JSON, 'r', encoding='utf-8') as f:
                self.stock_data = json.load(f)
        except FileNotFoundError:
            self.stock_data = []
            QMessageBox.warning(self, "Erro", "Arquivo de estoque do setor não encontrado!")
            return
        except json.JSONDecodeError:
            self.stock_data = []
            QMessageBox.warning(self, "Erro", "Arquivo de estoque do setor está corrompido!")
            return

        # Configurar tabela
        self.stock_table.setRowCount(len(self.stock_data))

        for row, item in enumerate(self.stock_data):
            # Item
            self.stock_table.setItem(row, 0, QTableWidgetItem(str(item.get('item', ''))))

            # Quantidade
            qtd = item.get('quantidade', 0)
            self.stock_table.setItem(row, 1, QTableWidgetItem(str(qtd)))

            # Valor Unitário (formatado como moeda)
            unit_value = item.get('valor_unitario', 0.0)
            unit_value_str = format_currency(unit_value)
            unit_item = QTableWidgetItem(unit_value_str)
            unit_item.setData(Qt.UserRole, unit_value)  # type: ignore
            self.stock_table.setItem(row, 2, unit_item)

            # Valor Total (formatado como moeda)
            total_value = item.get('valor_total', 0.0)
            # Se não existir, calcula: quantidade * valor unitário
            if total_value == 0 and qtd != 0 and unit_value != 0:
                total_value = qtd * unit_value
            total_value_str = format_currency(total_value)
            total_item = QTableWidgetItem(total_value_str)
            total_item.setData(Qt.UserRole, total_value)  # type: ignore
            self.stock_table.setItem(row, 3, total_item)

    def perform_stock_off(self):
        """Realiza a baixa nos itens selecionados"""
        selected_rows = self.stock_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Nenhum item selecionado",
                                "Selecione pelo menos um item para dar baixa.")
            return

        items_to_update = []

        for row_index in [row.row() for row in selected_rows]:
            item_name = self.stock_table.item(row_index, 0).text()
            current_qty = int(self.stock_table.item(row_index, 1).text())

            # Obter quantidade a baixar
            qty, ok = QInputDialog.getInt(
                self,
                f"Baixa de {item_name}",
                f"Quantidade a baixar (disponível: {current_qty}):",
                1,  # Valor padrão
                1,  # Mínimo
                current_qty,  # Máximo
                1  # Step
            )

            if not ok:
                continue  # Usuário cancelou

            # Validar quantidade
            if qty < 1:
                QMessageBox.warning(self, "Valor inválido",
                                    f"A quantidade para {item_name} deve ser pelo menos 1.")
                continue

            if qty > current_qty:
                QMessageBox.warning(self, "Estoque insuficiente",
                                    f"Quantidade solicitada ({qty}) maior que disponível ({current_qty}) para {item_name}.")
                continue

            items_to_update.append({
                "row": row_index,
                "name": item_name,
                "qty_to_remove": qty,
                "current_qty": current_qty
            })

        if not items_to_update:
            return  # Nenhum item atualizado

        # Atualizar estoque
        self.update_stock(items_to_update)

        QMessageBox.information(self, "Baixa realizada",
                                "Baixa de estoque realizada com sucesso!")
        self.load_stock()  # Recarregar tabela

    def update_stock(self, items_to_update):
        """Atualiza o estoque com as baixas solicitadas"""
        # Atualizar os dados em memória
        for item_info in items_to_update:
            for stock_item in self.stock_data:
                if stock_item["item"] == item_info["name"]:
                    new_qty = stock_item["quantidade"] - item_info["qty_to_remove"]
                    stock_item["quantidade"] = new_qty

                    # Atualizar valor total
                    if "valor_unitario" in stock_item:
                        stock_item["valor_total"] = new_qty * stock_item["valor_unitario"]
                    break

        # Salvar no arquivo
        try:
            with open(ESTOQUE_SETOR_JSON, 'w', encoding='utf-8') as f:
                json.dump(self.stock_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao salvar",
                                 f"Falha ao salvar estoque atualizado: {str(e)}")


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication([])
    window = StockOffWindow()
    window.show()
    app.exec()