from ultralytics import YOLO

# Initialize the YOLO model with the yolov8n configuration
model = YOLO("yolov8n.yaml")

# Train the model using the specified parameters
results = model.train(
    data="config.yaml",  # Configuration file for dataset and other settings
    imgsz=320,           # Image size
    batch=8,             # Batch size
    classes=[0, 2, 3, 4, 5, 7]  # Selected classes to train on
)

# Saved configurations:
# imgsz=640, batch=4 => train 2
# imgsz=320, batch=32 => train 5
# imgsz=320, batch=4 => train 6
# imgsz=320, batch=8 => train 7