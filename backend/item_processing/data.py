import os
import random
import shutil

def delete_empty_label_files(label_dir):
    all_labels = [f for f in os.listdir(label_dir) if f.endswith('.txt')]
    for label in all_labels:
        label_path = os.path.join(label_dir, label)
        if os.path.getsize(label_path) == 0:
            os.remove(label_path)

def filter_and_remove_images(image_dir, label_dir):
    all_images = [f for f in os.listdir(image_dir) if f.endswith('.png')]
    filtered_images = []
    for image in all_images:
        label_file = os.path.join(label_dir, image.replace('.png', '.txt'))
        if os.path.exists(label_file):
            filtered_images.append(image)
        else:
            os.remove(os.path.join(image_dir, image))
    return filtered_images

def split_data(data, train_ratio=0.9):
    random.shuffle(data)
    split_idx = int(len(data) * train_ratio)
    train_data = data[:split_idx]
    val_data = data[split_idx:]
    return train_data, val_data

def create_directories(base_dir, subdirs):
    for subdir in subdirs:
        os.makedirs(os.path.join(base_dir, subdir), exist_ok=True)

def move_files(data, source_dir, target_dir, file_type):
    for file in data:
        if file_type == 'image':
            src_file = os.path.join(source_dir, file)
            tgt_file = os.path.join(target_dir, 'images', file)
            shutil.move(src_file, tgt_file)
        elif file_type == 'label':
            src_file = os.path.join(source_dir, file.replace('.png', '.txt'))
            tgt_file = os.path.join(target_dir, 'labels', file.replace('.png', '.txt'))
            shutil.move(src_file, tgt_file)

base_dir = 'data'
image_dir = os.path.join(base_dir, 'images')
label_dir = os.path.join(base_dir, 'labels')

# Delete empty label files before filtering images
delete_empty_label_files(label_dir)

# Filter and remove images that don't have a corresponding label file
filtered_images = filter_and_remove_images(image_dir, label_dir)

# Split data into training and validation sets
train_images, val_images = split_data(filtered_images)

# Create necessary directories
create_directories(base_dir, ['train/images', 'train/labels', 'val/images', 'val/labels'])

# Move image and label files to appropriate directories
move_files(train_images, image_dir, os.path.join(base_dir, 'train'), 'image')
move_files(train_images, label_dir, os.path.join(base_dir, 'train'), 'label')
move_files(val_images, image_dir, os.path.join(base_dir, 'val'), 'image')
move_files(val_images, label_dir, os.path.join(base_dir, 'val'), 'label')

print(f'Training set: {len(train_images)} images')
print(f'Validation set: {len(val_images)} images')
