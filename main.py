import sys
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QComboBox, QLabel, QMessageBox, QCheckBox, QScrollArea,
    QGridLayout
)
from PyQt6.QtGui import QFont, QColor, QAction, QPalette
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import pandas as pd

class AnimatedButton(QPushButton):
    """Button with hover animation"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._scale = 1.0
        
    def enterEvent(self, event):
        self.animate_scale(1.05)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.animate_scale(1.0)
        super().leaveEvent(event)
        
    def animate_scale(self, target):
        self.animation = QPropertyAnimation(self, b"scale")
        self.animation.setDuration(150)
        self.animation.setStartValue(self._scale)
        self.animation.setEndValue(target)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()
        
    def get_scale(self):
        return self._scale
        
    def set_scale(self, scale):
        self._scale = scale
        self.setStyleSheet(self.styleSheet() + f" transform: scale({scale});")
        
    scale = pyqtProperty(float, get_scale, set_scale)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.isDarkTheme = False
        self.setWindowTitle("Statistics Visualization Tool")
        self.setGeometry(100, 100, 1200, 700)
        
        # Menu Bar
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu("File")
        
        # Export action
        exportFileAction = QAction("Export Plot...", self)
        exportFileAction.triggered.connect(self.exportGraphicOfDataset) 
        fileMenu.addAction(exportFileAction)
        
        # Clear action
        clearAction = QAction("Clear All Datasets", self)
        clearAction.triggered.connect(self.clearAllDatasets)
        fileMenu.addAction(clearAction)
        
        # Central Widget
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        
        # Main Layout
        mainLayout = QHBoxLayout()
        centralWidget.setLayout(mainLayout)
        
        # Left Panel
        leftLayout = QVBoxLayout()
        leftLayout.setSpacing(15)
        leftLayout.setContentsMargins(10, 10, 10, 10)
        mainLayout.addLayout(leftLayout, 1)
        
        # Dataset selection
        self.datasetCombo = self.createButtonCombo(leftLayout, "Select Dataset")
        self.datasetCombo.currentIndexChanged.connect(self.onDatasetChanged)
        
        # Checkboxes section
        self.checkboxesLayout = QGridLayout()
        self.checkboxesLayout.setSpacing(8)
        self.scrollArea = QScrollArea()
        self.scrollWidget = QWidget()
        self.areaLabel = QLabel("Select Variables to Display")
        self.areaLabel.setObjectName("sectionLabel")
        self.areaLabel.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        
        self.checkboxesLayout.addWidget(self.areaLabel, 0, 0, 1, 2)
        self.scrollWidget.setObjectName("checkboxGroup")
        self.scrollWidget.setLayout(self.checkboxesLayout)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        
        leftLayout.addWidget(self.scrollArea)
        
        # Smoothing methods
        self.smoothingMethodCombo = self.createButtonCombo(
            leftLayout, 
            "Smoothing Method", 
            ["None", "Simple Exponential Smoothing", "Double Exponential Smoothing"]
        )
        self.smoothingMethodCombo.currentIndexChanged.connect(self.updatePlot)
        
        # Trend computation
        self.trendCombo = self.createButtonCombo(
            leftLayout, 
            "Trend Computation", 
            ["None", "Simple Moving Average", "Exponential Moving Average"]
        )
        self.trendCombo.currentIndexChanged.connect(self.updatePlot)
        
        # Add dataset button
        addLayout = QHBoxLayout()
        self.addLabel = QLabel("Add Dataset")
        self.addLabel.setObjectName("addLabel")
        self.addLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.addButton = AnimatedButton("+")
        self.addButton.setObjectName("addButton")
        self.addButton.setToolTip("Load CSV dataset(s)")
        self.addButton.clicked.connect(self.addDataset)
        
        addLayout.addWidget(self.addLabel)
        addLayout.addWidget(self.addButton)
        leftLayout.addLayout(addLayout)
        
        # Right Panel (Plot area)
        rightLayout = QVBoxLayout()
        rightLayout.setContentsMargins(10, 10, 10, 10)
        mainLayout.addLayout(rightLayout, 3)
        
        # Plot canvas
        self.graphicsFigureCanvas = FigureCanvas(Figure(figsize=(8, 6)))
        self.ax = self.graphicsFigureCanvas.figure.subplots()
        self.ax.set_title("Load a dataset to begin")
        rightLayout.addWidget(self.graphicsFigureCanvas)
        
        # Navigation buttons
        navLayout = QHBoxLayout()
        navLayout.setSpacing(10)
        self.prevButton = AnimatedButton("◄ Previous Dataset")
        self.prevButton.setObjectName("navButton")
        self.prevButton.clicked.connect(self.prevGraphic)
        self.prevButton.setEnabled(False)
        
        self.nextButton = AnimatedButton("Next Dataset ►")
        self.nextButton.setObjectName("navButton")
        self.nextButton.clicked.connect(self.nextGraphic)
        self.nextButton.setEnabled(False)
        
        navLayout.addWidget(self.prevButton)
        navLayout.addWidget(self.nextButton)
        rightLayout.addLayout(navLayout)
        
        # Floating theme toggle button
        self.themeButton = AnimatedButton("☀")
        self.themeButton.setObjectName("themeButton")
        self.themeButton.setToolTip("Toggle Light/Dark Theme")
        self.themeButton.clicked.connect(self.toggleTheme)
        self.themeButton.setParent(centralWidget)
        self.themeButton.setFixedSize(50, 50)
        self.themeButton.move(20, 20)
        self.themeButton.raise_()
        
        # Apply initial theme
        self.applyTheme()
        
        # Data storage
        self.datasets = {}
        self.currentDatasetIndex = 0
        self.checkboxes = {}
        self.colors = {}
        
        # Initial canvas draw
        self.updatePlotTheme()
        self.graphicsFigureCanvas.draw()
        
    def toggleTheme(self):
        """Toggle between light and dark theme"""
        self.isDarkTheme = not self.isDarkTheme
        self.themeButton.setText("☾" if self.isDarkTheme else "☀")
        self.applyTheme()
        self.updatePlotTheme()
        self.updatePlot()
        
    def updatePlotTheme(self):
        """Update matplotlib plot colors based on theme"""
        if self.isDarkTheme:
            self.graphicsFigureCanvas.figure.patch.set_facecolor('#1e1e2e')
            self.ax.set_facecolor('#2d2d44')
            self.ax.spines['bottom'].set_color('#6c7086')
            self.ax.spines['top'].set_color('#6c7086')
            self.ax.spines['left'].set_color('#6c7086')
            self.ax.spines['right'].set_color('#6c7086')
            self.ax.tick_params(colors='#cdd6f4', which='both')
            self.ax.xaxis.label.set_color('#cdd6f4')
            self.ax.yaxis.label.set_color('#cdd6f4')
            self.ax.title.set_color('#cdd6f4')
            self.ax.grid(True, alpha=0.15, color='#6c7086')
        else:
            self.graphicsFigureCanvas.figure.patch.set_facecolor('#ffffff')
            self.ax.set_facecolor('#fafafa')
            self.ax.spines['bottom'].set_color('#ccc')
            self.ax.spines['top'].set_color('#ccc')
            self.ax.spines['left'].set_color('#ccc')
            self.ax.spines['right'].set_color('#ccc')
            self.ax.tick_params(colors='#333', which='both')
            self.ax.xaxis.label.set_color('#333')
            self.ax.yaxis.label.set_color('#333')
            self.ax.title.set_color('#333')
            self.ax.grid(True, alpha=0.3, color='#ddd')
    
    def applyTheme(self):
        """Apply light or dark theme"""
        if self.isDarkTheme:
            stylesheet = """
                QMainWindow {
                    background-color: #1e1e2e;
                }
                QMenuBar {
                    background-color: #2d2d44;
                    color: #cdd6f4;
                    border-bottom: 1px solid #45475a;
                }
                QMenuBar::item:selected {
                    background-color: #45475a;
                    border-radius: 6px;
                }
                QMenu {
                    background-color: #2d2d44;
                    color: #cdd6f4;
                    border: 1px solid #45475a;
                    border-radius: 8px;
                }
                QMenu::item:selected {
                    background-color: #45475a;
                    border-radius: 6px;
                }
                QLabel#sectionLabel {
                    color: #cdd6f4;
                    padding: 8px;
                    background-color: #2d2d44;
                    border-radius: 8px;
                }
                QLabel#addLabel {
                    color: #bac2de;
                    font-size: 12px;
                }
                QPushButton#addButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #a6e3a1, stop:1 #40a02b);
                    color: #1e1e2e;
                    border: none;
                    border-radius: 25px;
                    font-size: 22px;
                    font-weight: bold;
                    min-width: 50px;
                    max-width: 50px;
                    min-height: 50px;
                    max-height: 50px;
                }
                QPushButton#addButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #b8f1b0, stop:1 #4db841);
                }
                QPushButton#addButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #94e2d5, stop:1 #179299);
                }
                QPushButton#navButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #89b4fa, stop:1 #1e66f5);
                    color: white;
                    border: none;
                    border-radius: 12px;
                    padding: 10px 18px;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton#navButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #a0c9ff, stop:1 #3584ff);
                }
                QPushButton#navButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #74c7ec, stop:1 #04a5e5);
                }
                QPushButton#navButton:disabled {
                    background: #45475a;
                    color: #6c7086;
                }
                QPushButton#themeButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #f9e2af, stop:1 #f38ba8);
                    color: #1e1e2e;
                    border: none;
                    border-radius: 25px;
                    font-size: 20px;
                    font-weight: bold;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                }
                QPushButton#themeButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #fff4c2, stop:1 #ff99b5);
                }
                QComboBox#combo {
                    border: 2px solid #45475a;
                    border-radius: 10px;
                    padding: 8px;
                    background-color: #2d2d44;
                    color: #cdd6f4;
                    min-height: 25px;
                }
                QComboBox#combo:hover {
                    border: 2px solid #89b4fa;
                }
                QComboBox#combo::drop-down {
                    border: none;
                    border-radius: 8px;
                    width: 30px;
                }
                QComboBox#combo::down-arrow {
                    image: none;
                    border: 2px solid #cdd6f4;
                    width: 8px;
                    height: 8px;
                    border-top: none;
                    border-left: none;
                    transform: rotate(45deg);
                    margin-right: 8px;
                }
                QComboBox QAbstractItemView {
                    background-color: #2d2d44;
                    color: #cdd6f4;
                    border: 2px solid #45475a;
                    border-radius: 10px;
                    selection-background-color: #45475a;
                    outline: none;
                }
                QWidget#buttonComboLayout {
                    background-color: #2d2d44;
                    border-radius: 15px;
                    padding: 15px;
                    margin: 5px;
                    border: 1px solid #45475a;
                }
                QScrollArea#scrollArea {
                    border: 2px solid #45475a;
                    border-radius: 15px;
                    background-color: #2d2d44;
                }
                QWidget#checkboxGroup {
                    background-color: #2d2d44;
                }
                QScrollBar:vertical {
                    background-color: #2d2d44;
                    width: 12px;
                    border-radius: 6px;
                }
                QScrollBar::handle:vertical {
                    background-color: #45475a;
                    border-radius: 6px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #585b70;
                }
                QCheckBox {
                    spacing: 8px;
                    padding: 5px;
                    color: #cdd6f4;
                    font-weight: 500;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border-radius: 5px;
                }
            """
        else:
            stylesheet = """
                QMainWindow {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #f0f4f8, stop:1 #e8eef5);
                }
                QMenuBar {
                    background-color: #ffffff;
                    color: #2c3e50;
                    border-bottom: 1px solid #e0e0e0;
                }
                QMenuBar::item:selected {
                    background-color: #e3f2fd;
                    border-radius: 6px;
                }
                QMenu {
                    background-color: #ffffff;
                    color: #2c3e50;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                }
                QMenu::item:selected {
                    background-color: #e3f2fd;
                    border-radius: 6px;
                }
                QLabel#sectionLabel {
                    color: #2c3e50;
                    padding: 8px;
                    background-color: #ffffff;
                    border-radius: 8px;
                }
                QLabel#addLabel {
                    color: #5a6c7d;
                    font-size: 12px;
                }
                QPushButton#addButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #4CAF50, stop:1 #45a049);
                    color: white;
                    border: none;
                    border-radius: 25px;
                    font-size: 22px;
                    font-weight: bold;
                    min-width: 50px;
                    max-width: 50px;
                    min-height: 50px;
                    max-height: 50px;
                    box-shadow: 0 4px 8px rgba(76, 175, 80, 0.3);
                }
                QPushButton#addButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #66BB6A, stop:1 #4CAF50);
                }
                QPushButton#addButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #388E3C, stop:1 #2E7D32);
                }
                QPushButton#navButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #2196F3, stop:1 #1976D2);
                    color: white;
                    border: none;
                    border-radius: 12px;
                    padding: 10px 18px;
                    font-size: 11px;
                    font-weight: 600;
                    box-shadow: 0 3px 6px rgba(33, 150, 243, 0.3);
                }
                QPushButton#navButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #42A5F5, stop:1 #2196F3);
                }
                QPushButton#navButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #1976D2, stop:1 #1565C0);
                }
                QPushButton#navButton:disabled {
                    background: #e0e0e0;
                    color: #9e9e9e;
                    box-shadow: none;
                }
                QPushButton#themeButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #FFB74D, stop:1 #FF9800);
                    color: white;
                    border: none;
                    border-radius: 25px;
                    font-size: 20px;
                    font-weight: bold;
                    box-shadow: 0 4px 12px rgba(255, 152, 0, 0.4);
                }
                QPushButton#themeButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #FFCC80, stop:1 #FFB74D);
                }
                QComboBox#combo {
                    border: 2px solid #e0e0e0;
                    border-radius: 10px;
                    padding: 8px;
                    background-color: white;
                    color: #2c3e50;
                    min-height: 25px;
                }
                QComboBox#combo:hover {
                    border: 2px solid #2196F3;
                }
                QComboBox#combo::drop-down {
                    border: none;
                    border-radius: 8px;
                    width: 30px;
                }
                QComboBox#combo::down-arrow {
                    image: none;
                    border: 2px solid #2c3e50;
                    width: 8px;
                    height: 8px;
                    border-top: none;
                    border-left: none;
                    transform: rotate(45deg);
                    margin-right: 8px;
                }
                QComboBox QAbstractItemView {
                    background-color: white;
                    color: #2c3e50;
                    border: 2px solid #e0e0e0;
                    border-radius: 10px;
                    selection-background-color: #e3f2fd;
                    outline: none;
                }
                QWidget#buttonComboLayout {
                    background-color: white;
                    border-radius: 15px;
                    padding: 15px;
                    margin: 5px;
                    border: 1px solid #e0e0e0;
                }
                QScrollArea#scrollArea {
                    border: 2px solid #e0e0e0;
                    border-radius: 15px;
                    background-color: white;
                }
                QWidget#checkboxGroup {
                    background-color: white;
                }
                QScrollBar:vertical {
                    background-color: #f5f5f5;
                    width: 12px;
                    border-radius: 6px;
                }
                QScrollBar::handle:vertical {
                    background-color: #bdbdbd;
                    border-radius: 6px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #9e9e9e;
                }
                QCheckBox {
                    spacing: 8px;
                    padding: 5px;
                    color: #2c3e50;
                    font-weight: 500;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border-radius: 5px;
                }
            """
        self.setStyleSheet(stylesheet)
        
    def createButtonCombo(self, layout, text, items=None):
        """Create a labeled combo box"""
        buttonComboLayout = QVBoxLayout()
        buttonComboGroup = QWidget()
        buttonComboGroup.setLayout(buttonComboLayout)
        buttonComboGroup.setObjectName("buttonComboLayout")

        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(QFont('Arial', 11, QFont.Weight.Bold))
        label.setObjectName("sectionLabel")
        buttonComboLayout.addWidget(label)

        combo = QComboBox()
        combo.setObjectName("combo")
        
        if items:
            combo.addItems(items)
        buttonComboLayout.addWidget(combo)
        layout.addWidget(buttonComboGroup)
        
        return combo
        
    def addDataset(self):
        """Load CSV dataset(s)"""
        files, _ = QFileDialog.getOpenFileNames(
            self, 
            "Select CSV Datasets", 
            "", 
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not files:
            return
            
        loaded_count = 0
        for file in files:
            try:
                df = pd.read_csv(file)
                
                if df.empty:
                    QMessageBox.warning(self, "Empty File", f"File {file} is empty.")
                    continue
                
                # Convert first column to datetime if possible
                try:
                    df[df.columns[0]] = pd.to_datetime(df[df.columns[0]])
                except:
                    pass
                
                fileName = file.split('/')[-1].split('\\')[-1]
                datasetName = fileName.rsplit('.', 1)[0]
                
                # Handle duplicate names
                original_name = datasetName
                counter = 1
                while datasetName in self.datasets:
                    datasetName = f"{original_name}_{counter}"
                    counter += 1
                
                self.datasets[datasetName] = df
                
                if self.datasetCombo.findText(datasetName) == -1:
                    self.datasetCombo.addItem(datasetName)
                
                loaded_count += 1
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load {file}:\n{str(e)}")
        
        if loaded_count > 0:
            self.datasetCombo.setCurrentIndex(self.datasetCombo.count() - loaded_count)
            self.updateNavigationButtons()
            QMessageBox.information(
                self, 
                "Success", 
                f"Successfully loaded {loaded_count} dataset(s)."
            )
                
    def onDatasetChanged(self):
        """Handle dataset selection change"""
        datasetName = self.datasetCombo.currentText()
        if datasetName and datasetName in self.datasets:
            df = self.datasets[datasetName]
            self.updateCheckboxes(df.columns)
            self.updatePlot()
            self.currentDatasetIndex = list(self.datasets.keys()).index(datasetName)
            
    def getColor(self, idx):
        """Get color for column based on index"""
        colors = plt.cm.tab10.colors
        return colors[idx % len(colors)]
    
    def updateCheckboxes(self, columns):
        """Update checkbox list for dataset columns"""
        # Clear existing checkboxes
        while self.checkboxesLayout.count() > 0:
            item = self.checkboxesLayout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        
        # Re-add label
        self.areaLabel = QLabel("Select Variables to Display")
        self.areaLabel.setObjectName("sectionLabel")
        self.areaLabel.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        self.checkboxesLayout.addWidget(self.areaLabel, 0, 0, 1, 2)
        
        # Create checkboxes
        self.checkboxes = {}
        self.colors = {}
        
        row = 1
        col = 0
        for idx, column in enumerate(columns):
            color = self.getColor(idx)
            self.colors[column] = color
            
            checkbox = QCheckBox(column)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.updatePlot)
            
            # Color indicator style
            color_hex = QColor(*[int(c*255) for c in color]).name()
            checkbox.setStyleSheet(f"""
                QCheckBox::indicator {{
                    background-color: {color_hex};
                    border: 2px solid {color_hex};
                }}
                QCheckBox::indicator:unchecked {{
                    background-color: transparent;
                }}
                QCheckBox::indicator:hover {{
                    border: 2px solid {color_hex};
                }}
            """)
            
            self.checkboxesLayout.addWidget(checkbox, row, col)
            self.checkboxes[column] = checkbox
            
            col += 1
            if col > 1:
                col = 0
                row += 1
        
        # Set minimum height
        minHeight = 40 * ((len(columns) + 1) // 2)
        self.scrollWidget.setMinimumHeight(minHeight)
        
    def updatePlot(self):
        """Update the plot based on current selections"""
        datasetName = self.datasetCombo.currentText()
        if not datasetName or datasetName not in self.datasets:
            return
            
        df = self.datasets[datasetName]
        self.ax.clear()
        
        if df.empty:
            self.ax.set_title("Empty Dataset")
            self.updatePlotTheme()
            self.graphicsFigureCanvas.draw()
            return
        
        xColumn = df.columns[0]
        columns = df.columns[1:]
        
        has_data = False
        
        # Plot original data
        for column in columns:
            if column in self.checkboxes and self.checkboxes[column].isChecked():
                if pd.api.types.is_numeric_dtype(df[column]):
                    df.plot(x=xColumn, y=column, ax=self.ax, label=column, 
                           color=self.colors[column], linewidth=1.8, alpha=0.9)
                    has_data = True
        
        # Apply smoothing
        smoothingMethod = self.smoothingMethodCombo.currentText()
        if smoothingMethod != "None":
            self.applySmoothing(df, xColumn, columns, smoothingMethod)
        
        # Apply trend
        trendMethod = self.trendCombo.currentText()
        if trendMethod != "None":
            self.applyTrend(df, xColumn, columns, trendMethod)
        
        if has_data:
            self.ax.set_title(datasetName, fontsize=13, fontweight='bold', pad=15)
            self.ax.set_xlabel(xColumn, fontweight='600', fontsize=10)
            self.ax.legend(loc='best', fontsize=9, framealpha=0.9, 
                          fancybox=True, shadow=True)
        else:
            self.ax.set_title("No numeric data selected")
        
        self.updatePlotTheme()
        self.graphicsFigureCanvas.figure.tight_layout()
        self.graphicsFigureCanvas.draw()
    
    def applySmoothing(self, df, xColumn, columns, method):
        """Apply smoothing method to selected columns"""
        for column in columns:
            if column in self.checkboxes and self.checkboxes[column].isChecked():
                if pd.api.types.is_numeric_dtype(df[column]):
                    if method == "Simple Exponential Smoothing":
                        y = df[column].ewm(span=5, adjust=False).mean()
                        label = f"{column} (SES)"
                    elif method == "Double Exponential Smoothing":
                        y = df[column].ewm(span=5, adjust=False).mean().ewm(span=5, adjust=False).mean()
                        label = f"{column} (DES)"
                    else:
                        continue
                    
                    self.ax.plot(df[xColumn], y, label=label, 
                               linestyle='--', alpha=0.75, linewidth=1.5)
    
    def applyTrend(self, df, xColumn, columns, method):
        """Apply trend computation to selected columns"""
        for column in columns:
            if column in self.checkboxes and self.checkboxes[column].isChecked():
                if pd.api.types.is_numeric_dtype(df[column]):
                    if method == "Simple Moving Average":
                        trend = df[column].rolling(window=5, center=True).mean()
                        label = f"{column} (SMA)"
                    elif method == "Exponential Moving Average":
                        trend = df[column].ewm(span=5, adjust=False).mean()
                        label = f"{column} (EMA)"
                    else:
                        continue
                    
                    self.ax.plot(df[xColumn], trend, label=label, 
                               linestyle=':', alpha=0.75, linewidth=1.8)
    
    def nextGraphic(self):
        """Navigate to next dataset"""
        datasetNames = list(self.datasets.keys())
        if len(datasetNames) <= 1:
            return
        
        self.currentDatasetIndex = (self.currentDatasetIndex + 1) % len(datasetNames)
        nextDatasetName = datasetNames[self.currentDatasetIndex]
        self.datasetCombo.setCurrentText(nextDatasetName)
    
    def prevGraphic(self):
        """Navigate to previous dataset"""
        datasetNames = list(self.datasets.keys())
        if len(datasetNames) <= 1:
            return
        
        self.currentDatasetIndex = (self.currentDatasetIndex - 1) % len(datasetNames)
        prevDatasetName = datasetNames[self.currentDatasetIndex]
        self.datasetCombo.setCurrentText(prevDatasetName)
    
    def updateNavigationButtons(self):
        """Enable/disable navigation buttons based on dataset count"""
        has_multiple = len(self.datasets) > 1
        self.nextButton.setEnabled(has_multiple)
        self.prevButton.setEnabled(has_multiple)
    
    def exportGraphicOfDataset(self):
        """Export current plot to image file"""
        if not self.datasets:
            QMessageBox.warning(self, "No Data", "Please load a dataset first.")
            return
        
        fileName, _ = QFileDialog.getSaveFileName(
            self, 
            "Export Plot", 
            "", 
            "PNG Image (*.png);;JPEG Image (*.jpg);;PDF Document (*.pdf);;SVG Vector (*.svg)"
        )
        
        if fileName:
            try:
                self.graphicsFigureCanvas.figure.savefig(fileName, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "Success", f"Plot exported to:\n{fileName}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export plot:\n{str(e)}")
    
    def clearAllDatasets(self):
        """Clear all loaded datasets"""
        if not self.datasets:
            return
        
        reply = QMessageBox.question(
            self, 
            "Clear All", 
            "Are you sure you want to clear all datasets?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.datasets.clear()
            self.datasetCombo.clear()
            self.checkboxes.clear()
            self.colors.clear()
            self.currentDatasetIndex = 0
            
            # Clear checkboxes
            while self.checkboxesLayout.count() > 0:
                item = self.checkboxesLayout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
            
            # Reset plot
            self.ax.clear()
            self.ax.set_title("Load a dataset to begin")
            self.updatePlotTheme()
            self.graphicsFigureCanvas.draw()
            
            self.updateNavigationButtons()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())