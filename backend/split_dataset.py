#!/usr/bin/env python3

import os
import shutil
import argparse
from sklearn.model_selection import train_test_split

def move_files(files, split, images_path, labels_path):
    for f in files:
        # Move the image file
        shutil.move(os.path.join(images_path, f), os.path.join(images_path, split, f))
        # Correctly replace the file extension from .jpeg to .txt for label files
        label_file = f.replace('.jpeg', '.txt')
        label_file_path = os.path.join(labels_path, label_file)
        # Check if the label file exists before moving it
        if os.path.exists(label_file_path):
            shutil.move(label_file_path, os.path.join(labels_path, split, label_file))
        else:
            print(f"Label file does not exist for {f}, skipping.")

def split_dataset(base_path):
    images_path = os.path.join(base_path, 'images')
    labels_path = os.path.join(base_path, 'labels')

    # Create subdirectories for train, val, and test splits
    for split in ['train', 'val', 'test']:
        os.makedirs(os.path.join(images_path, split), exist_ok=True)
        os.makedirs(os.path.join(labels_path, split), exist_ok=True)

    # List all image files in the images directory
    image_files = [f for f in os.listdir(images_path) if os.path.isfile(os.path.join(images_path, f))]

    print(images_path)
    # Split the dataset into training, validation, and test sets
    train_files, test_files = train_test_split(image_files, test_size=0.30, random_state=42)
    val_files, test_files = train_test_split(test_files, test_size=0.50, random_state=42)

    # Execute the file moving for each split
    move_files(train_files, 'train', images_path, labels_path)
    move_files(val_files, 'val', images_path, labels_path)
    move_files(test_files, 'test', images_path, labels_path)

    print('Dataset split completed.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Split dataset into training, validation, and test sets.")
    parser.add_argument('--base_path', type=str, required=True, help='Base path for the dataset')
    args = parser.parse_args()

    split_dataset(args.base_path)
