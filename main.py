import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QComboBox, QPushButton, QVBoxLayout, QWidget, QMessageBox, QCheckBox, QSpinBox
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve
from PyQt5.QtGui import QIcon

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ExplorAI - Votre assistant de recherche intelligent")
        self.setGeometry(100, 100, 500, 500)  # Ajusté pour l'ajout de plus de widgets
        self.setWindowIcon(QIcon('path/to/icon.png'))  # Assurez-vous que le chemin vers l'icône est correct
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
            QLineEdit, QComboBox, QCheckBox, QSpinBox {
                border: 2px solid #2980b9;
                border-radius: 5px;
                padding: 5px;
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
        """)

        layout = QVBoxLayout()
        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        centralWidget.setLayout(layout)

        layout.addWidget(QLabel("Trouvez vos fichiers rapidement avec ExplorAI", self))

        # Champ pour le nom du fichier
        labelFileName = QLabel("Nom du fichier :", self)
        self.lineEditFileName = QLineEdit(self)
        layout.addWidget(labelFileName)
        layout.addWidget(self.lineEditFileName)

        # Option de recherche non stricte
        self.checkBoxLooseMatch = QCheckBox("Recherche non stricte du nom", self)
        layout.addWidget(self.checkBoxLooseMatch)

        # Champ pour la description (non utilisée actuellement dans la recherche)
        labelDescription = QLabel("Description :", self)
        self.lineEditDescription = QLineEdit(self)
        self.lineEditDescription.setFixedHeight(60)
        layout.addWidget(labelDescription)
        layout.addWidget(self.lineEditDescription)

        # Sélection du format du fichier
        labelFileFormat = QLabel("Format du fichier :", self)
        self.comboBoxFileFormat = QComboBox(self)
        self.comboBoxFileFormat.addItems(['.png', '.jpg', '.txt', '.pdf'])
        layout.addWidget(labelFileFormat)
        layout.addWidget(self.comboBoxFileFormat)

        # SpinBoxes pour la taille du fichier
        layout.addWidget(QLabel("Taille minimale du fichier (Ko) :"))
        self.spinBoxMinSize = QSpinBox(self)
        self.spinBoxMinSize.setMaximum(1000000)  # Max value in Ko
        layout.addWidget(self.spinBoxMinSize)

        layout.addWidget(QLabel("Taille maximale du fichier (Ko) :"))
        self.spinBoxMaxSize = QSpinBox(self)
        self.spinBoxMaxSize.setMaximum(1000000)
        self.spinBoxMaxSize.setValue(1000000)
        layout.addWidget(self.spinBoxMaxSize)

        # Bouton de recherche
        self.pushButtonSearch = QPushButton("Chercher", self)
        self.pushButtonSearch.clicked.connect(self.searchFile)
        layout.addWidget(self.pushButtonSearch)

        self.show()

    def searchFile(self):
        animation = QPropertyAnimation(self.pushButtonSearch, b"geometry")
        animation.setDuration(200)
        animation.setStartValue(QRect(self.pushButtonSearch.x(), self.pushButtonSearch.y(), self.pushButtonSearch.width(), self.pushButtonSearch.height()))
        animation.setEndValue(QRect(self.pushButtonSearch.x(), self.pushButtonSearch.y() - 10, self.pushButtonSearch.width(), self.pushButtonSearch.height()))
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        animation.start(QPropertyAnimation.DeleteWhenStopped)

        fileName = self.lineEditFileName.text()
        fileFormat = self.comboBoxFileFormat.currentText()
        minSize = self.spinBoxMinSize.value() * 1024  # Convert Ko to bytes
        maxSize = self.spinBoxMaxSize.value() * 1024
        looseMatch = self.checkBoxLooseMatch.isChecked()
        rootDir = '/'  # Adapt this to your needs

        file_found = False
        for root, dirs, files in os.walk(rootDir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_size = os.path.getsize(file_path)
                except OSError as e:
                    print(f"Cannot access {file_path}: {str(e)}")
                    continue  # Skip this file and continue with the next one
            
                if ((looseMatch and fileName in file) or file == fileName + fileFormat) and (minSize <= file_size <= maxSize):
                    file_found = True
                    QMessageBox.information(self, "Fichier Trouvé", f"Chemin du fichier : {file_path}")
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
