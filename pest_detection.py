import tensorflow as tf
from tensorflow.keras import layers, models
import numpy as np

# Define the CNN model
def create_model():
    model = models.Sequential([
        layers.Conv2D(32, (3, 3), activation='relu', input_shape=(224, 224, 3)),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.Flatten(),
        layers.Dense(64, activation='relu'),
        layers.Dense(10, activation='softmax')  # 10 classes of pests
    ])

    model.compile(optimizer='adam',
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])
    
    return model

# Generate some dummy data for demonstration
def generate_dummy_data():
    # Generate 1000 random images
    X = np.random.rand(1000, 224, 224, 3)
    # Generate random labels (0-9)
    y = np.random.randint(0, 10, 1000)
    return X, y

def main():
    # Create the model
    model = create_model()

    # Print model summary
    print("Model Summary:")
    model.summary()

    # Generate dummy data
    X, y = generate_dummy_data()

    # Split data into train and test sets
    train_images, test_images = X[:800], X[800:]
    train_labels, test_labels = y[:800], y[800:]

    # Train the model
    print("\nTraining the model...")
    history = model.fit(train_images, train_labels, epochs=5, 
                        validation_data=(test_images, test_labels), verbose=1)

    # Evaluate the model
    print("\nEvaluating the model...")
    test_loss, test_acc = model.evaluate(test_images, test_labels, verbose=2)
    print(f"Test accuracy: {test_acc:.4f}")

    # Make a sample prediction
    print("\nMaking a sample prediction...")
    sample_image = np.random.rand(1, 224, 224, 3)  # One random image
    prediction = model.predict(sample_image)
    predicted_class = np.argmax(prediction)
    print(f"Predicted class: {predicted_class}")
    print(f"Class probabilities: {prediction[0]}")

if __name__ == "__main__":
    main()