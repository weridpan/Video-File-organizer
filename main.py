#imports and general setup
import os # creates folders and checks if they are empty
import shutil #moves files and more
import datetime as datetime

#ask user for Source and Target folder
source_dir = input("Please enter source directory")
Target_dir = input("Please enter target directory")
#Check if folders are empty
empty = True
for _ in os.scandir(Target_dir):
    empty = False
    break

if empty:
    print("Empty directory")
else:
    print("Not empty directory")
#categorize file extensions
file_ext = {
    "Images": [".jpg",".jpeg",".png", ".gif", ".webp", ".bmp", ".tiff"],
    "Videos": [".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".mpeg"],
    "Audio": [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"],
    "Scripts": [".pdf", ".docx", ".txt", ".xlsx", ".pptx", ".odt", ".rtf"],
    "Archives": [".zip", ".rar", ".tar", ".gz", ".7z", ".iso"],
    "Project files": [".psd", ".ai", ".indd", ".sketch", ".xd", ".fig", ".prproj", ".aep"],
    "subtitles": [".srt", ".sub", ".vtt", ".csv", ".tsv"],
    "other": []
}
#create empty folders
def create_folders(target_dir, folders):
    for folder in folders:
        folder_path = os.path.join(base_dir, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

def organize_files_by_type(target_dir, file_ext):
    )        

