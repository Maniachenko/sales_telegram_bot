import cv2
import os
from glob import glob
from ultralytics import YOLO

images_path = "../item_detector/data/train/images"
fragments_save_path = "data"

if not os.path.exists(fragments_save_path):
    os.makedirs(fragments_save_path)

model = YOLO("/backend/item_detector/runs/detect/train/weights/best.pt")


def process_and_save_fragments(image_path):
    img_array = cv2.imread(image_path)
    if img_array is None:
        print(f"Failed to read {image_path}")
        return

    img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)

    # Get image dimensions
    height, width, _ = img_array.shape

    results = model(img_array)

    fragment_counter = 0

    for result in results:
        if result.boxes is not None:
            for box in result.boxes.xyxy:
                x1, y1, x2, y2 = map(int, box.cpu().numpy().tolist()[:4])

                extension_x = int((x2 - x1) * 0.07)
                extension_y = int((y2 - y1) * 0.07)

                x1 = max(0, x1 - extension_x)
                y1 = max(0, y1 - extension_y)
                x2 = min(width, x2 + extension_x)
                y2 = min(height, y2 + extension_y)

                img_fragment = img_array[y1:y2, x1:x2]

                img_fragment = cv2.cvtColor(img_fragment, cv2.COLOR_RGB2BGR)

                fragment_path = os.path.join(fragments_save_path,
                                             f"{os.path.basename(image_path).split('.')[0]}_fragment_{fragment_counter}.png")
                cv2.imwrite(fragment_path, img_fragment)
                print(f"Fragment saved to {fragment_path}")
                fragment_counter += 1

        else:
            print(f"No detections for {os.path.basename(image_path)}.")

image_files = glob(os.path.join(images_path, "*.jpeg")) + glob(os.path.join(images_path, "*.png"))

for image_file in image_files:
    process_and_save_fragments(image_file)
