import os
import shutil

# Define your directories
base_dir = 'data'  # Adjust this to your base directory path
obj_train_data_dir = os.path.join(base_dir, 'obj_train_data')
datasets = ['test', 'train', 'val']

for dataset in datasets:
    images_dir = os.path.join(base_dir, dataset, 'images')
    labels_dir = os.path.join(base_dir, dataset, 'labels')

    # Make sure labels directory exists
    os.makedirs(labels_dir, exist_ok=True)

    # Iterate through each image file in the images directory
    for image_file in os.listdir(images_dir):
        # Derive the base filename without extension
        base_filename = os.path.splitext(image_file)[0]

        # Define the corresponding .txt file path in obj_train_data
        txt_file_path = os.path.join(obj_train_data_dir, f"{base_filename}.txt")

        # Check if this .txt file exists
        if os.path.exists(txt_file_path):
            # Define the destination path for the .txt file in the labels directory
            dest_txt_file_path = os.path.join(labels_dir, f"{base_filename}.txt")

            # Copy the .txt file to the labels directory, replacing if it already exists
            shutil.copy(txt_file_path, dest_txt_file_path)
            print(f"Copied {txt_file_path} to {dest_txt_file_path}")
        else:
            print(f"No corresponding .txt file found for {image_file} in obj_train_data")

print("Processing complete.")
