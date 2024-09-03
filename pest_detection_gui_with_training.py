import sys
import os
import shutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, 
                             QLabel, QFileDialog, QMessageBox, QProgressBar, QListWidget, QListWidgetItem)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import numpy as np

class ModelTrainer(QThread):
    update_progress = pyqtSignal(int)
    training_complete = pyqtSignal(str)
    training_error = pyqtSignal(str)

    def __init__(self, train_dir, class_names):
        super().__init__()
        self.train_dir = train_dir
        self.class_names = class_names

    def run(self):
        try:
            img_height, img_width = 150, 150
            batch_size = 32

            train_datagen = ImageDataGenerator(
                rescale=1./255,
                rotation_range=20,
                width_shift_range=0.2,
                height_shift_range=0.2,
                shear_range=0.2,
                zoom_range=0.2,
                horizontal_flip=True,
                validation_split=0.2)

            train_generator = train_datagen.flow_from_directory(
                self.train_dir,
                target_size=(img_height, img_width),
                batch_size=batch_size,
                class_mode='categorical',
                subset='training')

            validation_generator = train_datagen.flow_from_directory(
                self.train_dir,
                target_size=(img_height, img_width),
                batch_size=batch_size,
                class_mode='categorical',
                subset='validation')

            model = models.Sequential([
                layers.Conv2D(32, (3, 3), activation='relu', input_shape=(img_height, img_width, 3)),
                layers.MaxPooling2D((2, 2)),
                layers.Conv2D(64, (3, 3), activation='relu'),
                layers.MaxPooling2D((2, 2)),
                layers.Conv2D(64, (3, 3), activation='relu'),
                layers.Flatten(),
                layers.Dense(64, activation='relu'),
                layers.Dense(len(self.class_names), activation='softmax')
            ])

            model.compile(optimizer='adam',
                          loss='categorical_crossentropy',
                          metrics=['accuracy'])

            epochs = 10
            for epoch in range(epochs):
                model.fit(train_generator, 
                          steps_per_epoch=train_generator.samples // batch_size, 
                          validation_data=validation_generator,
                          validation_steps=validation_generator.samples // batch_size,
                          epochs=1,
                          verbose=0)
                self.update_progress.emit((epoch + 1) * 100 // epochs)

            model.save('pest_detection_model.h5')
            self.training_complete.emit('Model training complete!')
        except Exception as e:
            self.training_error.emit(str(e))

class PestDetectionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pest Detection Tool")
        self.setGeometry(100, 100, 800, 600)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)

        self.load_directory_button = QPushButton("Load Image Directory")
        self.load_directory_button.clicked.connect(self.load_image_directory)
        layout.addWidget(self.load_directory_button)

        self.image_list = QListWidget(self)
        self.image_list.itemClicked.connect(self.display_selected_image)
        layout.addWidget(self.image_list)

        self.train_button = QPushButton("Train Model")
        self.train_button.clicked.connect(self.train_model)
        layout.addWidget(self.train_button)

        self.detect_button = QPushButton("Detect Pests")
        self.detect_button.clicked.connect(self.detect_pests)
        layout.addWidget(self.detect_button)

        self.progress_bar = QProgressBar(self)
        layout.addWidget(self.progress_bar)

        self.result_label = QLabel("No image loaded")
        self.result_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.result_label)

        self.image_paths = []
        self.current_image_path = None
        self.model = None
        self.class_names = []

    def load_image_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Image Directory")
        if directory:
            self.image_list.clear()
            self.image_paths = []
            self.class_names = set()
            for filename in os.listdir(directory):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    image_path = os.path.join(directory, filename)
                    self.add_image_to_list(image_path)
                    class_name = filename.split('_')[0]  # Assuming format: classname_*.png
                    self.class_names.add(class_name)
            self.class_names = list(self.class_names)
            self.result_label.setText(f"Loaded {len(self.image_paths)} images from {len(self.class_names)} classes")

    def add_image_to_list(self, image_path):
        self.image_paths.append(image_path)
        item = QListWidgetItem(os.path.basename(image_path))
        item.setData(Qt.UserRole, image_path)
        self.image_list.addItem(item)

    def display_selected_image(self, item):
        image_path = item.data(Qt.UserRole)
        self.current_image_path = image_path
        pixmap = QPixmap(image_path)
        scaled_pixmap = pixmap.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)
        self.result_label.setText("Image loaded. Click 'Detect Pests' to analyze.")

    def prepare_training_data(self):
        train_dir = os.path.join(os.path.dirname(self.image_paths[0]), 'training_data')
        if os.path.exists(train_dir):
            shutil.rmtree(train_dir)
        os.makedirs(train_dir)
        
        for class_name in self.class_names:
            os.makedirs(os.path.join(train_dir, class_name))
        
        for image_path in self.image_paths:
            filename = os.path.basename(image_path)
            class_name = filename.split('_')[0]
            dst = os.path.join(train_dir, class_name, filename)
            shutil.copy(image_path, dst)
        
        return train_dir

    def train_model(self):
        if not self.image_paths:
            QMessageBox.warning(self, "No Images", "Please load images first.")
            return
        
        train_dir = self.prepare_training_data()
        self.trainer = ModelTrainer(train_dir, self.class_names)
        self.trainer.update_progress.connect(self.update_progress_bar)
        self.trainer.training_complete.connect(self.training_finished)
        self.trainer.training_error.connect(self.training_error)
        self.trainer.start()
        self.train_button.setEnabled(False)
        self.detect_button.setEnabled(False)

    def update_progress_bar(self, value):
        self.progress_bar.setValue(value)

    def training_finished(self, message):
        self.result_label.setText(message)
        self.train_button.setEnabled(True)
        self.detect_button.setEnabled(True)
        self.model = tf.keras.models.load_model('pest_detection_model.h5')

    def training_error(self, error_message):
        QMessageBox.critical(self, "Training Error", error_message)
        self.train_button.setEnabled(True)
        self.detect_button.setEnabled(True)

    def detect_pests(self):
        if not self.current_image_path:
            QMessageBox.warning(self, "No Image", "Please select an image first.")
            return

        if not self.model:
            QMessageBox.warning(self, "No Model", "Please train the model first.")
            return

        try:
            img = tf.keras.preprocessing.image.load_img(self.current_image_path, target_size=(150, 150))
            img_array = tf.keras.preprocessing.image.img_to_array(img)
            img_array = tf.expand_dims(img_array, 0)

            predictions = self.model.predict(img_array)
            predicted_class = self.class_names[np.argmax(predictions[0])]
            confidence = round(100 * np.max(predictions[0]), 2)

            result_text = f"Detected: {predicted_class}\nConfidence: {confidence}%"
            self.result_label.setText(result_text)
        except Exception as e:
            QMessageBox.critical(self, "Detection Error", str(e))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PestDetectionApp()
    window.show()
    sys.exit(app.exec_())