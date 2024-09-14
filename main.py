import sys
import os
import mimetypes
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit, 
                             QComboBox, QPushButton, QVBoxLayout, QWidget, 
                             QMessageBox, QCheckBox, QSpinBox, QProgressBar, 
                             QMenuBar, QAction, QStatusBar, QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QListWidget, QGroupBox, QFormLayout, QMenu, QDateEdit, QHBoxLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QRect, QEasingCurve, QDateTime, QTranslator, QLocale, QLibraryInfo
from PyQt5.QtGui import QIcon, QDesktopServices, QFont
from PyQt5.Qt import QUrl, QSystemTrayIcon, QStyle

# Thread pour la recherche de fichiers
class FileSearchThread(QThread):
    file_found_signal = pyqtSignal(str)
    search_complete_signal = pyqtSignal(bool)

    def __init__(self, directories, fileName, fileFormat, minSize, maxSize, looseMatch, dateFrom, dateTo):
        super().__init__()
        self.directories = directories
        self.fileName = fileName
        self.fileFormat = fileFormat
        self.minSize = minSize
        self.maxSize = maxSize
        self.looseMatch = looseMatch
        self.dateFrom = dateFrom
        self.dateTo = dateTo
        self._is_running = True

    def run(self):
        files_found = False
        for rootDir in self.directories:
            for root, dirs, files in os.walk(rootDir):
                if not self._is_running:
                    break
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_size = os.path.getsize(file_path)
                        file_mtime = os.path.getmtime(file_path)
                    except OSError:
                        continue

                    if self.fileFormat and not file.lower().endswith(self.fileFormat.lower()):
                        continue

                    file_name_without_extension = os.path.splitext(file)[0]
                    file_date = QDateTime.fromSecsSinceEpoch(int(file_mtime)).date()

                    if ((self.looseMatch and self.fileName.lower() in file_name_without_extension.lower()) or 
                        (file_name_without_extension.lower() == self.fileName.lower())) and \
                        (self.minSize <= file_size <= self.maxSize) and \
                        (self.dateFrom <= file_date <= self.dateTo):
                        self.file_found_signal.emit(file_path)
                        files_found = True

        self.search_complete_signal.emit(files_found)

    def stop(self):
        self._is_running = False

# Fenêtre principale
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Finder - Recherche intelligente de fichiers")
        self.setGeometry(100, 100, 850, 550)  # Fenêtre plus petite par défaut
        self.setWindowIcon(QIcon('logo.png'))
        self.current_theme = 'light'
        self.selected_directories = []
        self.translator = QTranslator()
        self.current_language = 'fr'
        self.initUI()
        self.found_files = []


    def initUI(self):
        self.createMenuBar()
        self.createStatusBar()
        self.createSystemTray()

        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(20, 20, 20, 20)  # Marges réduites pour un look plus compact
        self.centralWidget.setLayout(self.layout)

        # Titre principal
        self.labelTitle = QLabel("File Finder")
        self.labelTitle.setAlignment(Qt.AlignCenter)
        self.labelTitle.setFont(QFont("Arial", 24, QFont.Bold))  # Taille de police ajustée
        self.labelTitle.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        self.layout.addWidget(self.labelTitle)

        # Sous-titre
        self.labelSubtitle = QLabel("Recherche intelligente et rapide de vos fichiers")
        self.labelSubtitle.setAlignment(Qt.AlignCenter)
        self.labelSubtitle.setFont(QFont("Arial", 12))
        self.labelSubtitle.setStyleSheet("color: #7f8c8d; margin-bottom: 20px;")
        self.layout.addWidget(self.labelSubtitle)

        self.addSeparator()

        # Dossiers sélectionnés
        self.directoryListWidget = QListWidget(self)
        self.layout.addWidget(QLabel("Dossiers sélectionnés :", self.centralWidget))
        self.layout.addWidget(self.directoryListWidget)

        # Bouton de sélection de dossiers
        self.selectDirButton = QPushButton("Sélectionner des dossiers", self)
        self.selectDirButton.setStyleSheet(self.get_button_stylesheet())
        self.selectDirButton.clicked.connect(self.selectDirectories)
        self.layout.addWidget(self.selectDirButton)

        self.addSeparator()

        # Champs pour entrer le nom du fichier à rechercher
        self.lineEditFileName = QLineEdit(self)
        self.lineEditFileName.setPlaceholderText("Entrez le nom du fichier...")
        self.lineEditFileName.setStyleSheet(self.get_input_stylesheet())
        self.layout.addWidget(QLabel("Nom du fichier :", self.centralWidget))
        self.layout.addWidget(self.lineEditFileName)

        self.addSeparator()

        # Bouton pour afficher/masquer les options avancées
        self.toggleAdvancedOptionsButton = QPushButton("Afficher les options avancées", self)
        self.toggleAdvancedOptionsButton.setCheckable(True)
        self.toggleAdvancedOptionsButton.setStyleSheet(self.get_toggle_button_stylesheet())
        self.toggleAdvancedOptionsButton.clicked.connect(self.toggleAdvancedOptions)
        self.layout.addWidget(self.toggleAdvancedOptionsButton)

        # Options avancées
        self.optionalGroupBox = QGroupBox("Options avancées")
        self.optionalGroupBox.setStyleSheet("QGroupBox { font-size: 14px; font-weight: bold; margin-top: 10px; }")
        self.optionalLayout = QFormLayout()

        # Format de fichier
        self.comboBoxFileFormat = QComboBox(self)
        self.comboBoxFileFormat.setStyleSheet(self.get_input_stylesheet())
        self.comboBoxFileFormat.addItem("")
        self.comboBoxFileFormat.addItems(['.png', '.jpg', '.txt', '.pdf'])
        self.optionalLayout.addRow(QLabel("Format du fichier (optionnel) :", self.centralWidget), self.comboBoxFileFormat)

        # Taille du fichier
        self.spinBoxMinSize = QSpinBox(self)
        self.spinBoxMinSize.setMaximum(1000000)
        self.spinBoxMinSize.setStyleSheet(self.get_input_stylesheet())
        self.optionalLayout.addRow(QLabel("Taille minimale du fichier (Ko) :", self.centralWidget), self.spinBoxMinSize)

        self.spinBoxMaxSize = QSpinBox(self)
        self.spinBoxMaxSize.setMaximum(1000000)
        self.spinBoxMaxSize.setValue(1000000)
        self.spinBoxMaxSize.setStyleSheet(self.get_input_stylesheet())
        self.optionalLayout.addRow(QLabel("Taille maximale du fichier (Ko) :", self.centralWidget), self.spinBoxMaxSize)

        # Date de création
        self.dateEditFrom = QDateEdit(self)
        self.dateEditFrom.setCalendarPopup(True)
        self.dateEditFrom.setDate(QDateTime.currentDateTime().date().addYears(-1))
        self.dateEditFrom.setStyleSheet(self.get_input_stylesheet())
        self.optionalLayout.addRow(QLabel("Date de création à partir de :", self.centralWidget), self.dateEditFrom)

        self.dateEditTo = QDateEdit(self)
        self.dateEditTo.setCalendarPopup(True)
        self.dateEditTo.setDate(QDateTime.currentDateTime().date())
        self.dateEditTo.setStyleSheet(self.get_input_stylesheet())
        self.optionalLayout.addRow(QLabel("Date de création jusqu'à :", self.centralWidget), self.dateEditTo)

        # Option de recherche non stricte
        self.checkBoxLooseMatch = QCheckBox("Recherche non stricte du nom", self)
        self.checkBoxLooseMatch.setStyleSheet(self.get_checkbox_stylesheet())
        self.optionalLayout.addRow(self.checkBoxLooseMatch)

        self.optionalGroupBox.setLayout(self.optionalLayout)
        self.optionalGroupBox.setVisible(False)  # Cacher les options avancées par défaut
        self.layout.addWidget(self.optionalGroupBox)

        self.addSeparator()

        # Bouton de recherche
        self.pushButtonSearch = QPushButton("Chercher", self)
        self.pushButtonSearch.setStyleSheet(self.get_primary_button_stylesheet())
        self.pushButtonSearch.clicked.connect(self.startSearch)
        self.layout.addWidget(self.pushButtonSearch)

        # Barre de progression
        self.progressBar = QProgressBar(self)
        self.progressBar.setStyleSheet(self.get_progressbar_stylesheet())
        self.layout.addWidget(self.progressBar)
        self.progressBar.setVisible(False)

        self.addSeparator()

        # Champ de texte pour filtrer les résultats
        self.filterLineEdit = QLineEdit(self)
        self.filterLineEdit.setPlaceholderText("Filtrer les résultats...")
        self.filterLineEdit.setStyleSheet(self.get_input_stylesheet())
        self.filterLineEdit.setFixedHeight(30)
        self.filterLineEdit.textChanged.connect(self.filterResults)
        self.layout.addWidget(self.filterLineEdit)

        # Tableau pour afficher les résultats de recherche
        self.resultTable = QTableWidget(self)
        self.resultTable.setColumnCount(1)
        self.resultTable.setHorizontalHeaderLabels(["Chemin des fichiers"])
        self.resultTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.resultTable.setContextMenuPolicy(Qt.CustomContextMenu)
        self.resultTable.customContextMenuRequested.connect(self.showContextMenu)
        self.resultTable.itemSelectionChanged.connect(self.displayFileDetails)
        self.resultTable.setStyleSheet(self.get_table_stylesheet())
        self.resultTable.setFixedHeight(150)  # Réduire la hauteur du tableau pour correspondre à la fenêtre plus petite
        self.layout.addWidget(self.resultTable)

        # Groupe pour afficher les détails du fichier sélectionné
        self.detailsGroupBox = QGroupBox("Détails du fichier")
        self.detailsGroupBox.setStyleSheet(self.get_groupbox_stylesheet())
        self.detailsLayout = QFormLayout()

        # Étiquettes pour afficher les détails du fichier
        self.filePathLabel = QLabel("")
        self.fileSizeLabel = QLabel("")
        self.fileCreatedLabel = QLabel("")
        self.fileModifiedLabel = QLabel("")

        self.detailsLayout.addRow(QLabel("Chemin du fichier :"), self.filePathLabel)
        self.detailsLayout.addRow(QLabel("Taille du fichier :"), self.fileSizeLabel)
        self.detailsLayout.addRow(QLabel("Date de création :"), self.fileCreatedLabel)
        self.detailsLayout.addRow(QLabel("Date de modification :"), self.fileModifiedLabel)

        self.detailsGroupBox.setLayout(self.detailsLayout)
        self.layout.addWidget(self.detailsGroupBox)

        self.layout.addStretch()

        self.animateWidgets()

    def createMenuBar(self):
        menuBar = QMenuBar(self)
        self.setMenuBar(menuBar)

        fileMenu = menuBar.addMenu("Fichier")

        saveSettingsAction = QAction("Sauvegarder les paramètres", self)
        saveSettingsAction.triggered.connect(self.saveSettings)
        fileMenu.addAction(saveSettingsAction)

        loadSettingsAction = QAction("Charger les paramètres", self)
        loadSettingsAction.triggered.connect(self.loadSettings)
        fileMenu.addAction(loadSettingsAction)

        themeMenu = menuBar.addMenu("Thème")

        lightThemeAction = QAction("Thème Clair", self)
        lightThemeAction.triggered.connect(lambda: self.switchTheme('light'))
        themeMenu.addAction(lightThemeAction)

        darkThemeAction = QAction("Thème Sombre", self)
        darkThemeAction.triggered.connect(lambda: self.switchTheme('dark'))
        themeMenu.addAction(darkThemeAction)

        blueThemeAction = QAction("Thème Bleu", self)
        blueThemeAction.triggered.connect(lambda: self.switchTheme('blue'))
        themeMenu.addAction(blueThemeAction)

        languageMenu = menuBar.addMenu("Langue")

        frenchAction = QAction("Français", self)
        frenchAction.triggered.connect(lambda: self.switchLanguage('fr'))
        languageMenu.addAction(frenchAction)

        englishAction = QAction("English", self)
        englishAction.triggered.connect(lambda: self.switchLanguage('en'))
        languageMenu.addAction(englishAction)

    def createStatusBar(self):
        self.statusBar = QStatusBar(self)
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Prêt")

    def createSystemTray(self):
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.trayIcon.show()

    def toggleAdvancedOptions(self):
        if self.toggleAdvancedOptionsButton.isChecked():
            self.optionalGroupBox.setVisible(True)
            self.toggleAdvancedOptionsButton.setText("Masquer les options avancées")
        else:
            self.optionalGroupBox.setVisible(False)
            self.toggleAdvancedOptionsButton.setText("Afficher les options avancées")

    def light_theme_stylesheet(self):
        return """
            QWidget {
                font-size: 14px;
                font-family: 'Roboto', sans-serif;
                background-color: #f7f7f7;
                color: #2c3e50;
            }
            QLabel {
                color: #34495e;
            }
        """

    def dark_theme_stylesheet(self):
        return """
            QWidget {
                font-size: 14px;
                font-family: 'Roboto', sans-serif;
                background-color: #2c3e50;
                color: #ecf0f1;
            }
            QLabel {
                color: #ecf0f1;
            }
        """

    def blue_theme_stylesheet(self):
        return """
            QWidget {
                font-size: 14px;
                font-family: 'Roboto', sans-serif;
                background-color: #e3f2fd;
                color: #2c3e50;
            }
            QLabel {
                color: #1e88e5;
            }
        """

    def get_button_stylesheet(self):
        return """
            QPushButton {
                background-color: #2980b9;
                color: white;
                border-radius: 8px;
                padding: 8px 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1f5f8a;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """

    def get_primary_button_stylesheet(self):
        return """
            QPushButton {
                background-color: #27ae60;
                color: white;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """

    def get_toggle_button_stylesheet(self):
        return """
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                border-radius: 8px;
                padding: 10px 15px;
                font-size: 14px;
            }
            QPushButton:checked {
                background-color: #27ae60;
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
        """

    def get_input_stylesheet(self):
        return """
            QLineEdit, QComboBox, QSpinBox, QDateEdit {
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                padding: 8px;
                background-color: #ecf0f1;
                font-size: 14px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus {
                border: 2px solid #2980b9;
                outline: none;
            }
        """

    def get_checkbox_stylesheet(self):
        return """
            QCheckBox {
                font-size: 14px;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:checked {
                background-color: #27ae60;
                border: 1px solid #27ae60;
            }
            QCheckBox::indicator:unchecked {
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
            }
        """

    def get_progressbar_stylesheet(self):
        return """
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                text-align: center;
                font-size: 14px;
                color: white;
                background-color: #f0f2f5;
            }
            QProgressBar::chunk {
                background-color: #27ae60;
                width: 20px;
            }
        """

    def get_table_stylesheet(self):
        return """
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: #2980b9;
                color: white;
                padding: 5px;
                border: 1px solid #2980b9;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """

    def get_groupbox_stylesheet(self):
        return """
            QGroupBox {
                background-color: #f0f2f5;
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                margin-top: 10px;
            }
        """

    def addSeparator(self):
        separator = QFrame(self)
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(separator)

    def animateWidgets(self):
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if widget:
                animation = QPropertyAnimation(widget, b"geometry")
                animation.setDuration(400)
                animation.setStartValue(QRect(widget.x(), widget.y() - 30, widget.width(), widget.height()))
                animation.setEndValue(QRect(widget.x(), widget.y(), widget.width(), widget.height()))
                animation.setEasingCurve(QEasingCurve.OutQuad)
                animation.start(QPropertyAnimation.DeleteWhenStopped)

    def selectDirectories(self):
        directories = QFileDialog.getExistingDirectory(self, "Sélectionner des dossiers", "", QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks | QFileDialog.Option())
        if directories:
            self.selected_directories.append(directories)
            self.directoryListWidget.addItem(directories)

    def startSearch(self):
        if not self.selected_directories:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner au moins un dossier pour la recherche.")
            return
        
        self.disableInputs(True)
        self.statusBar.showMessage("Recherche en cours...")
        self.found_files.clear()
        self.resultTable.setRowCount(0)
        self.progressBar.setVisible(True)
        self.progressBar.setRange(0, 0)

        fileName = self.lineEditFileName.text()
        fileFormat = self.comboBoxFileFormat.currentText() if self.comboBoxFileFormat.currentText() != "" else None
        minSize = self.spinBoxMinSize.value() * 1024
        maxSize = self.spinBoxMaxSize.value() * 1024
        looseMatch = self.checkBoxLooseMatch.isChecked()
        dateFrom = self.dateEditFrom.date()
        dateTo = self.dateEditTo.date()

        self.search_thread = FileSearchThread(self.selected_directories, fileName, fileFormat, minSize, maxSize, looseMatch, dateFrom, dateTo)
        self.search_thread.file_found_signal.connect(self.fileFound)
        self.search_thread.search_complete_signal.connect(self.searchComplete)
        self.search_thread.start()

    def disableInputs(self, disable):
        self.lineEditFileName.setDisabled(disable)
        self.comboBoxFileFormat.setDisabled(disable)
        self.spinBoxMinSize.setDisabled(disable)
        self.spinBoxMaxSize.setDisabled(disable)
        self.checkBoxLooseMatch.setDisabled(disable)
        self.pushButtonSearch.setDisabled(disable)
        self.selectDirButton.setDisabled(disable)
        self.dateEditFrom.setDisabled(disable)
        self.dateEditTo.setDisabled(disable)

    def fileFound(self, filePath):
        self.found_files.append(filePath)
        row_position = self.resultTable.rowCount()
        self.resultTable.insertRow(row_position)
        
        icon = self.getFileIcon(filePath)
        item = QTableWidgetItem(icon, filePath)
        self.resultTable.setItem(row_position, 0, item)

    def searchComplete(self, files_found):
        self.progressBar.setVisible(False)
        self.disableInputs(False)
        if not self.found_files:
            self.lineEditFileName.setStyleSheet("border: 2px solid red;")
            QMessageBox.warning(self, "Aucun Résultat", "Fichier non trouvé. Veuillez vérifier le nom et réessayer.")
            self.statusBar.showMessage("Recherche terminée : aucun fichier trouvé")
        else:
            self.statusBar.showMessage("Recherche terminée : fichiers trouvés")
            self.trayIcon.showMessage("File Finder", "Recherche terminée : fichiers trouvés", QSystemTrayIcon.Information, 5000)

    def switchTheme(self, theme):
        self.current_theme = theme
        if theme == 'light':
            self.setStyleSheet(self.light_theme_stylesheet())
        elif theme == 'dark':
            self.setStyleSheet(self.dark_theme_stylesheet())
        elif theme == 'blue':
            self.setStyleSheet(self.blue_theme_stylesheet())

    def saveSettings(self):
        settings = {
            "directories": self.selected_directories,
            "fileName": self.lineEditFileName.text(),
            "fileFormat": self.comboBoxFileFormat.currentText(),
            "minSize": self.spinBoxMinSize.value(),
            "maxSize": self.spinBoxMaxSize.value(),
            "looseMatch": self.checkBoxLooseMatch.isChecked(),
            "dateFrom": self.dateEditFrom.date().toString(Qt.ISODate),
            "dateTo": self.dateEditTo.date().toString(Qt.ISODate)
        }
        file_name, _ = QFileDialog.getSaveFileName(self, "Sauvegarder les paramètres", "", "JSON Files (*.json)")
        if file_name:
            with open(file_name, 'w') as file:
                json.dump(settings, file)
            QMessageBox.information(self, "Succès", "Paramètres sauvegardés avec succès.")

    def loadSettings(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Charger les paramètres", "", "JSON Files (*.json)")
        if file_name:
            with open(file_name, 'r') as file:
                settings = json.load(file)
                self.selected_directories = settings["directories"]
                self.directoryListWidget.clear()
                self.directoryListWidget.addItems(self.selected_directories)
                self.lineEditFileName.setText(settings["fileName"])
                self.comboBoxFileFormat.setCurrentText(settings["fileFormat"])
                self.spinBoxMinSize.setValue(settings["minSize"])
                self.spinBoxMaxSize.setValue(settings["maxSize"])
                self.checkBoxLooseMatch.setChecked(settings["looseMatch"])
                self.dateEditFrom.setDate(QDateTime.fromString(settings["dateFrom"], Qt.ISODate).date())
                self.dateEditTo.setDate(QDateTime.fromString(settings["dateTo"], Qt.ISODate).date())
            QMessageBox.information(self, "Succès", "Paramètres chargés avec succès.")

    def switchLanguage(self, language_code):
        if language_code == 'fr':
            self.translator.load(QLibraryInfo.location(QLibraryInfo.TranslationsPath) + "/qt_fr.qm")
        elif language_code == 'en':
            self.translator.load(QLibraryInfo.location(QLibraryInfo.TranslationsPath) + "/qt_en.qm")

        QApplication.instance().installTranslator(self.translator)
        self.retranslateUi()

    def retranslateUi(self):
        self.setWindowTitle("File Finder - Recherche intelligente de fichiers")
        self.labelTitle.setText("File Finder")
        self.labelSubtitle.setText("Recherche intelligente et rapide de vos fichiers")
        self.selectDirButton.setText("Sélectionner des dossiers")
        self.lineEditFileName.setPlaceholderText("Entrez le nom du fichier...")
        self.optionalGroupBox.setTitle("Options avancées")
        self.pushButtonSearch.setText("Chercher")
        self.filterLineEdit.setPlaceholderText("Filtrer les résultats...")
        self.resultTable.setHorizontalHeaderLabels(["Chemin des fichiers"])
        self.detailsGroupBox.setTitle("Détails du fichier")
        self.statusBar.showMessage("Prêt")

    def closeEvent(self, event):
        if hasattr(self, 'search_thread') and self.search_thread.isRunning():
            self.search_thread.stop()
            self.search_thread.wait()
        event.accept()

    def getFileIcon(self, filePath):
        mime_type, _ = mimetypes.guess_type(filePath)
        if mime_type:
            if mime_type.startswith("image"):
                return QIcon("path/to/image/icon.png")
            elif mime_type.startswith("text"):
                return QIcon("path/to/text/icon.png")
            elif mime_type.startswith("application/pdf"):
                return QIcon("path/to/pdf/icon.png")
        return QIcon("path/to/default/icon.png")

    def showContextMenu(self, position):
        menu = QMenu()
        openAction = menu.addAction("Ouvrir le fichier")
        openFolderAction = menu.addAction("Ouvrir le dossier contenant")
        copyPathAction = menu.addAction("Copier le chemin du fichier")

        action = menu.exec_(self.resultTable.viewport().mapToGlobal(position))

        if action == openAction:
            self.openFile()
        elif action == openFolderAction:
            self.openContainingFolder()
        elif action == copyPathAction:
            self.copyFilePath()

    def openFile(self):
        selected_item = self.resultTable.currentItem()
        if selected_item:
            QDesktopServices.openUrl(QUrl.fromLocalFile(selected_item.text()))

    def openContainingFolder(self):
        selected_item = self.resultTable.currentItem()
        if selected_item:
            folder_path = os.path.dirname(selected_item.text())
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder_path))

    def copyFilePath(self):
        selected_item = self.resultTable.currentItem()
        if selected_item:
            clipboard = QApplication.clipboard()
            clipboard.setText(selected_item.text())

    def filterResults(self, text):
        for row in range(self.resultTable.rowCount()):
            item = self.resultTable.item(row, 0)
            if text.lower() in item.text().lower():
                self.resultTable.setRowHidden(row, False)
            else:
                self.resultTable.setRowHidden(row, True)

    def displayFileDetails(self):
        selected_item = self.resultTable.currentItem()
        if selected_item:
            file_path = selected_item.text()
            file_info = os.stat(file_path)

            self.filePathLabel.setText(file_path)
            self.fileSizeLabel.setText(f"{file_info.st_size / 1024:.2f} Ko")
            self.fileCreatedLabel.setText(QDateTime.fromSecsSinceEpoch(int(file_info.st_ctime)).toString(Qt.DefaultLocaleLongDate))
            self.fileModifiedLabel.setText(QDateTime.fromSecsSinceEpoch(int(file_info.st_mtime)).toString(Qt.DefaultLocaleLongDate))

def main():
    app = QApplication(sys.argv)

    translator = QTranslator()
    translator.load(QLibraryInfo.location(QLibraryInfo.TranslationsPath) + "/qt_fr.qm")
    app.installTranslator(translator)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()



