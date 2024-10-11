from ultralytics import YOLO

# Initialize the YOLO model with the yolov8m configuration
model = YOLO("yolov8m.yaml")

# Train the model using the specified parameters
results = model.train(
    data="config.yaml",  # Configuration file for dataset and other settings
    imgsz=320,           # Image size
    batch=4,             # Batch size
    epochs=100,          # Number of epochs
    lr0=0.01,            # Initial learning rate
    lrf=0.01             # Final learning rate
)

# Saved configurations:
# imgsz=320, batch=2, yolov8n => train16
# imgsz=320, batch=2, yolov8s => train21
# imgsz=320, batch=4, yolov8m => train22
