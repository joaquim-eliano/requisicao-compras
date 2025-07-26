# views/login_window.py
import json
import os
import sys
from PySide6.QtWidgets import (
    QDialog, QGridLayout, QLineEdit,
    QPushButton, QMessageBox, QLabel
)

# Obter diretório do script
if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Diretório raiz do projeto (sobe um nível a partir do script)
#PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

USERS_JSON = os.path.join(SCRIPT_DIR, "users.json")

class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.valid_login = False
        self.role = None
        self.username = ""
        self.name = ""
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Login")
        self.setFixedSize(300, 150)

        # Widgets
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)  # type: ignore

        # Layout
        layout = QGridLayout()
        layout.addWidget(QLabel("Usuário"), 0, 0)
        layout.addWidget(self.username_input, 0, 1)
        layout.addWidget(QLabel("Senha"), 1, 0)
        layout.addWidget(self.password_input, 1, 1)
        layout.addWidget(self.create_login_button(), 2, 0, 1, 2)

        self.setLayout(layout)

    def create_login_button(self):
        button = QPushButton("Entrar")
        button.clicked.connect(self.verify_login)
        return button

    def verify_login(self):
        try:
            with open(USERS_JSON, "r", encoding="utf-8") as f:
                users = json.load(f)
        except FileNotFoundError:
            QMessageBox.critical(self, "Erro", "Arquivo de usuários não encontrado.")
            return

        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        # Procurar o usuário na lista
        for user in users:
            if user["username"] == username and user["password"] == password:
                self.valid_login = True
                self.role = user["role"]
                self.username = username
                self.name = user.get("name", username)  # Usar nome se existir
                self.accept()
                return

        QMessageBox.warning(self, "Erro", "Usuário ou senha inválidos.")