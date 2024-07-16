from ultralytics import YOLO

model = YOLO("yolov8n.yaml")

results = model.train(data="config.yaml", batch=2, epochs=200)