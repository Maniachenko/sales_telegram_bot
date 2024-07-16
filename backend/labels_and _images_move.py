import os
import shutil
from sklearn.model_selection import train_test_split


def move_files(files, src_path, dest_path):
    """Move specified files from source to destination directory."""
    for f in files:
        shutil.move(os.path.join(src_path, f), os.path.join(dest_path, f))


def split_dataset(base_path, train_size=0.7, val_size=0.15, test_size=0.15):
    assert train_size + val_size + test_size == 1, "The sizes must sum up to 1"

    images_path = os.path.join(base_path, 'train', 'images')
    labels_path = os.path.join(base_path, 'train', 'labels')

    # Listing all images and labels
    image_files = [f for f in os.listdir(images_path) if os.path.isfile(os.path.join(images_path, f))]
    label_files = [f for f in os.listdir(labels_path) if os.path.isfile(os.path.join(labels_path, f))]

    # Splitting the dataset
    train_images, test_images = train_test_split(image_files, test_size=test_size, random_state=42)
    val_images, test_images = train_test_split(test_images, test_size=test_size / (test_size + val_size),
                                               random_state=42)

    # Creating directories for the new split
    for split in ['train', 'val', 'test']:
        for subdir in ['images', 'labels']:
            os.makedirs(os.path.join(base_path, split, subdir), exist_ok=True)

    # Moving the files
    move_files(train_images, images_path, os.path.join(base_path, 'train', 'images'))
    move_files(val_images, images_path, os.path.join(base_path, 'val', 'images'))
    move_files(test_images, images_path, os.path.join(base_path, 'test', 'images'))

    # Since we assume labels correspond to images, we move labels based on image file names
    for image_file in train_images + val_images + test_images:
        label_file = image_file.rsplit('.', 1)[0] + '.txt'
        if label_file in label_files:
            original_label_path = os.path.join(labels_path, label_file)
            if image_file in train_images:
                shutil.move(original_label_path, os.path.join(base_path, 'train', 'labels', label_file))
            elif image_file in val_images:
                shutil.move(original_label_path, os.path.join(base_path, 'val', 'labels', label_file))
            elif image_file in test_images:
                shutil.move(original_label_path, os.path.join(base_path, 'test', 'labels', label_file))


if __name__ == "__main__":
    base_path = '/item_detector/data'  # Adjust this to your base path
    split_dataset(base_path)
    print("Dataset split and organized successfully.")
