#!/user/bin/env python3

import os
import sys
from random import shuffle
from shutil import copy


def deal_with_cultivars():
    basedir = "./dataset"
    folder_names = [f[0].split("/")[-1] for f in os.walk(basedir)]

    # folder names: eg Beryl's Gem => Beryls Gem (breaks processing later on)
    cultivar_folders_with_possessive_apostrophe = [f for f in folder_names if "'s " in f]
    for cultivar in cultivar_folders_with_possessive_apostrophe:
        os.rename(os.path.join(basedir, cultivar),
                  os.path.join(basedir, cultivar.replace("'s ", "s ")))

    # cultivars with no species: eg Westringia 'Deep Purple'
    #   Either find the correct species, and then move all files to the species,
    #   Or delete the cultivar, as this would confuse the species classification
    cultivar_folders_without_species = [(f, f.split("'")[:-1]) for f in folder_names if
                                        f.count("'") >= 2 and  # contains apostrophied name
                                        len(f.split("'")[0].strip().split(" ")) == 1]  # species name is missing
    for (full_folder_name, breakdown) in cultivar_folders_without_species:
        new_name = ""

        for folder_to_check in folder_names:
            if breakdown[1] in folder_to_check and \
                    folder_to_check != full_folder_name and \
                    full_folder_name.split(" ")[0] in folder_to_check:
                new_name = folder_to_check

        species_found = new_name != ""
        current_path = os.path.join(basedir, full_folder_name)
        if species_found:  # Species found, move all files and delete folder
            for root, dir, files in os.walk(current_path):
                old_file_paths = [os.path.join(current_path, file_name) for file_name in files]
                for file_path in old_file_paths:
                    os.rename(file_path, file_path.replace(full_folder_name, new_name))
        else:  # Species not found, delete images and delete folder
            for root, dir, files in os.walk(current_path):
                file_paths = [os.path.join(current_path, file_name) for file_name in files]
                for file_path in file_paths:
                    os.remove(file_path)
        os.rmdir(current_path)

    # cultivars with species attached, should have cultivar data removed
    cultivar_folders_remaining = [f for f in folder_names if
                                  f.count("'") >= 2]
    for cultivar_folder in cultivar_folders_remaining:
        non_cultivar_species_exists = cultivar_folder.split("'")[0].strip() in folder_names
        folder_path = os.path.join(basedir, cultivar_folder)

        for _, _, files in os.walk(folder_path):
            for f in files:
                if non_cultivar_species_exists:  # Move all files to non-cultivar species, delete folder
                    os.rename(
                        os.path.join(folder_path, f),
                        os.path.join(folder_path.split("'")[0].strip(), f))
                else:  # Remove all images, delete folder
                    os.remove(os.path.join(folder_path, f))

        os.rmdir(folder_path)


def remove_small_folders():
    """
    Folders too small (<3 examples) can't be split for training/validation/testing
    Delete images in such folders, and then their folders
    """
    basedir = "./dataset"

    for root, dir, files in os.walk(basedir):
        if root != basedir and len(files) < 3:
            print(f"Folder to delete {root} {files}")

            [os.remove(os.path.join(root, f)) for f in files]
            os.rmdir(root)

            print("Done")


def generate_split():
    """
    Generate a split folder, in ../split-0/
    Should contain the following folders: train|val|test
    """

    basedir = "./dataset"
    split_dir = "./split-0"
    train_dir, val_dir, test_dir = [os.path.join(split_dir, c) for c in ["train", "val", "test"]]
    [os.path.isdir(d) or os.mkdir(d) for d in [split_dir, train_dir, val_dir, test_dir]]

    for root, dir, files in os.walk(basedir):
        if root != basedir:
            species_name = root.split("/")[-1]
            for current_directory in [train_dir, val_dir, test_dir]:
                if not os.path.isdir(os.path.join(current_directory, species_name)):
                    os.mkdir(os.path.join(current_directory, species_name))

            # Allocate 15% each (or 1, whichever is higher) to test and val, then the rest to train
            file_count = len(files)
            file_paths = [os.path.join(root, f) for f in files]

            test_and_val_count = max(1, round(file_count * .15))
            shuffle(file_paths)

            test_files = [file_paths.pop() for _ in range(test_and_val_count)]
            val_files = [file_paths.pop() for _ in range(test_and_val_count)]
            train_files = file_paths

            [copy(test_file, test_file.replace(basedir, test_dir)) for test_file in test_files]
            [copy(val_file, val_file.replace(basedir, val_dir)) for val_file in val_files]
            [copy(train_file, train_file.replace(basedir, train_dir)) for train_file in train_files]


if __name__ == '__main__':
    task = sys.argv[1]
    if task == "cultivars":
        deal_with_cultivars()
    elif task == "delete-small":
        remove_small_folders()
    elif task == "split":
        generate_split()
