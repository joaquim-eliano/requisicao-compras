# main.py

import sys
from PySide6.QtWidgets import QApplication, QDialog, QStyleFactory
from views.login_window import LoginWindow
from views.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    style = QStyleFactory.create('Windows')
    QApplication.setStyle(style)
    QApplication.setPalette(style.standardPalette())

    login_dialog = LoginWindow()

    if login_dialog.exec() == QDialog.Accepted and login_dialog.valid_login: # type: ignore
        window = MainWindow(login_dialog.role)
        window.show()
        sys.exit(app.exec())
    sys.exit()

if __name__ == '__main__':
    main()