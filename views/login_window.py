# views\login_window

import json
from PySide6.QtWidgets import (
    QDialog, QGridLayout, QLineEdit,
    QPushButton, QMessageBox, QLabel
)

class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.valid_login = False
        self.role = None

    def setup_ui(self):
        self.setWindowTitle("Login")
        self.setFixedSize(300, 150)

        # Widgets
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password) # type: ignore

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
            with open("users.json", "r", encoding="utf-8") as f:
                users = json.load(f)
        except FileNotFoundError:
            QMessageBox.critical(self, "Erro", "Arquivo de usuários não encontrado.")
            return

        username = self.username_input.text()
        password = self.password_input.text()

        if user_data := users.get(username):
            if user_data["password"] == password:
                self.valid_login = True
                self.role = user_data["role"]
                self.accept()
                return

        QMessageBox.warning(self, "Erro", "Usuário ou senha inválidos.")