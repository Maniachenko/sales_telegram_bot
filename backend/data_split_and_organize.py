import os
import shutil
from sklearn.model_selection import train_test_split

# Define source and destination directories
source_dir = './item_processing_cvat/obj_train_data'
destination_dir = './item_processing/data'

# Define split ratios
train_ratio = 0.8
val_ratio = 0.1
test_ratio = 0.1

# Create directories for train, val, and test sets
sets = ['train', 'val', 'test']
for set_type in sets:
    os.makedirs(os.path.join(destination_dir, set_type, 'images'), exist_ok=True)
    os.makedirs(os.path.join(destination_dir, set_type, 'labels'), exist_ok=True)

# Get list of all images and corresponding labels (.txt files)
all_images = [f for f in os.listdir(source_dir) if f.endswith(('.jpeg', '.jpg', '.png'))]
all_labels = [f.replace('.jpeg', '.txt').replace('.jpg', '.txt').replace('.png', '.txt') for f in all_images]

# Split item_names into train, validation, and test sets
train_images, temp_images, train_labels, temp_labels = train_test_split(
    all_images, all_labels, test_size=(val_ratio + test_ratio), random_state=42
)

val_images, test_images, val_labels, test_labels = train_test_split(
    temp_images, temp_labels, test_size=test_ratio / (val_ratio + test_ratio), random_state=42
)

# Function to move images and labels to the corresponding directories
def move_files(image_list, label_list, set_type):
    for image, label in zip(image_list, label_list):
        # Move images
        image_src_path = os.path.join(source_dir, image)
        image_dst_path = os.path.join(destination_dir, set_type, 'images', image)
        shutil.copy(image_src_path, image_dst_path)

        # Move corresponding labels
        label_src_path = os.path.join(source_dir, label)
        label_dst_path = os.path.join(destination_dir, set_type, 'labels', label)
        if os.path.exists(label_src_path):  # Only copy label if it exists
            shutil.copy(label_src_path, label_dst_path)

# Move train, validation, and test sets to their respective directories
move_files(train_images, train_labels, 'train')
move_files(val_images, val_labels, 'val')
move_files(test_images, test_labels, 'test')

print("Dataset successfully split into train, validation, and test sets!")
