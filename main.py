# main.py
import sys
from PySide6.QtWidgets import QApplication, QStyleFactory, QDialog
from views.main_window import MainWindow
from views.login_window import LoginWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)

    login_dialog = LoginWindow()
    style = QStyleFactory.create('Windows')
    QApplication.setStyle(style)
    QApplication.setPalette(style.standardPalette())
    if login_dialog.exec() == QDialog.Accepted and login_dialog.valid_login: # type: ignore
        window = MainWindow(login_dialog.role)
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit()
