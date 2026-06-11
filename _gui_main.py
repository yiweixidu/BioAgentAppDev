import sys

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QGridLayout, QLineEdit

from _gui_window import MainWindow

def main():
    # you can instantiate object from QApplication
    app = QApplication(sys.argv)  # event loop object

    #Create a window to be displayed for our event loop object app
    window = MainWindow()  #window is hidden
    window.show()

    #you have to start event loop reference by object app
    app.exec()  #keep the event loop executed

main()