"""File Organizer - Organize files by type into categorized folders.

This script scans a source directory and moves files into category-based
folders (Images, Videos, Audio, etc.) based on file extensions.
"""

import os
import shutil
import re
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

# Constants
DEFAULT_CATEGORY = "other"
DUPLICATE_SUFFIX = "_{}"
ORGANIZER_LOG_FILE = ".organizer_log.txt"
PREMIERE_PRO_PATTERN = re.compile(
    r'--[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}-\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}(_\d+)?',
    re.IGNORECASE
)
AFTER_EFFECTS_PATTERN = re.compile(r'auto-save', re.IGNORECASE)

# File category mapping - supports nested paths like "Category/Subfolder"
FILE_CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"],
    "Images/working documents": [".psd", ".ai", ".indd"],  # AI design files go to Images/AI subfolder
    "Videos": [".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".mpeg"],
    "Audio": [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"],
    "Documents": [".pdf", ".docx", ".txt", ".xlsx", ".pptx", ".odt", ".rtf"],
    "Archives": [".zip", ".rar", ".tar", ".gz", ".7z", ".iso"],
    "Project Files": [".sketch", ".xd", ".fig", ".prproj", ".aep"],
    "Project Files/Autosave": [".autosave", ".bak"],  # Autosave files go to Project Files/Autosave
    "Subtitles": [".srt", ".sub", ".vtt", ".csv", ".tsv"],
    DEFAULT_CATEGORY: []
}
EXTENSION_MAP = {
    ext: category
    for category, exts in FILE_CATEGORIES.items()
    for ext in exts
}

def is_directory_empty(directory_path: str) -> bool:
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


def is_premiere_pro_autosave(filename: str) -> bool:
    """Check if a file is a Premiere Pro autosave file based on filename pattern.
    
    Premiere Pro autosaves follow the pattern:
    ProjectName--GUID-TIMESTAMP[_number]
    where GUID is a UUID format and TIMESTAMP is YYYY-MM-DD_HH-MM-SS
    The trailing _number is optional.
    
    Args:
        filename (str): Name of the file.
    
    Returns:
        bool: True if file matches Premiere Pro autosave pattern, False otherwise.
    """
    return bool(PREMIERE_PRO_PATTERN.search(filename))


def is_after_effects_autosave(filename: str) -> bool:
    """Check if a file is an After Effects autosave file based on filename pattern.
    
    After Effects autosaves contain "auto-save" in the filename.
    Example: "room particle auto-save 6_1"
    
    Args:
        filename (str): Name of the file.
    
    Returns:
        bool: True if file matches After Effects autosave pattern, False otherwise.
    """
    return bool(AFTER_EFFECTS_PATTERN.search(filename))


def find_category_for_file(filename: str) -> str:
    """Find the appropriate category for a file based on extension or pattern.
    
    Args:
        filename (str): Name of the file.
    
    Returns:
        str: Category name, or DEFAULT_CATEGORY if no match found.
    """
    # Check for autosave files first (Premiere Pro and After Effects)
    if is_premiere_pro_autosave(filename) or is_after_effects_autosave(filename):
        return "Project Files/Autosave"
    
    # Then check file extension
    file_ext = os.path.splitext(filename)[1].lower()
    return EXTENSION_MAP.get(file_ext, DEFAULT_CATEGORY)


def handle_duplicate_filename(target_folder: str, filename: str, check_existing: bool = True) -> str:
    """Generate a unique filename if one already exists in the folder.
    
    Args:
        target_folder (str): Target directory path.
        filename (str): Original filename.
        check_existing (bool): If True, check for existing files and add numeric suffix.
                              If False, return path as-is. Default is True.
    
    Returns:
        str: Filename path that doesn't conflict with existing files.
    """
    if not check_existing:
        return os.path.join(target_folder, filename)
    
    target_file_path = os.path.join(target_folder, filename)
    base_name, ext = os.path.splitext(filename)
    counter = 1
    
    while os.path.exists(target_file_path):
        new_filename = f"{base_name}{DUPLICATE_SUFFIX.format(counter)}{ext}"
        target_file_path = os.path.join(target_folder, new_filename)
        counter += 1
    
    return target_file_path


def remove_empty_directories(directory_path: str, preserve_root: bool = True) -> int:
    """Recursively remove empty directories.
    
    Args:
        directory_path (str): Top-level directory to start removing from.
        preserve_root (bool): If True, don't delete the root directory itself.
    
    Returns:
        int: Number of directories removed.
    """
    removed_count = 0
    
    try:
        # Walk bottom-up so we remove children before parents
        for root, dirs, files in os.walk(directory_path, topdown=False):
            for directory in dirs:
                full_path = os.path.join(root, directory)
                try:
                    if is_directory_empty(full_path):
                        os.rmdir(full_path)
                        logging.debug(f"Removed empty directory: {full_path}")
                        removed_count += 1
                except OSError as e:
                    logging.debug(f"Could not remove directory {full_path}: {e}")
        
        # Optionally remove the root directory if empty and preserve_root is False
        if not preserve_root and is_directory_empty(directory_path):
            try:
                os.rmdir(directory_path)
                removed_count += 1
            except OSError:
                pass
    
    except Exception as e:
        logging.error(f"Error removing empty directories: {e}")
    
    return removed_count


def display_preview(operations: list, operation_type: str) -> None:
    """Display a detailed preview of what would be organized.
    
    Args:
        operations (list): List of operation dictionaries to preview.
        operation_type (str): "move" or "copy".
    """
    print("\n" + "=" * 80)
    print("PREVIEW - The following files would be organized:")
    print("=" * 80)
    
    if not operations:
        print("No files to organize.")
        return
    
    # Group operations by category
    by_category = {}
    for op in operations:
        if op['status'] == 'success':
            # Get category from operation dict (includes nested paths like "Images/working documents")
            category = op.get('category', 'unknown')
            
            if category not in by_category:
                by_category[category] = []
            
            # Extract just the filename
            filename = os.path.basename(op['source'])
            by_category[category].append(filename)
    
    # Display grouped by category
    for category in sorted(by_category.keys()):
        files = by_category[category]
        print(f"\n📁 {category.upper()}/  ({len(files)} file{'s' if len(files) != 1 else ''})")
        for filename in sorted(files):
            # Different symbol for move vs copy
            action_symbol = "⇒" if operation_type == "move" else "→"
            print(f"   {action_symbol} {filename}")
    
    # Show summary of what would happen
    total_files = sum(1 for op in operations if op['status'] == 'success')
    failed_files = sum(1 for op in operations if op['status'] != 'success')
    
    print("\n" + "=" * 80)
    print(f"Summary: {total_files} file{'s' if total_files != 1 else ''} would be {operation_type}d", end="")
    if failed_files > 0:
        print(f", {failed_files} would fail")
    else:
        print()
    print("=" * 80)

def write_operation_log(target_dir: str, operations: list, dry_run: bool,
                        operation_type: str, total_processed: int, total_failed: int) -> None:

    """Write operation details to a log file.

    The log file is always appended to (not overwritten), so previous logs are preserved.

    Args:
        target_dir (str): Target directory where log file will be written.
        operations (list): List of operation dictionaries with keys: action, source, destination, status.
        dry_run (bool): Whether this was a dry-run operation.
        operation_type (str): "move" or "copy".
        total_processed (int): Number of files successfully processed.
        total_failed (int): Number of files that failed.
    """
    try:
        log_path = os.path.join(target_dir, ORGANIZER_LOG_FILE)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(log_path, 'a', encoding='utf-8') as log_file:
            log_file.write(f"\n{'='*80}\n")
            log_file.write(f"Operation Log - {timestamp}\n")
            log_file.write(f"Mode: {'DRY-RUN' if dry_run else 'LIVE'} | Operation: {operation_type.upper()}\n")
            log_file.write(f"{'='*80}\n\n")
            
            for op in operations:
                status_symbol = "✓" if op['status'] == 'success' else "✗"
                log_file.write(f"[{status_symbol}] {op['action']}\n")
                log_file.write(f"    From: {op['source']}\n")
                log_file.write(f"    To:   {op['destination']}\n")
                if op['status'] != 'success':
                    log_file.write(f"    Error: {op.get('error', 'Unknown error')}\n")
                log_file.write("\n")
            
            log_file.write(f"{'='*80}\n")
            log_file.write(f"Summary:\n")
            log_file.write(f"  Total Processed: {total_processed}\n")
            log_file.write(f"  Total Failed:    {total_failed}\n")
            log_file.write(f"  Success Rate:    {total_processed}/{total_processed + total_failed}\n")
            log_file.write(f"{'='*80}\n\n")
        
        logging.info(f"Operation log written to: {log_path}")
    
    except Exception as e:
        logging.error(f"Failed to write operation log: {e}")


def organize_files_by_type(source_dir: str, target_dir: str, categories: dict, operation: str = "move", 
                          dry_run: bool = False) -> tuple:
    """Recursively scan source directory and organize files by category.
    
    Args:
        source_dir (str): Source directory path.
        target_dir (str): Target directory path.
        categories (dict): Mapping of category names to file extensions.
        operation (str): Either "move" or "copy". Determines file operation.
        dry_run (bool): If True, simulate the operation without modifying files.
    
    Returns:
        tuple: (files_processed_count, files_failed_count, operations_list)
    """
    files_processed = 0
    files_failed = 0
    operations = []
    operation = operation.lower()
    
    if operation not in {"copy", "move"}:
        raise ValueError("Invalid operation. Must be 'copy' or 'move'")
    
    try:
        normalized_target = os.path.abspath(target_dir)

        for root, dirs, files in os.walk(source_dir):
            # Prevent descending into target directory to avoid infinite recursion
            # or accidentally moving files into themselves during organization.
            dirs[:] = [
                d for d in dirs
                if os.path.commonpath([os.path.abspath(os.path.join(root, d)), normalized_target]) != normalized_target
            ]
            
            # Process each file in the current directory
            for filename in files:
                file_path = os.path.join(root, filename)
                
                try:
                    # Determine the category for this file
                    category = find_category_for_file(filename)
                    
                    # Determine target folder (don't create if dry-run)
                    target_folder = os.path.join(target_dir, category)
                    
                    if not dry_run:
                        os.makedirs(target_folder, exist_ok=True)
                    
                    # Get unique target path (handling duplicates)
                    target_file_path = handle_duplicate_filename(
                        target_folder,
                        filename,
                        check_existing=not dry_run
                    )
                    
                    # Perform the file operation (move or copy) or simulate it
                    if os.path.abspath(file_path) == os.path.abspath(target_file_path):
                        continue
                    
                    action = "Copy" if operation == "copy" else "Move"
                    
                    if dry_run:
                        logging.info(f"[DRY-RUN] {action} {filename} → {category}/")
                        operations.append({
                            'action': f"{action} (simulated)",
                            'source': file_path,
                            'destination': target_file_path,
                            'category': category,
                            'status': 'success'
                        })
                    else:
                        if operation == "copy":
                            shutil.copy2(file_path, target_file_path)
                        else:
                            shutil.move(file_path, target_file_path)
                        
                        logging.info(f"{action} {filename} → {category}/")
                        operations.append({
                            'action': action,
                            'source': file_path,
                            'destination': target_file_path,
                            'category': category,
                            'status': 'success'
                        })
                    
                    files_processed += 1
                    
                except PermissionError as error:
                    logging.warning(f"Permission denied {operation}ing {filename}: {error}")
                    operations.append({
                        'action': 'Move' if operation == 'move' else 'Copy',
                        'source': file_path,
                        'destination': target_folder,
                        'category': category,
                        'status': 'failed',
                        'error': f"Permission denied: {error}"
                    })
                    files_failed += 1
                except OSError as error:
                    logging.warning(f"File system error {operation}ing {filename}: {error}")
                    operations.append({
                        'action': 'Move' if operation == 'move' else 'Copy',
                        'source': file_path,
                        'destination': target_folder,
                        'category': category,
                        'status': 'failed',
                        'error': f"File system error: {error}"
                    })
                    files_failed += 1
                except Exception as error:
                    logging.error(f"Error {operation}ing {filename}: {error}")
                    operations.append({
                        'action': 'Move' if operation == 'move' else 'Copy',
                        'source': file_path,
                        'destination': target_folder,
                        'category': category,
                        'status': 'failed',
                        'error': str(error)
                    })
                    files_failed += 1
    
    except Exception as error:
        logging.error(f"Critical error during organization: {error}")
        return files_processed, files_failed, operations
    
    return files_processed, files_failed, operations

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
        
        # Normalize paths and check if source and target are the same
        normalized_source = os.path.abspath(source_dir)
        normalized_target = os.path.abspath(target_dir)
        
        if normalized_source == normalized_target:
            print("\n⚠️  Warning: Source and target directories are the same!")
            confirm = input("Do you want to organize files within this directory? (y/n): ").lower()
            if confirm != 'y':
                print("Operation cancelled.")
                return 0
        
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
        
        # Ask about dry-run mode (Phase 2A)
        print("\nChoose mode:")
        print("1. Live mode (actually organize files)")
        print("2. Dry-run mode (preview changes without modifying files)")
        mode_choice = input("Enter your choice (1 or 2): ").strip()
        dry_run = mode_choice == "2"
        
        if dry_run:
            print("Selected: Dry-run mode (no files will be modified)")
        else:
            print("Selected: Live mode")
        
        # Ask about empty folder handling
        print("\nChoose empty folder handling:")
        print("1. Create category folders even if unused (don't remove empty folders)")
        print("2. Only create folders for files to be organized (remove empty folders after)")
        cleanup_choice = input("Enter your choice (1 or 2): ").strip()
        cleanup_empty = cleanup_choice == "2"
        
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
        
        # Show a preview if dry-run
        if dry_run:
            print("\n⚠️  DRY-RUN MODE: No files will be modified.")
            print("    Changes will be logged but not applied.\n")
        
        # Organize files
        print("Organizing files...")
        files_processed, files_failed, operations = organize_files_by_type(
            source_dir, target_dir, FILE_CATEGORIES, operation, dry_run
        )
        
        # Write operation log (Phase 2E) - Only for live operations
        if not dry_run:
            write_operation_log(target_dir, operations, dry_run, operation, 
                              files_processed, files_failed)
            
            # Clean up empty folders if requested
            if cleanup_empty and files_processed > 0:
                print("Removing empty directories...")
                removed = remove_empty_directories(target_dir, preserve_root=True)
                if removed > 0:
                    print(f"Removed {removed} empty directories.")
        else:
            # Display preview for dry-run
            display_preview(operations, operation)
        
        # Display summary
        print("\n" + "=" * 50)
        if dry_run:
            print("✅ DRY-RUN PREVIEW COMPLETE")
            print(f"Files would be {operation}d: {files_processed}")
            if files_failed > 0:
                print(f"Files would fail: {files_failed}")
            print("=" * 50)
            print("\n💡 This was a preview only - no files were modified.")
            print("\nTo actually organize these files, run the program again and select:")
            print(f"  Operation: {operation.capitalize()}")
            print("  Mode: Live mode (option 1)")
            
            # Ask if user wants to save a log file for this dry-run
            save_log = input("\nWould you like to save a log file for this dry-run? (y/n): ").lower()
            if save_log == 'y':
                write_operation_log(target_dir, operations, dry_run, operation,
                                  files_processed, files_failed)
                print("✓ Dry-run log file saved.")
            
            print("\n" + "=" * 50)
            input("Press Enter to exit the program...")
        else:
            print(f"✅ File organization complete!")
            print(f"Files {operation}d: {files_processed}")
            if files_failed > 0:
                print(f"Files failed: {files_failed}")
            print("=" * 50)
            print(f"\n📋 Operation log saved to: {os.path.join(target_dir, ORGANIZER_LOG_FILE)}")
        
        return 0
        
    except Exception as error:
        print(f"\nAn error occurred: {error}")
        return 1


if __name__ == "__main__":
    exit(main())
