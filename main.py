import sys 

# Importing the required libraries for the application of PyQt 
# The libraries are imported from the PyQt5 module
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("File Dialog Example")
        self.setGeometry(100, 100, 400, 200)

        self.initUI()

    def initUI(self):
        self.show()

        # Creating a file dialog object
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.AnyFile)

        # Opening the file dialog
        file_dialog.open()