import json
from PySide6.QtWidgets import QDialog, QGridLayout, QLineEdit, QPushButton, QMessageBox, QLabel


class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setFixedSize(300, 150)

        # Widgets das boxes
        self.label_user = QLabel("Usuário")
        self.username_input = QLineEdit()
        self.label_pass = QLabel("Senha")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        # Widgets dos botões
        self.login_button = QPushButton("Entrar")
        self.login_button.clicked.connect(self.verify_login)

        # joga tudo nos layout
        layout = QGridLayout()
        layout.addWidget(self.label_user)
        layout.addWidget(self.username_input)
        layout.addWidget(self.label_pass)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

        # Flag de controle
        self.valid_login = False

    def verify_login(self):
        try:
            with open("users.json", "r", encoding="utf-8") as f:
                users = json.load(f)
        except FileNotFoundError:
            QMessageBox.critical(self, "Erro", "Arquivo de usuários não encontrado.")
            return

        username = self.username_input.text()
        password = self.password_input.text()

        if username in users and users[username]["password"] == password:
            self.valid_login = True
            self.role = users[username]["role"]
            self.accept()  # Fecha a janela de login com sucesso
        else:
            QMessageBox.warning(self, "Erro", "Usuário ou senha inválidos.")