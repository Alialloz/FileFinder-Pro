import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QComboBox, QPushButton, QVBoxLayout, QWidget, QMessageBox, QCheckBox, QSpinBox
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve, QThread, pyqtSignal
from PyQt5.QtGui import QIcon

class FileSearchThread(QThread):
    file_found_signal = pyqtSignal(str)
    search_failed_signal = pyqtSignal()

    def __init__(self, rootDir, fileName, fileFormat, minSize, maxSize, looseMatch):
        super().__init__()
        self.rootDir = rootDir
        self.fileName = fileName
        self.fileFormat = fileFormat
        self.minSize = minSize
        self.maxSize = maxSize
        self.looseMatch = looseMatch

    def run(self):
        file_found = False
        for root, dirs, files in os.walk(self.rootDir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_size = os.path.getsize(file_path)
                except OSError:
                    continue  # Skip inaccessible files
                
                if ((self.looseMatch and self.fileName.lower() in file.lower()) or file.lower() == (self.fileName.lower() + self.fileFormat.lower())) and (self.minSize <= file_size <= self.maxSize):
                    self.file_found_signal.emit(file_path)
                    file_found = True
                    break
            if file_found:
                break
        
        if not file_found:
            self.search_failed_signal.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ExplorAI - Votre assistant de recherche intelligent")
        self.setGeometry(100, 100, 500, 500)
        self.setWindowIcon(QIcon('path/to/icon.png'))
        self.initUI()

    def initUI(self):
        self.setStyleSheet("""
            QWidget { font-size: 16px; font-family: 'Arial'; background-color: #f5f5f5; }
            QLabel { color: #2c3e50; }
            QLineEdit, QComboBox, QCheckBox, QSpinBox { border: 2px solid #2980b9; border-radius: 5px; padding: 5px; background-color: #ecf0f1; }
            QPushButton { background-color: #3498db; color: white; border-radius: 5px; padding: 10px; font-weight: bold; }
            QPushButton:hover { background-color: #2980b9; }
        """)

        layout = QVBoxLayout()
        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        centralWidget.setLayout(layout)

        layout.addWidget(QLabel("Trouvez vos fichiers rapidement avec ExplorAI", self))

        self.lineEditFileName = QLineEdit(self)
        layout.addWidget(QLabel("Nom du fichier :"))
        layout.addWidget(self.lineEditFileName)

        self.checkBoxLooseMatch = QCheckBox("Recherche non stricte du nom", self)
        layout.addWidget(self.checkBoxLooseMatch)

        self.lineEditDescription = QLineEdit(self)
        self.lineEditDescription.setFixedHeight(60)
        layout.addWidget(QLabel("Description :"))
        layout.addWidget(self.lineEditDescription)

        self.comboBoxFileFormat = QComboBox(self)
        self.comboBoxFileFormat.addItems(['.png', '.jpg', '.txt', '.pdf'])
        layout.addWidget(QLabel("Format du fichier :"))
        layout.addWidget(self.comboBoxFileFormat)

        self.spinBoxMinSize = QSpinBox(self)
        self.spinBoxMinSize.setMaximum(1000000)
        layout.addWidget(QLabel("Taille minimale du fichier (Ko) :"))
        layout.addWidget(self.spinBoxMinSize)

        self.spinBoxMaxSize = QSpinBox(self)
        self.spinBoxMaxSize.setMaximum(1000000)
        self.spinBoxMaxSize.setValue(1000000)
        layout.addWidget(QLabel("Taille maximale du fichier (Ko) :"))
        layout.addWidget(self.spinBoxMaxSize)

        self.pushButtonSearch = QPushButton("Chercher", self)
        self.pushButtonSearch.clicked.connect(self.startSearch)
        layout.addWidget(self.pushButtonSearch)

    def startSearch(self):
        animation = QPropertyAnimation(self.pushButtonSearch, b"geometry")
        animation.setDuration(200)
        animation.setStartValue(QRect(self.pushButtonSearch.x(), self.pushButtonSearch.y(), self.pushButtonSearch.width(), self.pushButtonSearch.height()))
        animation.setEndValue(QRect(self.pushButtonSearch.x(), self.pushButtonSearch.y() - 10, self.pushButtonSearch.width(), self.pushButtonSearch.height()))
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        animation.start(QPropertyAnimation.DeleteWhenStopped)

        fileName = self.lineEditFileName.text()
        fileFormat = self.comboBoxFileFormat.currentText()
        minSize = self.spinBoxMinSize.value() * 1024
        maxSize = self.spinBoxMaxSize.value() * 1024
        looseMatch = self.checkBoxLooseMatch.isChecked()
        rootDir = '/'  # Adjust this to your system if needed

        # Start search thread
        self.search_thread = FileSearchThread(rootDir, fileName, fileFormat, minSize, maxSize, looseMatch)
        self.search_thread.file_found_signal.connect(self.fileFound)
        self.search_thread.search_failed_signal.connect(self.searchFailed)
        self.search_thread.start()

    def fileFound(self, filePath):
        QMessageBox.information(self, "Fichier Trouvé", f"Chemin du fichier : {filePath}")

    def searchFailed(self):
        self.lineEditFileName.setStyleSheet("border: 2px solid red;")
        QMessageBox.warning(self, "Aucun Résultat", "Fichier non trouvé. Veuillez vérifier le nom et réessayer.")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()  # Make sure the window is shown
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
