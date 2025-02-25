import sys
from PyQt5.QtWidgets import (
    QApplication, QFileDialog, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QComboBox, QLabel, QAction, QMessageBox, QCheckBox, QScrollArea,
    QGridLayout
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import pandas as pd

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # * Configuration de la fenêtre principale
        self.setWindowTitle("GUI TP STATISTIQUE")
        self.setGeometry(100, 100, 800, 600)

        # * Création de la barre de menu
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu("FILE")

        # * Ajout d'une action au menu
        exportFileAction = QAction("Export", self)
        exportFileAction.triggered.connect(self.exportGraphicOfDataset) 
        fileMenu.addAction(exportFileAction)

        # * Création du widget central
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)

        # * Layout principal
        mainLayout = QHBoxLayout()
        centralWidget.setLayout(mainLayout)

        # * Layout gauche
        leftLayout = QVBoxLayout()
        addLayout = QHBoxLayout()
        mainLayout.addLayout(leftLayout, 1)
        
        # * Layout pour les checkboxs avec scroll
        self.checkboxesLayout = QGridLayout()
        self.scrollArea = QScrollArea()
        self.scrollWidget = QWidget()
        self.areaLabel = QLabel("Graphics section managment")
        self.areaLabel.setObjectName("label")
        self.areaLabel.setFont(QFont('Times New Roman', 10, QFont.Bold))
        # self.checkboxesLayout.setAlignment(Qt.AlignCenter)
        self.checkboxesLayout.addWidget(self.areaLabel)
        self.scrollWidget.setObjectName("checkboxGroup")
        self.scrollWidget.setLayout(self.checkboxesLayout)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setWidgetResizable(True)
        # self.scrollArea.setFixedHeight(200)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # * Boutons et ComboBox
        self.datasetCombo = self.createButtonCombo(leftLayout, "Datasets")
        self.datasetCombo.currentIndexChanged.connect(self.updateGraphic)
        leftLayout.addWidget(self.scrollArea)
        self.smoothingMethodCombo = self.createButtonCombo(leftLayout, "Smoothing Methods", ["None", "Simple Exponential Smoothing", "Double Exponential Smoothing"])
        self.smoothingMethodCombo.currentIndexChanged.connect(self.smoothingMethodSelection)
        self.trendCombo = self.createButtonCombo(leftLayout, "Trend Computation Methods", ["None", "Simple Moving Average", "Exponential Moving Average"])
        self.trendCombo.currentIndexChanged.connect(self.trendSelection)

        # * Label Ajouter dataset
        self.addLabel = QLabel("Add dataset")
        self.addLabel.setObjectName("addLabel")
        self.addLabel.setAlignment(Qt.AlignCenter)

        # * Bouton Ajouter dataset
        self.addButton = QPushButton("+")
        self.addButton.setObjectName("addButton")
        self.addButton.clicked.connect(self.addDataset)
        
        addLayout.addWidget(self.addLabel)
        addLayout.addWidget(self.addButton)
        leftLayout.addLayout(addLayout)

        # * Layout droit
        rightLayout = QVBoxLayout()
        mainLayout.addLayout(rightLayout, 3)

        # * Placeholder pour la représentation graphique
        self.graphicsFigureCanvas = FigureCanvas(Figure())
        self.ax = self.graphicsFigureCanvas.figure.subplots()
        rightLayout.addWidget(self.graphicsFigureCanvas)

        # * Bouton Next
        self.nextButton = QPushButton("Next")
        self.nextButton.setObjectName("nextButton")
        self.nextButton.clicked.connect(self.nextGraphic)
        rightLayout.addWidget(self.nextButton)
        # self.nextButton.clicked.connect(self.nextGraphic)

        # * Chargement du fichier CSS
        self.setStyleSheet(open("stylesheet.qss").read())
        
        # * Dictionnaire pour stocker les datasets
        self.datasets = {}
        
        # * Variable pour suivre l'etat des graphiques
        self.currentDatasetIndex = 0
        self.currentGraphicIndex = 0
        self.selectedColumns = []
        
        # * Dictionnqire pour les différentes methodes de lissage exponentiel
        self.smoothingMethodDict = {
            "Simple Exponential Smoothing": self.simpleExponentialSmoothing,
            "Double Exponential Smoothing": self.doubleExponentialSmoothing
        }
        
        # * Dictionnaire pour les différentes methodes de calcul de tendance
        self.trendDict = {
            "Simple Moving Average": self.simpleMovingAverage,
            "Exponential Moving Average": self.exponentialMovingAverage
        }
        
    def exportGraphicOfDataset(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getSaveFileName(self, "Export graphic of dataset", "", "Images (*.png *.xpm *.jpg)", options=options)
        if fileName:
            # TODO code for image exporting
            pass

    def createButtonCombo(self, layout, text, items=None):
        buttonComboLayout = QVBoxLayout()
        buttonComboGroup = QWidget()
        buttonComboGroup.setLayout(buttonComboLayout)
        buttonComboGroup.setObjectName("buttonComboLayout")

        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont('Times New Roman', 12, QFont.Bold))
        label.setObjectName("label")
        label.setFixedHeight(20)
        buttonComboLayout.addWidget(label, Qt.AlignTop)

        combo = QComboBox()
        combo.setObjectName("combo")
        # combo.currentIndexChanged.connect(self.updateGraphic)
        if items:
            combo.addItems(items)
        buttonComboLayout.addWidget(combo, Qt.AlignCenter)
        layout.addWidget(buttonComboGroup)
        
        return combo
        
    def addDataset(self):
        options = QFileDialog.Options()
        # checkBoxLayout = QVBoxLayout()
        files, _ = QFileDialog.getOpenFileNames(self, "Select Datasets", "", "CSV Files (*.csv)", options=options)
        if files:
            for file in files:
                try:
                    df = pd.read_csv(file)
                    df[df.columns[0]] = pd.to_datetime(df[df.columns[0]])
                    fileName = file.split('/')[-1]
                    datasetName = fileName.split(".csv")[0]
                    self.datasets[datasetName] = df
                    if self.datasetCombo.findText(datasetName) == -1:
                        self.datasetCombo.addItem(datasetName)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to load {file}: {e}")
                    
        self.checkboxesLayout.removeWidget(self.areaLabel)
                
    def updateGraphic(self):
        datasetName = self.datasetCombo.currentText()
        if datasetName:
            df = self.datasets.get(datasetName)
            if df is not None:
                self.updateCheckboxes(df.columns)
                self.plotGraphic()
                
    def getColor(self, idx):
        colors = plt.cm.tab10.colors # * Utiliser une palette de couleur
        return colors[idx % len(colors)]
    
    def updateCheckboxes(self, columns):
        for i in reversed(range(self.checkboxesLayout.count())):
            widget = self.checkboxesLayout.takeAt(i).widget()
            if widget is not None:
                widget.deleteLater()
                
        self.checkboxes = {}
        self.colors = {}
        for idx, column in enumerate(columns):
            color = self.getColor(idx)
            self.colors[column] = color
            checkbox = QCheckBox(column)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.plotGraphic)
            checkbox.setStyleSheet(f"QCheckBox::indicator {{ background-color: {QColor(*[int(c*255) for c in color]).name()}; }} QCheckBox::indicator:unchecked {{ background-color: transparent; border: 2px solid {QColor(*[int(c*255) for c in color]).name()};}}")
            self.checkboxesLayout.addWidget(checkbox, idx // 2, idx % 2)
            self.checkboxes[column] = checkbox
            
        # * Ajustement de la taille minimale du widget de défilement
        minHeight = 40 * ((len(columns) + 1) // 2)
        self.scrollWidget.setMinimumHeight(minHeight)
        
        # * Réinitialiser l'index et les colonnes sélectionnées
        self.currentGraphicIndex = 0
        self.selectedColumns = [col for col in columns if self.checkboxes[col].isChecked()]
        
    def plotGraphic(self):
        datasetName = self.datasetCombo.currentText()
        if datasetName:
            df = self.datasets.get(datasetName)
            if df is not None:
                self.ax.clear()
                columns = df.columns[1:]
                firstColumn = df.columns[0]
                for column in columns:
                    if self.checkboxes[column].isChecked() and pd.api.types.is_numeric_dtype(df[column]):
                        df.plot(x=firstColumn, y=column, ax=self.ax, label=column, color=self.colors[column])
                self.ax.set_title(self.datasetCombo.currentText())
                self.ax.legend()
                self.graphicsFigureCanvas.draw()
                
    def nextGraphic(self):
        datasetNames = list(self.datasets.keys())
        if not datasetNames:
            return
        
        # * Paaser au dataset suivant
        self.currentDatasetIndex = (self.currentDatasetIndex + 1) % len(datasetNames)
        nextDatasetName = datasetNames[self.currentDatasetIndex]
        self.datasetCombo.setCurrentText(nextDatasetName)
        
        # * Mettre à jour les checkboxes et réinitialiser l'index de graphique
        self.updateCheckboxes(self.datasets[nextDatasetName].columns)
        self.plotGraphic()
        
    def simpleExponentialSmoothing(self):
        datasetName = self.datasetCombo.currentText()
        if not datasetName:
            return

        df = self.datasets.get(datasetName)
        if df is None:
            return
        
        xColumn = df.columns[0]  # * Utiliser la première colonne datetime comme abscisse
        columns = df.columns[1:]
        
        for column in columns:
            if self.checkboxes[column].isChecked() and pd.api.types.is_numeric_dtype(df[column]):
                y = df[column]
                y = y.ewm(span=5, adjust=False).mean()  # * Exemple de lissage exponentiel simple
                self.ax.plot(df[xColumn], y, label=column+"SEM")

        self.ax.set_title(datasetName)
        self.ax.legend()
        self.graphicsFigureCanvas.draw()
        
    def doubleExponentialSmoothing(self):
        datasetName = self.datasetCombo.currentText()
        if not datasetName:
            return

        df = self.datasets.get(datasetName)
        if df is None:
            return
        
        xColumn = df.columns[0]  # * Utiliser la première colonne datetime comme abscisse
        columns = df.columns[1:]
        
        for column in columns:
            if self.checkboxes[column].isChecked() and pd.api.types.is_numeric_dtype(df[column]):
                y = df[column]
                y = df[column].ewm(span=5, adjust=False).mean().ewm(span=5, adjust=False).mean()  # * Exemple de lissage exponentiel double
                self.ax.plot(df[xColumn], y, label=column+"DEM")

        self.ax.set_title(datasetName)
        self.ax.legend()
        self.graphicsFigureCanvas.draw()
        
    def simpleMovingAverage(self):
        datasetName = self.datasetCombo.currentText()
        if not datasetName:
            return

        df = self.datasets.get(datasetName)
        if df is None:
            return
        
        xColumn = df.columns[0]  # * Utiliser la première colonne datetime comme abscisse
        columns = df.columns[1:]
        
        for column in columns:
            if self.checkboxes[column].isChecked() and pd.api.types.is_numeric_dtype(df[column]):
                y = df[column]
                trend = y.rolling(window=5).mean()  # * Exemple de moyenne mobile simple
                self.ax.plot(df[xColumn], trend, label=column+"Simple Trend", linestyle='--')

        self.ax.set_title(datasetName)
        self.ax.legend()
        self.graphicsFigureCanvas.draw()
        
    def exponentialMovingAverage(self):
        datasetName = self.datasetCombo.currentText()
        if not datasetName:
            return

        df = self.datasets.get(datasetName)
        if df is None:
            return
        
        xColumn = df.columns[0]  # * Utiliser la première colonne datetime comme abscisse
        columns = df.columns[1:]
        
        for column in columns:
            if self.checkboxes[column].isChecked() and pd.api.types.is_numeric_dtype(df[column]):
                y = df[column]
                trend = y.ewm(span=5, adjust=False).mean()  # * Exemple de moyenne mobile exponentielle
                self.ax.plot(df[xColumn], trend, label=column+"Polynomial Trend", linestyle='--')

        self.ax.set_title(datasetName)
        self.ax.legend()
        self.graphicsFigureCanvas.draw()
        
    def smoothingMethodSelection(self):
        smoothingMethod = self.smoothingMethodCombo.currentText()
        if smoothingMethod in self.smoothingMethodDict:
            self.smoothingMethodDict[smoothingMethod]()
        else:
            print("None have being selected")
        
    def trendSelection(self):
        trend = self.trendCombo.currentText()
        if trend in self.trendDict:
            self.trendDict[trend]()
        else:
            print("None have being selected")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())