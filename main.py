import sys
import os
import mimetypes
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit, 
                             QComboBox, QPushButton, QVBoxLayout, QWidget, 
                             QMessageBox, QCheckBox, QSpinBox, QProgressBar, 
                             QMenuBar, QAction, QStatusBar, QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QListWidget, QGroupBox, QFormLayout, QMenu, QDateEdit, QHBoxLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QRect, QEasingCurve, QDateTime, QTranslator, QLocale, QLibraryInfo
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.Qt import QUrl, QSystemTrayIcon, QStyle

# Classe qui gère la recherche des fichiers dans un thread séparé
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.tr("ExplorAI - Votre assistant de recherche intelligent"))
        self.setGeometry(100, 100, 1200, 700)
        self.setWindowIcon(QIcon('path/to/icon.png'))
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
        self.centralWidget.setLayout(self.layout)

        self.labelTitle = QLabel(self.tr("Trouvez vos fichiers rapidement avec ExplorAI"))
        self.labelTitle.setAlignment(Qt.AlignCenter)
        self.labelTitle.setStyleSheet("font-size: 28px; font-weight: bold; color: #2c3e50; margin-bottom: 30px;")
        self.layout.addWidget(self.labelTitle)

        self.addSeparator()

        # Nouvelle disposition en grille pour les entrées principales
        gridLayout = QHBoxLayout()
        self.layout.addLayout(gridLayout)

        # Répertoires sélectionnés
        self.directoryListWidget = QListWidget(self)
        self.directoryListWidget.setStyleSheet("font-size: 14px;")
        gridLayout.addWidget(self.directoryListWidget)

        # Bouton pour sélectionner les répertoires
        self.selectDirButton = QPushButton(self.tr("Sélectionner des dossiers"), self)
        self.selectDirButton.setStyleSheet("font-size: 16px; padding: 10px;")
        self.selectDirButton.clicked.connect(self.selectDirectories)
        gridLayout.addWidget(self.selectDirButton)

        self.addSeparator()

        # Champ pour le nom de fichier
        self.lineEditFileName = QLineEdit(self)
        self.lineEditFileName.setPlaceholderText(self.tr("Entrez le nom du fichier..."))
        self.layout.addWidget(QLabel(self.tr("Nom du fichier :"), self.centralWidget))
        self.layout.addWidget(self.lineEditFileName)

        self.addSeparator()

        # Groupe des options avancées
        self.optionalGroupBox = QGroupBox(self.tr("Options avancées"))
        self.optionalGroupBox.setStyleSheet("QGroupBox { font-size: 16px; font-weight: bold; }")
        self.optionalLayout = QFormLayout()

        self.comboBoxFileFormat = QComboBox(self)
        self.comboBoxFileFormat.addItem("")
        self.comboBoxFileFormat.addItems(['.png', '.jpg', '.txt', '.pdf'])
        self.optionalLayout.addRow(QLabel(self.tr("Format du fichier (optionnel) :"), self.centralWidget), self.comboBoxFileFormat)

        self.spinBoxMinSize = QSpinBox(self)
        self.spinBoxMinSize.setMaximum(1000000)
        self.optionalLayout.addRow(QLabel(self.tr("Taille minimale du fichier (Ko) :"), self.centralWidget), self.spinBoxMinSize)

        self.spinBoxMaxSize = QSpinBox(self)
        self.spinBoxMaxSize.setMaximum(1000000)
        self.spinBoxMaxSize.setValue(1000000)
        self.optionalLayout.addRow(QLabel(self.tr("Taille maximale du fichier (Ko) :"), self.centralWidget), self.spinBoxMaxSize)

        self.dateEditFrom = QDateEdit(self)
        self.dateEditFrom.setCalendarPopup(True)
        self.dateEditFrom.setDate(QDateTime.currentDateTime().date().addYears(-1))
        self.optionalLayout.addRow(QLabel(self.tr("Date de création à partir de :"), self.centralWidget), self.dateEditFrom)

        self.dateEditTo = QDateEdit(self)
        self.dateEditTo.setCalendarPopup(True)
        self.dateEditTo.setDate(QDateTime.currentDateTime().date())
        self.optionalLayout.addRow(QLabel(self.tr("Date de création jusqu'à :"), self.centralWidget), self.dateEditTo)

        self.checkBoxLooseMatch = QCheckBox(self.tr("Recherche non stricte du nom"), self)
        self.optionalLayout.addRow(self.checkBoxLooseMatch)

        self.optionalGroupBox.setLayout(self.optionalLayout)
        self.optionalGroupBox.setCheckable(True)
        self.optionalGroupBox.setChecked(False)
        self.layout.addWidget(self.optionalGroupBox)

        self.addSeparator()

        # Bouton de recherche avec icône
        self.pushButtonSearch = QPushButton(self.tr("Chercher"), self)
        self.pushButtonSearch.setStyleSheet("margin-top: 15px; padding: 15px; font-size: 18px; background-color: #2980b9; color: white; border-radius: 10px;")
        self.pushButtonSearch.setIcon(QIcon('path/to/search_icon.png'))  # Ajoutez une icône de recherche
        self.pushButtonSearch.clicked.connect(self.startSearch)
        self.layout.addWidget(self.pushButtonSearch)

        self.progressBar = QProgressBar(self)
        self.progressBar.setStyleSheet("margin-top: 20px; height: 20px;")
        self.layout.addWidget(self.progressBar)
        self.progressBar.setVisible(False)

        self.addSeparator()

        self.filterLineEdit = QLineEdit(self)
        self.filterLineEdit.setPlaceholderText(self.tr("Filtrer les résultats..."))
        self.filterLineEdit.textChanged.connect(self.filterResults)
        self.layout.addWidget(self.filterLineEdit)

        self.resultTable = QTableWidget(self)
        self.resultTable.setColumnCount(1)
        self.resultTable.setHorizontalHeaderLabels([self.tr("Chemin des fichiers")])
        self.resultTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.resultTable.setContextMenuPolicy(Qt.CustomContextMenu)
        self.resultTable.customContextMenuRequested.connect(self.showContextMenu)
        self.resultTable.itemSelectionChanged.connect(self.displayFileDetails)
        self.layout.addWidget(self.resultTable)

        # Nouveau panneau des détails avec des sections plus visibles
        self.detailsGroupBox = QGroupBox(self.tr("Détails du fichier"))
        self.detailsGroupBox.setStyleSheet("QGroupBox { font-size: 16px; font-weight: bold; }")
        self.detailsLayout = QFormLayout()

        self.filePathLabel = QLabel("")
        self.fileSizeLabel = QLabel("")
        self.fileCreatedLabel = QLabel("")
        self.fileModifiedLabel = QLabel("")

        self.detailsLayout.addRow(QLabel(self.tr("Chemin du fichier :")), self.filePathLabel)
        self.detailsLayout.addRow(QLabel(self.tr("Taille du fichier :")), self.fileSizeLabel)
        self.detailsLayout.addRow(QLabel(self.tr("Date de création :")), self.fileCreatedLabel)
        self.detailsLayout.addRow(QLabel(self.tr("Date de modification :")), self.fileModifiedLabel)

        self.detailsGroupBox.setLayout(self.detailsLayout)
        self.layout.addWidget(self.detailsGroupBox)

        self.layout.addStretch()

        self.animateWidgets()

    def createMenuBar(self):
        menuBar = QMenuBar(self)
        self.setMenuBar(menuBar)

        fileMenu = menuBar.addMenu(self.tr("Fichier"))

        saveSettingsAction = QAction(self.tr("Sauvegarder les paramètres"), self)
        saveSettingsAction.triggered.connect(self.saveSettings)
        fileMenu.addAction(saveSettingsAction)

        loadSettingsAction = QAction(self.tr("Charger les paramètres"), self)
        loadSettingsAction.triggered.connect(self.loadSettings)
        fileMenu.addAction(loadSettingsAction)

        themeMenu = menuBar.addMenu(self.tr("Thème"))

        lightThemeAction = QAction(self.tr("Thème Clair"), self)
        lightThemeAction.triggered.connect(lambda: self.switchTheme('light'))
        themeMenu.addAction(lightThemeAction)

        darkThemeAction = QAction(self.tr("Thème Sombre"), self)
        darkThemeAction.triggered.connect(lambda: self.switchTheme('dark'))
        themeMenu.addAction(darkThemeAction)

        blueThemeAction = QAction(self.tr("Thème Bleu"), self)
        blueThemeAction.triggered.connect(lambda: self.switchTheme('blue'))
        themeMenu.addAction(blueThemeAction)

        languageMenu = menuBar.addMenu(self.tr("Langue"))

        frenchAction = QAction("Français", self)
        frenchAction.triggered.connect(lambda: self.switchLanguage('fr'))
        languageMenu.addAction(frenchAction)

        englishAction = QAction("English", self)
        englishAction.triggered.connect(lambda: self.switchLanguage('en'))
        languageMenu.addAction(englishAction)

    def createStatusBar(self):
        self.statusBar = QStatusBar(self)
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage(self.tr("Prêt"))

    def createSystemTray(self):
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.trayIcon.show()

    def light_theme_stylesheet(self):
        return """
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
            QLineEdit, QComboBox, QCheckBox, QSpinBox, QDateEdit {
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                padding: 10px;
                background-color: #ffffff;
                font-size: 15px;
            }
            QLineEdit:focus, QComboBox:focus, QCheckBox:focus, QSpinBox:focus, QDateEdit:focus {
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
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                font-size: 15px;
            }
            QGroupBox {
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                padding: 10px;
                font-size: 15px;
                margin-top: 15px;
            }
            QGroupBox:title {
                subcontrol-origin: margin;
                padding: 0 5px;
                background-color: #bdc3c7;
                border-radius: 5px;
            }
        """

    def dark_theme_stylesheet(self):
        return """
            QWidget {
                font-size: 16px;
                font-family: 'Roboto', sans-serif;
                background-color: #2c3e50;
            }
            QLabel {
                color: #ecf0f1;
                font-weight: bold;
                margin-bottom: 10px;
            }
            QLineEdit, QComboBox, QCheckBox, QSpinBox, QDateEdit {
                border: 1px solid #95a5a6;
                border-radius: 8px;
                padding: 10px;
                background-color: #34495e;
                color: #ecf0f1;
                font-size: 15px;
            }
            QLineEdit:focus, QComboBox:focus, QCheckBox:focus, QSpinBox:focus, QDateEdit:focus {
                border: 1px solid #1abc9c;
                outline: none;
            }
            QPushButton {
                background-color: #1abc9c;
                color: white;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #16a085;
            }
            QPushButton:pressed {
                background-color: #12876f;
            }
            QProgressBar {
                border: 1px solid #95a5a6;
                border-radius: 8px;
                text-align: center;
                font-size: 15px;
                color: white;
                background-color: #34495e;
            }
            QProgressBar::chunk {
                background-color: #1abc9c;
                width: 20px;
            }
            QTableWidget {
                background-color: #34495e;
                border: 1px solid #95a5a6;
                border-radius: 8px;
                font-size: 15px;
                color: #ecf0f1;
            }
            QGroupBox {
                background-color: #2c3e50;
                border: 1px solid #95a5a6;
                border-radius: 8px;
                padding: 10px;
                font-size: 15px;
                margin-top: 15px;
            }
            QGroupBox:title {
                subcontrol-origin: margin;
                padding: 0 5px;
                background-color: #16a085;
                border-radius: 5px;
            }
        """

    def blue_theme_stylesheet(self):
        return """
            QWidget {
                font-size: 16px;
                font-family: 'Roboto', sans-serif;
                background-color: #e3f2fd;
            }
            QLabel {
                color: #1e88e5;
                font-weight: bold;
                margin-bottom: 10px;
            }
            QLineEdit, QComboBox, QCheckBox, QSpinBox, QDateEdit {
                border: 1px solid #64b5f6;
                border-radius: 8px;
                padding: 10px;
                background-color: #ffffff;
                font-size: 15px;
            }
            QLineEdit:focus, QComboBox:focus, QCheckBox:focus, QSpinBox:focus, QDateEdit:focus {
                border: 1px solid #1e88e5;
                outline: none;
            }
            QPushButton {
                background-color: #1e88e5;
                color: white;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
            QProgressBar {
                border: 1px solid #64b5f6;
                border-radius: 8px;
                text-align: center;
                font-size: 15px;
                color: white;
                background-color: #bbdefb;
            }
            QProgressBar::chunk {
                background-color: #1e88e5;
                width: 20px;
            }
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #64b5f6;
                border-radius: 8px;
                font-size: 15px;
            }
            QGroupBox {
                background-color: #e3f2fd;
                border: 1px solid #64b5f6;
                border-radius: 8px;
                padding: 10px;
                font-size: 15px;
                margin-top: 15px;
            }
            QGroupBox:title {
                subcontrol-origin: margin;
                padding: 0 5px;
                background-color: #64b5f6;
                border-radius: 5px;
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
                animation.setDuration(500)
                animation.setStartValue(QRect(widget.x(), widget.y() - 50, widget.width(), widget.height()))
                animation.setEndValue(QRect(widget.x(), widget.y(), widget.width(), widget.height()))
                animation.setEasingCurve(QEasingCurve.OutBounce)
                animation.start(QPropertyAnimation.DeleteWhenStopped)

    def selectDirectories(self):
        directories = QFileDialog.getExistingDirectory(self, self.tr("Sélectionner des dossiers"), "", QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks | QFileDialog.Option())
        if directories:
            self.selected_directories.append(directories)
            self.directoryListWidget.addItem(directories)

    def startSearch(self):
        if not self.selected_directories:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Veuillez sélectionner au moins un dossier pour la recherche."))
            return
        
        self.disableInputs(True)
        self.statusBar.showMessage(self.tr("Recherche en cours..."))
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
            QMessageBox.warning(self, self.tr("Aucun Résultat"), self.tr("Fichier non trouvé. Veuillez vérifier le nom et réessayer."))
            self.statusBar.showMessage(self.tr("Recherche terminée : aucun fichier trouvé"))
        else:
            self.statusBar.showMessage(self.tr("Recherche terminée : fichiers trouvés"))
            self.trayIcon.showMessage("ExplorAI", self.tr("Recherche terminée : fichiers trouvés"), QSystemTrayIcon.Information, 5000)

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
        file_name, _ = QFileDialog.getSaveFileName(self, self.tr("Sauvegarder les paramètres"), "", self.tr("JSON Files (*.json)"))
        if file_name:
            with open(file_name, 'w') as file:
                json.dump(settings, file)
            QMessageBox.information(self, self.tr("Succès"), self.tr("Paramètres sauvegardés avec succès."))

    def loadSettings(self):
        file_name, _ = QFileDialog.getOpenFileName(self, self.tr("Charger les paramètres"), "", self.tr("JSON Files (*.json)"))
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
            QMessageBox.information(self, self.tr("Succès"), self.tr("Paramètres chargés avec succès."))

    def switchLanguage(self, language_code):
        if language_code == 'fr':
            self.translator.load(QLibraryInfo.location(QLibraryInfo.TranslationsPath) + "/qt_fr.qm")
        elif language_code == 'en':
            self.translator.load(QLibraryInfo.location(QLibraryInfo.TranslationsPath) + "/qt_en.qm")

        QApplication.instance().installTranslator(self.translator)
        self.retranslateUi()

    def retranslateUi(self):
        self.setWindowTitle(self.tr("ExplorAI - Votre assistant de recherche intelligent"))
        self.labelTitle.setText(self.tr("Trouvez vos fichiers rapidement avec ExplorAI"))
        self.selectDirButton.setText(self.tr("Sélectionner des dossiers"))
        self.lineEditFileName.setPlaceholderText(self.tr("Entrez le nom du fichier..."))
        self.optionalGroupBox.setTitle(self.tr("Options avancées"))
        self.pushButtonSearch.setText(self.tr("Chercher"))
        self.filterLineEdit.setPlaceholderText(self.tr("Filtrer les résultats..."))
        self.resultTable.setHorizontalHeaderLabels([self.tr("Chemin des fichiers")])
        self.detailsGroupBox.setTitle(self.tr("Détails du fichier"))
        self.statusBar.showMessage(self.tr("Prêt"))

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
        openAction = menu.addAction(self.tr("Ouvrir le fichier"))
        openFolderAction = menu.addAction(self.tr("Ouvrir le dossier contenant"))
        copyPathAction = menu.addAction(self.tr("Copier le chemin du fichier"))

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
