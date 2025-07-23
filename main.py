# main.py
import sys
from PySide6.QtWidgets import QApplication

from views.login_window import LoginWindow
from views.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    while True:
        # Exibir janela de login
        login_dialog = LoginWindow()
        if login_dialog.exec() == LoginWindow.Accepted and login_dialog.valid_login: # type: ignore
            # Obter dados do usuário
            username = login_dialog.username
            role = login_dialog.role
            name = login_dialog.name

            # Criar e exibir a janela principal
            window = MainWindow(role, username, name)
            window.show()

            # Executar o loop de eventos
            app.exec()
        else:
            break

    sys.exit(0)


if __name__ == "__main__":
    main()