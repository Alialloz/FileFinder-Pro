import sys
import os

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QComboBox, QPushButton, QVBoxLayout, QWidget, QMessageBox

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("ExplorAI")
        self.setGeometry(100, 100, 400, 300)  # Adjusted for potential error messages

        self.initUI()

    def initUI(self):
        # Create a QWidget layout to add widgets
        layout = QVBoxLayout()
        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        centralWidget.setLayout(layout)

        # Adding label and line edit for file name
        labelFileName = QLabel("Nom fichier:", self)
        self.lineEditFileName = QLineEdit(self)
        layout.addWidget(labelFileName)
        layout.addWidget(self.lineEditFileName)

        # Adding label and line edit for description (not used in search)
        labelDescription = QLabel("Description:", self)
        self.lineEditDescription = QLineEdit(self)
        self.lineEditDescription.setFixedHeight(50)  # Makes it a bit bigger
        layout.addWidget(labelDescription)
        layout.addWidget(self.lineEditDescription)

        # Adding label and combo box for file format
        labelFileFormat = QLabel("Format fichier:", self)
        self.comboBoxFileFormat = QComboBox(self)
        self.comboBoxFileFormat.addItems(['.png', '.jpg', '.txt', '.pdf'])  # You can add more formats
        layout.addWidget(labelFileFormat)
        layout.addWidget(self.comboBoxFileFormat)

        # Adding a push button to initiate file search
        self.pushButtonSearch = QPushButton("Cherche !", self)
        self.pushButtonSearch.clicked.connect(self.searchFile)  # Connect button click to searchFile method
        layout.addWidget(self.pushButtonSearch)

        # Show the window
        self.show()

    def searchFile(self):
        # Get the file name and format from user input
        fileName = self.lineEditFileName.text()
        fileFormat = self.comboBoxFileFormat.currentText()

        # Start from the root directory, adapt this to your requirement
        rootDir = '/'
        for root, dirs, files in os.walk(rootDir):
            for file in files:
                if file == fileName + fileFormat:
                    QMessageBox.information(self, "File Found", f"File path: {os.path.join(root, file)}")
                    return

        QMessageBox.warning(self, "No Result", "File not found.")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
