import sys
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, QComboBox
from PyQt5.QtCore import Qt
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder

class ClimateAdaptationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Climate Adaptation Recommender")
        self.setGeometry(100, 100, 600, 400)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # Input fields
        input_layout = QHBoxLayout()
        self.temp_input = QLineEdit()
        self.rainfall_input = QLineEdit()
        self.soil_input = QComboBox()
        self.soil_input.addItems(['clay', 'loam', 'sandy'])
        self.crop_input = QComboBox()
        self.crop_input.addItems(['corn', 'wheat', 'rice', 'soybean'])

        input_layout.addWidget(QLabel("Temperature (°F):"))
        input_layout.addWidget(self.temp_input)
        input_layout.addWidget(QLabel("Rainfall (inches):"))
        input_layout.addWidget(self.rainfall_input)
        input_layout.addWidget(QLabel("Soil Type:"))
        input_layout.addWidget(self.soil_input)
        input_layout.addWidget(QLabel("Current Crop:"))
        input_layout.addWidget(self.crop_input)

        main_layout.addLayout(input_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.predict_button = QPushButton("Predict")
        self.predict_button.clicked.connect(self.predict)
        self.load_csv_button = QPushButton("Load CSV")
        self.load_csv_button.clicked.connect(self.load_csv)
        button_layout.addWidget(self.predict_button)
        button_layout.addWidget(self.load_csv_button)

        main_layout.addLayout(button_layout)

        # Output area
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        main_layout.addWidget(self.output_text)

        self.model = None
        self.encoders = None

    def load_csv(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv)")
        if file_name:
            try:
                data = pd.read_csv(file_name)
                self.train_model(data)
            except Exception as e:
                self.output_text.setText(f"Error loading CSV: {str(e)}")

    def train_model(self, data):
        X = data[['temperature', 'rainfall', 'soil_type', 'current_crop']]
        y = data['recommended_adaptation']

        self.encoders = {}
        for column in ['soil_type', 'current_crop']:
            le = LabelEncoder()
            X[column] = le.fit_transform(X[column])
            self.encoders[column] = le

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)
        report = classification_report(y_test, y_pred)
        self.output_text.setText(f"Model trained successfully.\n\nModel Evaluation:\n{report}")

    def predict(self):
        if self.model is None:
            self.output_text.setText("Please load a CSV file to train the model first.")
            return

        try:
            temperature = float(self.temp_input.text())
            rainfall = float(self.rainfall_input.text())
            soil_type = self.encoders['soil_type'].transform([self.soil_input.currentText()])[0]
            current_crop = self.encoders['current_crop'].transform([self.crop_input.currentText()])[0]

            input_data = pd.DataFrame({
                'temperature': [temperature],
                'rainfall': [rainfall],
                'soil_type': [soil_type],
                'current_crop': [current_crop]
            })

            prediction = self.model.predict(input_data)
            self.output_text.setText(f"Recommended adaptation strategy: {prediction[0]}")
        except ValueError:
            self.output_text.setText("Please enter valid numeric values for temperature and rainfall.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ClimateAdaptationApp()
    window.show()
    sys.exit(app.exec_())