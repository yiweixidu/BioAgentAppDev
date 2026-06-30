# main.py
"""
BioAgent entry point — Login → MainWindow loop.
After Logout, returns to Login instead of exiting the whole program.
"""
import sys
from PyQt6.QtWidgets import QApplication, QPushButton
from gui.login_dialog import LoginDialog
from gui.main_window import MainWindow

def run_session(app) -> bool:
    """
    Run one full Login → MainWindow cycle.
    Returns:
        True  → user clicked Logout, needs to log in again
        False → user closed the app, should exit
    """
    login = LoginDialog()
    if login.exec() != LoginDialog.DialogCode.Accepted:
        return False   # user cancelled login or exceeded max attempts → exit

    window = MainWindow()

    # Use a mutable container to capture whether the close was triggered by logout
    state = {"logout": False}

    def on_logout():
        state["logout"] = True

    window.logout_requested.connect(on_logout)
    window.show()
    app.exec()   # blocks until window.close() is called

    return state["logout"]

def main():
    # you can instantiate object from QApplication
    app = QApplication(sys.argv)  # event loop object

    while True:
        should_relogin = run_session(app)
        if not should_relogin:
            break

    sys.exit(0)  # user closed or max attempts reached

main()