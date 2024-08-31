import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QComboBox, QPushButton, QVBoxLayout, QWidget, QMessageBox, QCheckBox, QSpinBox, QProgressBar
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QFont

class FileSearchThread(QThread):
    file_found_signal = pyqtSignal(str)
    search_complete_signal = pyqtSignal(bool)

    def __init__(self, rootDir, fileName, fileFormat, minSize, maxSize, looseMatch):
        super().__init__()
        self.rootDir = rootDir
        self.fileName = fileName
        self.fileFormat = fileFormat
        self.minSize = minSize
        self.maxSize = maxSize
        self.looseMatch = looseMatch
        self._is_running = True

    def run(self):
        files_found = False
        for root, dirs, files in os.walk(self.rootDir):
            if not self._is_running:
                break
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_size = os.path.getsize(file_path)
                except OSError:
                    continue  # Skip inaccessible files

                # Check if file matches the criteria
                if ((self.looseMatch and self.fileName.lower() in file.lower()) or 
                    (file.lower() == self.fileName.lower() + (self.fileFormat.lower() if self.fileFormat else ''))) and \
                    (self.minSize <= file_size <= self.maxSize):
                    self.file_found_signal.emit(file_path)
                    files_found = True

        self.search_complete_signal.emit(files_found)

    def stop(self):
        self._is_running = False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ExplorAI - Votre assistant de recherche intelligent")
        self.setGeometry(100, 100, 500, 500)
        self.setWindowIcon(QIcon('path/to/icon.png'))  # Assurez-vous que le chemin est correct
        self.initUI()
        self.found_files = []

    def initUI(self):
        self.setStyleSheet("""
            QWidget {
                font-size: 16px;
                font-family: 'Roboto', sans-serif;
                background-color: #f0f2f5;
            }
            QLabel {
                color: #34495e;
                font-weight: bold;
                margin-bottom: 10px;
            }
            QLineEdit, QComboBox, QCheckBox, QSpinBox {
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                padding: 10px;
                background-color: #ffffff;
                font-size: 15px;
            }
            QLineEdit:focus, QComboBox:focus, QCheckBox:focus, QSpinBox:focus {
                border: 1px solid #3498db;
                outline: none;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 15px;
                box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1f5f8a;
            }
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                text-align: center;
                font-size: 15px;
                color: white;
                background-color: #ecf0f1;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                width: 20px;
            }
        """)

        layout = QVBoxLayout()
        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        centralWidget.setLayout(layout)

        layout.addWidget(QLabel("Trouvez vos fichiers rapidement avec ExplorAI"))

        self.lineEditFileName = QLineEdit(self)
        layout.addWidget(QLabel("Nom du fichier :"))
        layout.addWidget(self.lineEditFileName)

        self.checkBoxLooseMatch = QCheckBox("Recherche non stricte du nom", self)
        layout.addWidget(self.checkBoxLooseMatch)

        self.comboBoxFileFormat = QComboBox(self)
        self.comboBoxFileFormat.addItem("")  # Item vide pour format optionnel
        self.comboBoxFileFormat.addItems(['.png', '.jpg', '.txt', '.pdf'])
        layout.addWidget(QLabel("Format du fichier (optionnel) :"))
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

        self.progressBar = QProgressBar(self)
        layout.addWidget(self.progressBar)
        self.progressBar.setVisible(False)

    def startSearch(self):
        self.found_files.clear()
        self.progressBar.setVisible(True)
        self.progressBar.setRange(0, 0)  # Indeterminate state
        self.lineEditFileName.setStyleSheet("")  # Reset border color

        fileName = self.lineEditFileName.text()
        fileFormat = self.comboBoxFileFormat.currentText() if self.comboBoxFileFormat.currentText() != "" else None
        minSize = self.spinBoxMinSize.value() * 1024
        maxSize = self.spinBoxMaxSize.value() * 1024
        looseMatch = self.checkBoxLooseMatch.isChecked()
        rootDir = '/'  # Adjust this to your system if needed

        self.search_thread = FileSearchThread(rootDir, fileName, fileFormat, minSize, maxSize, looseMatch)
        self.search_thread.file_found_signal.connect(self.fileFound)
        self.search_thread.search_complete_signal.connect(self.searchComplete)
        self.search_thread.start()

    def fileFound(self, filePath):
        self.found_files.append(filePath)

    def searchComplete(self, files_found):
        self.progressBar.setVisible(False)
        if self.found_files:
            results = "\n".join(self.found_files)
            QMessageBox.information(self, "Fichiers Trouvés", f"Chemin des fichiers :\n{results}")
        else:
            self.lineEditFileName.setStyleSheet("border: 2px solid red;")
            if not files_found:
                QMessageBox.warning(self, "Aucun Résultat", "Fichier non trouvé. Veuillez vérifier le nom et réessayer.")
            else:
                QMessageBox.warning(self, "Recherche interrompue", "La recherche a été interrompue.")

    def closeEvent(self, event):
        if hasattr(self, 'search_thread') and self.search_thread.isRunning():
            self.search_thread.stop()
            self.search_thread.wait()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
