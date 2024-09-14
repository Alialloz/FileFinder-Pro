import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit, QVBoxLayout, QWidget, 
                             QPushButton, QHBoxLayout, QMessageBox, QTableWidget, QTableWidgetItem, QInputDialog)
from PyQt5.QtCore import Qt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
import base64
import random
import string

class PasswordManager(QMainWindow):
    def __init__(self):
        super().__init__()

        # Variables de stockage
        self.passwords = {}
        self.encryption_key = None
        self.salt_file = "salt.dat"  # Fichier pour sauvegarder le sel
        self.password_file = "passwords.dat"  # Fichier pour sauvegarder les mots de passe chiffrés
        self.salt = None

        self.initUI()

    def initUI(self):
        # Configuration de la fenêtre principale
        self.setWindowTitle("Gestionnaire de mots de passe sécurisé")
        self.setGeometry(100, 100, 600, 400)

        # Widget principal
        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)

        # Layout principal
        self.layout = QVBoxLayout()
        self.centralWidget.setLayout(self.layout)

        # Interface utilisateur pour entrer le mot de passe maître
        self.masterPasswordInput = QLineEdit(self)
        self.masterPasswordInput.setEchoMode(QLineEdit.Password)
        self.masterPasswordInput.setPlaceholderText("Entrez le mot de passe maître")
        self.layout.addWidget(self.masterPasswordInput)

        self.unlockButton = QPushButton("Déverrouiller", self)
        self.unlockButton.clicked.connect(self.unlock)
        self.layout.addWidget(self.unlockButton)

        self.infoLabel = QLabel("", self)
        self.layout.addWidget(self.infoLabel)

        # Boutons de gestion des mots de passe
        self.buttonLayout = QHBoxLayout()
        self.addButton = QPushButton("Ajouter", self)
        self.addButton.clicked.connect(self.addPassword)
        self.buttonLayout.addWidget(self.addButton)

        self.generateButton = QPushButton("Générer un mot de passe", self)
        self.generateButton.clicked.connect(self.generatePassword)
        self.buttonLayout.addWidget(self.generateButton)

        self.layout.addLayout(self.buttonLayout)

        # Table pour afficher les mots de passe
        self.passwordTable = QTableWidget(self)
        self.passwordTable.setColumnCount(2)
        self.passwordTable.setHorizontalHeaderLabels(["Site", "Mot de passe"])
        self.layout.addWidget(self.passwordTable)

        # Charger le sel depuis un fichier ou générer un nouveau
        self.loadSalt()

    def unlock(self):
        # Déverrouille l'application avec le mot de passe maître
        password = self.masterPasswordInput.text()
        if password == "":
            self.infoLabel.setText("Veuillez entrer le mot de passe maître.")
            return
        
        # Générer la clé de chiffrement à partir du mot de passe maître
        self.encryption_key = self.derive_key_from_password(password)
        self.infoLabel.setText("Application déverrouillée.")

        # Charger les mots de passe depuis le fichier chiffré
        if os.path.exists(self.password_file):
            with open(self.password_file, "rb") as file:
                encrypted_data = file.read()
            try:
                fernet = Fernet(self.encryption_key)
                decrypted_data = fernet.decrypt(encrypted_data).decode()
                self.passwords = json.loads(decrypted_data)
                self.populateTable()
            except:
                QMessageBox.warning(self, "Erreur", "Mot de passe maître incorrect.")
        else:
            QMessageBox.information(self, "Info", "Aucun mot de passe enregistré.")

    def derive_key_from_password(self, password):
        # Utiliser PBKDF2 pour dériver la clé à partir du mot de passe maître
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def loadSalt(self):
        # Charger ou générer un sel pour la dérivation de clé
        if os.path.exists(self.salt_file):
            with open(self.salt_file, "rb") as file:
                self.salt = file.read()
        else:
            self.salt = os.urandom(16)  # Générer un nouveau sel
            with open(self.salt_file, "wb") as file:
                file.write(self.salt)

    def addPassword(self):
        # Ajouter un mot de passe
        site, password = self.promptPasswordInput()
        if site and password:
            self.passwords[site] = password
            self.populateTable()
            self.savePasswords()

    def generatePassword(self):
        # Générer un mot de passe sécurisé
        password_length = 12
        all_chars = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(random.choice(all_chars) for _ in range(password_length))
        site, _ = self.promptPasswordInput(pre_generated_password=password)
        if site:
            self.passwords[site] = password
            self.populateTable()
            self.savePasswords()

    def populateTable(self):
        # Afficher les mots de passe dans la table
        self.passwordTable.setRowCount(0)
        for site, password in self.passwords.items():
            rowPosition = self.passwordTable.rowCount()
            self.passwordTable.insertRow(rowPosition)
            self.passwordTable.setItem(rowPosition, 0, QTableWidgetItem(site))
            self.passwordTable.setItem(rowPosition, 1, QTableWidgetItem(password))

    def promptPasswordInput(self, pre_generated_password=""):
        # Demander à l'utilisateur d'entrer un site et un mot de passe
        site, okSite = QInputDialog.getText(self, "Ajouter un site", "Nom du site :")
        if not okSite or site == "":
            return None, None
        if pre_generated_password:
            return site, pre_generated_password
        password, okPassword = QInputDialog.getText(self, "Ajouter un mot de passe", "Mot de passe pour ce site :")
        if not okPassword or password == "":
            return None, None
        return site, password

    def savePasswords(self):
        # Sauvegarder les mots de passe dans un fichier chiffré
        if self.encryption_key:
            fernet = Fernet(self.encryption_key)
            encrypted_data = fernet.encrypt(json.dumps(self.passwords).encode())
            with open(self.password_file, "wb") as file:
                file.write(encrypted_data)

def main():
    app = QApplication(sys.argv)
    window = PasswordManager()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
