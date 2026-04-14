"""File Organizer - Organize files by type into categorized folders.

This script scans a source directory and moves files into category-based
folders (Images, Videos, Audio, etc.) based on file extensions.
"""

import os
import shutil

# Constants
DEFAULT_CATEGORY = "other"
DUPLICATE_SUFFIX = "_{}"

# File category mapping
FILE_CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"],
    "Videos": [".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".mpeg"],
    "Audio": [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"],
    "Documents": [".pdf", ".docx", ".txt", ".xlsx", ".pptx", ".odt", ".rtf"],
    "Archives": [".zip", ".rar", ".tar", ".gz", ".7z", ".iso"],
    "Project Files": [".psd", ".ai", ".indd", ".sketch", ".xd", ".fig", ".prproj", ".aep"],
    "Subtitles": [".srt", ".sub", ".vtt", ".csv", ".tsv"],
    DEFAULT_CATEGORY: []
}

def is_directory_empty(directory_path):
    """Check if a directory is empty.
    
    Args:
        directory_path (str): Path to the directory to check.
    
    Returns:
        bool: True if directory is empty, False otherwise.
    """
    try:
        for _ in os.scandir(directory_path):
            return False
        return True
    except OSError:
        return False


def find_category_for_file(filename, categories):
    """Find the appropriate category for a file based on extension.
    
    Args:
        filename (str): Name of the file.
        categories (dict): Mapping of category names to file extensions.
    
    Returns:
        str: Category name, or DEFAULT_CATEGORY if no match found.
    """
    file_ext = os.path.splitext(filename)[1].lower()
    
    for category, extensions in categories.items():
        if file_ext in extensions:
            return category
    
    return DEFAULT_CATEGORY


def handle_duplicate_filename(target_folder, filename):
    """Generate a unique filename if one already exists in the folder.
    
    Args:
        target_folder (str): Target directory path.
        filename (str): Original filename.
    
    Returns:
        str: Original filename if unique, or modified name with counter suffix.
    """
    target_file_path = os.path.join(target_folder, filename)
    
    if not os.path.exists(target_file_path):
        return target_file_path
    
    base_name, ext = os.path.splitext(filename)
    counter = 1
    
    while os.path.exists(target_file_path):
        new_filename = f"{base_name}{DUPLICATE_SUFFIX.format(counter)}{ext}"
        target_file_path = os.path.join(target_folder, new_filename)
        counter += 1
    
    return target_file_path


def create_folders(target_dir, folders):
    """Create category folders in the target directory.
    
    Args:
        target_dir (str): Target directory path.
        folders (iterable): Collection of folder names to create.
    """
    for folder in folders:
        folder_path = os.path.join(target_dir, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

def organize_files_by_type(source_dir, target_dir, categories, operation="move"):
    """Recursively scan source directory and organize files by category.
    
    Args:
        source_dir (str): Source directory path.
        target_dir (str): Target directory path.
        categories (dict): Mapping of category names to file extensions.
        operation (str): Either "move" or "copy". Determines file operation.
    
    Returns:
        tuple: (files_moved_count, files_failed_count)
    """
    files_processed = 0
    files_failed = 0
    
    for root, dirs, files in os.walk(source_dir):
        for filename in files:
            file_path = os.path.join(root, filename)
            
            try:
                # Determine the category for this file
                category = find_category_for_file(filename, categories)
                
                # Ensure category folder exists
                target_folder = os.path.join(target_dir, category)
                if not os.path.exists(target_folder):
                    os.makedirs(target_folder)
                
                # Get unique target path (handling duplicates)
                target_file_path = handle_duplicate_filename(target_folder, filename)
                
                # Perform the file operation (move or copy)
                if operation.lower() == "copy":
                    shutil.copy2(file_path, target_file_path)
                    action = "Copied"
                else:
                    shutil.move(file_path, target_file_path)
                    action = "Moved"
                
                print(f"{action} {filename} to {category}/")
                files_processed += 1
                
            except Exception as error:
                print(f"Error {operation}ing {filename}: {error}")
                files_failed += 1
    
    return files_processed, files_failed

def main():
    """Main entry point for the file organizer."""
    print("=" * 50)
    print("File Organizer by Extension")
    print("=" * 50)
    
    try:
        # Get directories from user
        source_dir = input("\nPlease enter source directory: ").strip()
        target_dir = input("Please enter target directory: ").strip()
        
        # Validate directories exist
        if not os.path.exists(source_dir):
            print(f"\nError: Source directory '{source_dir}' does not exist.")
            return 1
        if not os.path.exists(target_dir):
            print(f"Error: Target directory '{target_dir}' does not exist.")
            return 1
        
        # Ask user to choose between copy and move
        print("\nChoose operation:")
        print("1. Copy files (original files will remain in source)")
        print("2. Move files (original files will be moved to target)")
        choice = input("Enter your choice (1 or 2): ").strip()
        
        if choice == "2":
            operation = "move"
            print("Selected: Move")
        else:
            operation = "copy"
            print("Selected: Copy")
        
        # Check if target directory is empty
        is_empty = is_directory_empty(target_dir)
        status = "empty" if is_empty else "not empty"
        print(f"\nTarget directory is {status}.")
        
        # Confirm if target directory is not empty
        if not is_empty:
            confirm = input("\nTarget directory is not empty. Continue? (y/n): ").lower()
            if confirm != 'y':
                print("Operation cancelled.")
                return 0
        
        # Create category folders
        print("\nCreating category folders...")
        create_folders(target_dir, FILE_CATEGORIES.keys())
        
        # Organize files
        print("\nOrganizing files...")
        files_processed, files_failed = organize_files_by_type(source_dir, target_dir, FILE_CATEGORIES, operation)
        
        # Display summary
        print("\n" + "=" * 50)
        print(f"File organization complete!")
        print(f"Files {operation}d: {files_processed}")
        if files_failed > 0:
            print(f"Files failed: {files_failed}")
        print("=" * 50)
        
        return 0
        
    except Exception as error:
        print(f"\nAn error occurred: {error}")
        return 1


if __name__ == "__main__":
    exit(main())
