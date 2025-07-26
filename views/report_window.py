# views/report_window.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QRadioButton,
    QButtonGroup, QPushButton, QLabel, QComboBox,
    QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtCore import Qt
import json
import os
import sys
from datetime import datetime

# Obter diretório do script
if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Diretório raiz do projeto (sobe um nível a partir do script)
# PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# REQUISICOES_JSON = os.path.join(PROJECT_ROOT, "requisicoes.json")
# USERS_JSON = os.path.join(PROJECT_ROOT, "users.json")

REQUISICOES_JSON = os.path.join(SCRIPT_DIR, "requisicoes.json")
USERS_JSON = os.path.join(SCRIPT_DIR, "users.json")


class ReportWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gerar Relatório")
        self.setFixedSize(500, 350)  # Tamanho reduzido sem a pré-visualização
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

        # Botões (removido o botão de imprimir)
        btn_layout = QHBoxLayout()
        generate_btn = QPushButton("Gerar Relatório")
        generate_btn.clicked.connect(self.generate_report)
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.close)

        btn_layout.addWidget(generate_btn)
        btn_layout.addWidget(close_btn)

        # Layout principal
        layout.addWidget(filter_group)
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
            print(f"Erro ao carregar requisições: {e}")
            return

        # Aplicar filtros
        if selected_status != "Todas":
            requests = [req for req in requests if req.get("status") == selected_status]

        # Gerar relatório
        report_html = self.create_report_html(requests, selected_status, selected_user)

        # Abrir janela de visualização do relatório
        self.preview_window = ReportPreviewWindow(report_html, self)
        self.preview_window.show()

    def create_report_html(self, requests, status, user):
        # Gerar data atual
        data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Relatório de Requisições</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    color: #000;
                    background-color: #fff;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                th, td {{
                    border: 1px solid #000;
                    padding: 10px;
                    text-align: left;
                }}
                th {{
                    background-color: #f0f0f0;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Relatório de Requisições</h1>
                <p><strong>Status:</strong> {status} | <strong>Usuário:</strong> {user or 'Todos'}</p>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Itens</th>
                        <th>Quantidade Total</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
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

        html += f"""
                </tbody>
            </table>

            <div class="footer">
                <p>Sistema de Requisições Online - Relatório gerado em: {data_hoje}</p>
            </div>
        </body>
        </html>
        """

        return html


class ReportPreviewWindow(QDialog):
    def __init__(self, html_content, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Visualização do Relatório")
        # Tamanho para A4 (210mm x 297mm) em pixels (96 DPI)
        self.resize(794, 1123)  # 210mm * 3.78 = 794px, 297mm * 3.78 = 1123px

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Área de rolagem
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("background-color: white;")

        # Widget de conteúdo
        content_widget = QFrame()
        content_widget.setStyleSheet("background-color: white; color: black;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(100, 4, 4, 4)

        # Conteúdo do relatório (HTML)
        content_label = QLabel(html_content)
        content_label.setTextFormat(Qt.RichText)  # type: ignore
        content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)  # type: ignore
        content_label.setWordWrap(True)
        content_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_layout.addWidget(content_label)

        # Botões
        btn_layout = QHBoxLayout()
        print_btn = QPushButton("Imprimir")
        print_btn.clicked.connect(lambda: self.print_report(html_content))
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.close)

        btn_layout.addStretch(1)
        btn_layout.addWidget(print_btn)
        btn_layout.addWidget(close_btn)

        content_layout.addLayout(btn_layout)

        # Configurar a área de rolagem
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

    def print_report(self, html_content):
        printer = QPrinter(QPrinter.HighResolution)  # type: ignore
        printer.setPageSize(QPrinter.A4)  # type: ignore
        printer.setPageOrientation(QPrinter.Portrait)  # type: ignore

        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.Accepted:  # type: ignore
            doc = QTextDocument()
            doc.setHtml(html_content)
            doc.print_(printer)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication([])
    window = ReportWindow()
    window.show()
    app.exec()