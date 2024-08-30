import sys
import os

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QComboBox, QPushButton, QVBoxLayout, QWidget, QMessageBox
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve  # Corrected import here
from PyQt5.QtGui import QIcon

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("ExplorAI - Votre assistant de recherche intelligent")
        self.setWindowIcon(QIcon('path/to/icon.png'))  # Update the path to your icon
        self.setGeometry(100, 100, 500, 400)

        self.initUI()

    def initUI(self):
        self.setStyleSheet("""
            QWidget {
                font-size: 16px;
                font-family: 'Arial';
                background-color: #f5f5f5;
            }
            QLabel {
                color: #2c3e50;
            }
            QLineEdit {
                border: 2px solid #2980b9;
                border-radius: 5px;
                padding: 10px;
                background-color: #ecf0f1;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QComboBox {
                border: 2px solid #2980b9;
                border-radius: 5px;
                padding: 5px;
                min-width: 120px;
                background-color: #ecf0f1;
            }
        """)

        layout = QVBoxLayout()
        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        centralWidget.setLayout(layout)

        layout.addWidget(QLabel("Trouvez vos fichiers rapidement avec ExplorAI", self))
        
        labelFileName = QLabel("Nom du fichier :", self)
        self.lineEditFileName = QLineEdit(self)
        layout.addWidget(labelFileName)
        layout.addWidget(self.lineEditFileName)

        labelDescription = QLabel("Description :", self)
        self.lineEditDescription = QLineEdit(self)
        self.lineEditDescription.setFixedHeight(60)
        layout.addWidget(labelDescription)
        layout.addWidget(self.lineEditDescription)

        labelFileFormat = QLabel("Format du fichier :", self)
        self.comboBoxFileFormat = QComboBox(self)
        self.comboBoxFileFormat.addItems(['.png', '.jpg', '.txt', '.pdf'])
        layout.addWidget(labelFileFormat)
        layout.addWidget(self.comboBoxFileFormat)

        self.pushButtonSearch = QPushButton("Chercher", self)
        self.pushButtonSearch.clicked.connect(self.searchFile)
        layout.addWidget(self.pushButtonSearch)

        self.show()

    def searchFile(self):
        animation = QPropertyAnimation(self.pushButtonSearch, b"geometry")
        animation.setDuration(200)
        animation.setStartValue(QRect(self.pushButtonSearch.x(), self.pushButtonSearch.y(), self.pushButtonSearch.width(), self.pushButtonSearch.height()))
        animation.setEndValue(QRect(self.pushButtonSearch.x(), self.pushButtonSearch.y() - 10, self.pushButtonSearch.width(), self.pushButtonSearch.height()))
        animation.setEasingCurve(QEasingCurve.InOutQuad)  # Corrected easing curve
        animation.start(QPropertyAnimation.DeleteWhenStopped)

        fileName = self.lineEditFileName.text()
        fileFormat = self.comboBoxFileFormat.currentText()
        rootDir = '/'  # Adapt to your needs

        file_found = False
        for root, dirs, files in os.walk(rootDir):
            for file in files:
                if file == fileName + fileFormat:
                    file_found = True
                    QMessageBox.information(self, "Fichier Trouvé", f"Chemin du fichier : {os.path.join(root, file)}")
                    break
            if file_found:
                break

        if not file_found:
            self.lineEditFileName.setStyleSheet("border: 2px solid red;")
            QMessageBox.warning(self, "Aucun Résultat", "Fichier non trouvé. Veuillez vérifier le nom et réessayer.")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
