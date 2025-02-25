import sys
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QComboBox, QLabel, QAction, QFileDialog, QMessageBox, QCheckBox, QScrollArea, QGridLayout
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Configuration de la fenêtre principale
        self.setWindowTitle("GUI TP STATISTIQUE")
        self.setGeometry(100, 100, 800, 600)

        # Création de la barre de menu
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("FILE")

        # Ajout d'une action au menu
        file_action = QAction("File", self)
        file_menu.addAction(file_action)

        # Création du widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Layout gauche
        left_layout = QVBoxLayout()
        main_layout.addLayout(left_layout, 1)

        # Boutons et ComboBox
        self.dataset_combo = self.create_button_combo(left_layout, "Select dataset")
        self.sm_combo = self.create_button_combo(left_layout, "Select SM", ["None", "Simple Exponential Smoothing", "Double Exponential Smoothing"])
        self.tendance_combo = self.create_button_combo(left_layout, "Select Tendance", ["None", "Simple Moving Average", "Exponential Moving Average"])

        # Bouton Ajouter dataset
        add_button = QPushButton("Ajouter dataset")
        add_button.setObjectName("addButton")
        add_button.clicked.connect(self.add_dataset)
        left_layout.addWidget(add_button)

        # Bouton Appliquer méthode
        apply_button = QPushButton("Appliquer Méthode")
        apply_button.setObjectName("applyButton")
        apply_button.clicked.connect(self.apply_method)
        left_layout.addWidget(apply_button)

        # Layout pour les checkboxes avec scroll
        self.checkbox_layout = QGridLayout()
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_widget.setLayout(self.checkbox_layout)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedHeight(200)  # Hauteur fixe pour le défilement
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        left_layout.addWidget(self.scroll_area)

        # Layout droit
        right_layout = QVBoxLayout()
        main_layout.addLayout(right_layout, 3)

        # Placeholder pour la représentation graphique
        self.figure_canvas = FigureCanvas(Figure())
        self.ax = self.figure_canvas.figure.subplots()
        right_layout.addWidget(self.figure_canvas)

        # Section de titre et légende
        title_legend_layout = QHBoxLayout()
        right_layout.addLayout(title_legend_layout)

        title_label = QLabel("TITLE OF REPRESENTATION")
        title_label.setStyleSheet("font-weight: bold;")
        title_legend_layout.addWidget(title_label)

        legend_label = QLabel("LEGEND")
        title_legend_layout.addWidget(legend_label)

        # Bouton Next
        next_button = QPushButton("Next")
        next_button.setObjectName("nextButton")
        next_button.clicked.connect(self.next_graph)
        right_layout.addWidget(next_button)

        # Chargement du fichier CSS
        self.setStyleSheet(open("teststylesheet.css").read())

        # Dictionnaire pour stocker les datasets
        self.datasets = {}

        # Variables pour suivre l'état des graphiques
        self.current_dataset_index = 0
        self.current_graph_index = 0
        self.selected_columns = []

    def create_button_combo(self, layout, text, items=None):
        button_combo_layout = QHBoxLayout()
        layout.addLayout(button_combo_layout)

        button = QPushButton(text)
        button_combo_layout.addWidget(button)

        combo = QComboBox()
        combo.currentIndexChanged.connect(self.update_graph)
        if items:
            combo.addItems(items)
        button_combo_layout.addWidget(combo)

        return combo

    def add_dataset(self):
        options = QFileDialog.Options()
        files, _ = QFileDialog.getOpenFileNames(self, "Select Datasets", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if files:
            for file in files:
                try:
                    df = pd.read_csv(file)
                    # Convertir les colonnes en datetime si possible
                    # for column in df.columns:
                    #     try:
                    df[df.columns[0]] = pd.to_datetime(df[df.columns[0]])
                        # except (ValueError, TypeError):
                        #     pass
                    dataset_name = file.split('/')[-1]
                    self.datasets[dataset_name] = df
                    self.dataset_combo.addItem(dataset_name)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to load {file}: {e}")

    def update_graph(self):
        dataset_name = self.dataset_combo.currentText()
        if dataset_name:
            df = self.datasets.get(dataset_name)
            if df is not None:
                self.update_checkboxes(df.columns)
                self.plot_graph()

    def get_color(self, idx):
        colors = plt.cm.tab10.colors  # Utiliser une palette de couleurs
        return colors[idx % len(colors)]

    def update_checkboxes(self, columns):
        for i in reversed(range(self.checkbox_layout.count())): 
            widget = self.checkbox_layout.takeAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        self.checkboxes = {}
        self.colors = {}
        for idx, column in enumerate(columns):
            color = self.get_color(idx)
            self.colors[column] = color
            checkbox = QCheckBox(column)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.plot_graph)
            checkbox.setStyleSheet(f"QCheckBox::indicator {{ background-color: {QColor(*[int(c*255) for c in color]).name()}; }}")
            self.checkbox_layout.addWidget(checkbox, idx // 2, idx % 2)
            self.checkboxes[column] = checkbox

        # Ajustement de la taille minimale du widget de défilement
        min_height = 40 * ((len(columns) + 1) // 2)
        self.scroll_widget.setMinimumHeight(min_height)

        # Réinitialiser l'index et les colonnes sélectionnées
        self.current_graph_index = 0
        self.selected_columns = [col for col in columns if self.checkboxes[col].isChecked()]

    def plot_graph(self):
        dataset_name = self.dataset_combo.currentText()
        if dataset_name:
            df = self.datasets.get(dataset_name)
            if df is not None:
                self.ax.clear()
                datetime_columns = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
                if datetime_columns:
                    x_column = datetime_columns[0]  # Utiliser la première colonne datetime comme abscisse
                else:
                    x_column = df.index  # Utiliser l'index comme abscisse si aucune colonne datetime

                for column in df.columns:
                    if self.checkboxes[column].isChecked() and pd.api.types.is_numeric_dtype(df[column]):
                        df.plot(x=x_column, y=column, ax=self.ax, label=column, color=self.colors[column])
                self.ax.set_title(self.dataset_combo.currentText())
                self.ax.legend()
                self.figure_canvas.draw()

    def apply_method(self):
        dataset_name = self.dataset_combo.currentText()
        if not dataset_name:
            return

        df = self.datasets.get(dataset_name)
        if df is None:
            return

        sm_method = self.sm_combo.currentText()
        tendance_method = self.tendance_combo.currentText()

        self.ax.clear()
        datetime_columns = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
        if datetime_columns:
            x_column = datetime_columns[0]  # Utiliser la première colonne datetime comme abscisse
        else:
            x_column = df.index  # Utiliser l'index comme abscisse si aucune colonne datetime

        for column in df.columns:
            if self.checkboxes[column].isChecked() and pd.api.types.is_numeric_dtype(df[column]):
                y = df[column]
                if sm_method == "Simple Exponential Smoothing":
                    y = y.ewm(span=5, adjust=False).mean()  # Exemple de lissage exponentiel simple
                elif sm_method == "Double Exponential Smoothing":
                    y = df[column].ewm(span=5, adjust=False).mean().ewm(span=5, adjust=False).mean()  # Exemple de lissage exponentiel double

                if tendance_method == "Simple Moving Average":
                    trend = y.rolling(window=5).mean()  # Exemple de moyenne mobile simple
                    self.ax.plot(df[x_column], trend, linestyle='--', color=self.colors[column])
                elif tendance_method == "Exponential Moving Average":
                    trend = y.ewm(span=5, adjust=False).mean()  # Exemple de moyenne mobile exponentielle
                    self.ax.plot(df[x_column], trend, linestyle='--', color=self.colors[column])

                self.ax.plot(df[x_column], y, label=column, color=self.colors[column])

        self.ax.set_title(dataset_name)
        self.ax.legend()
        self.figure_canvas.draw()

    def next_graph(self):
        dataset_names = list(self.datasets.keys())
        if not dataset_names:
            return
        
        # Passer au dataset suivant
        self.current_dataset_index = (self.current_dataset_index + 1) % len(dataset_names)
        next_dataset_name = dataset_names[self.current_dataset_index]
        self.dataset_combo.setCurrentText(next_dataset_name)

        # Mettre à jour les checkboxes et réinitialiser l'index de graphique
        self.update_checkboxes(self.datasets[next_dataset_name].columns)
        self.plot_graph()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())