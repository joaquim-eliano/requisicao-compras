import sys
from PySide6.QtWidgets import QApplication

from views.login_window import LoginWindow
from views.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    # Exibir janela de login
    login_dialog = LoginWindow()

    if login_dialog.exec() == LoginWindow.Accepted and login_dialog.valid_login: # type: ignore
        # Obter o nome de usuário do login_dialog
        username = login_dialog.username
        role = login_dialog.role

        # Criar e exibir a janela principal
        window = MainWindow(role, username)
        window.show()

        # Executar o loop de eventos
        sys.exit(app.exec())
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()