# views/report_window.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QRadioButton,
    QButtonGroup, QPushButton, QLabel, QComboBox, QTextEdit
)
from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
import json
import os
import sys

# Obter diretório do script
if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Diretório raiz do projeto (sobe um nível a partir do script)
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

REQUISICOES_JSON = os.path.join(PROJECT_ROOT, "requisicoes.json")
USERS_JSON = os.path.join(PROJECT_ROOT, "users.json")


class ReportWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gerar Relatório")
        self.setFixedSize(500, 400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Grupo de filtros
        filter_group = QGroupBox("Filtros")
        filter_layout = QVBoxLayout(filter_group)

        # Filtro por status
        status_group = QGroupBox("Status da Requisição")
        status_layout = QVBoxLayout(status_group)
        self.status_buttons = {
            "Todas": QRadioButton("Todas"),
            "Pendente": QRadioButton("Pendente"),
            "Aprovada": QRadioButton("Aprovada"),
            "Comprada": QRadioButton("Comprada"),
            "Enviada": QRadioButton("Enviada"),
            "Finalizada": QRadioButton("Finalizada"),
            "Reprovada": QRadioButton("Reprovada")
        }

        self.status_group = QButtonGroup(self)
        for text, button in self.status_buttons.items():
            status_layout.addWidget(button)
            self.status_group.addButton(button)
        self.status_buttons["Todas"].setChecked(True)

        # Filtro por usuário
        user_group = QGroupBox("Usuário")
        user_layout = QVBoxLayout(user_group)
        self.user_combo = QComboBox()
        self.user_combo.addItem("Todos", None)
        self.load_users()
        user_layout.addWidget(self.user_combo)

        # Adicionar grupos ao layout
        filter_layout.addWidget(status_group)
        filter_layout.addWidget(user_group)

        # Área de preview
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)

        # Botões
        btn_layout = QHBoxLayout()
        generate_btn = QPushButton("Gerar Relatório")
        generate_btn.clicked.connect(self.generate_report)
        print_btn = QPushButton("Imprimir")
        print_btn.clicked.connect(self.print_report)
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.close)

        btn_layout.addWidget(generate_btn)
        btn_layout.addWidget(print_btn)
        btn_layout.addWidget(close_btn)

        # Layout principal
        layout.addWidget(filter_group)
        layout.addWidget(QLabel("Pré-visualização:"))
        layout.addWidget(self.preview)
        layout.addLayout(btn_layout)

    def load_users(self):
        try:
            with open(USERS_JSON, 'r', encoding='utf-8') as f:
                users = json.load(f)
                for user in users:
                    self.user_combo.addItem(user['username'], user['username'])
        except Exception as e:
            print(f"Erro ao carregar usuários: {e}")

    def generate_report(self):
        # Obter filtros selecionados
        selected_status = next(
            (text for text, btn in self.status_buttons.items() if btn.isChecked()),
            "Todas"
        )
        selected_user = self.user_combo.currentData()

        # Carregar requisições
        try:
            with open(REQUISICOES_JSON, 'r', encoding='utf-8') as f:
                requests = json.load(f)
        except Exception as e:
            self.preview.setText(f"Erro ao carregar requisições: {str(e)}")
            return

        # Aplicar filtros
        if selected_status != "Todas":
            requests = [req for req in requests if req.get("status") == selected_status]

        # TODO: Adicionar filtro por usuário quando tivermos esse dado

        # Gerar relatório
        report_html = self.create_report_html(requests, selected_status, selected_user)
        self.preview.setHtml(report_html)

    def create_report_html(self, requests, status, user):
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 1cm; }}
                h1 {{ text-align: center; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .footer {{ margin-top: 30px; text-align: right; font-size: 0.8em; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Relatório de Requisições</h1>
                <p><strong>Status:</strong> {status} | <strong>Usuário:</strong> {user or 'Todos'}</p>
            </div>
            <table>
                <tr>
                    <th>ID</th>
                    <th>Itens</th>
                    <th>Quantidade Total</th>
                    <th>Status</th>
                </tr>
        """

        for req in requests:
            items_html = "<br>".join(
                [f"{item['item']} ({item['quantidade']})" for item in req['itens']]
            )
            total_qty = sum(item['quantidade'] for item in req['itens'])

            html += f"""
            <tr>
                <td>{req['id']}</td>
                <td>{items_html}</td>
                <td>{total_qty}</td>
                <td>{req['status']}</td>
            </tr>
            """

        html += """
            </table>
            <div class="footer">
                <p>Sistema de Estoque - Relatório gerado em: <!--DATA--></p>
            </div>
        </body>
        </html>
        """

        return html

    def print_report(self):
        printer = QPrinter(QPrinter.HighResolution) # type: ignore
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.Accepted: # type: ignore
            doc = QTextDocument()
            doc.setHtml(self.preview.toHtml())
            doc.print_(printer)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication([])
    window = ReportWindow()
    window.show()
    app.exec()