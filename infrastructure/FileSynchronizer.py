import os
import shutil

# This class synchronizes files in between directories.
class FileSynchronizer:

    # Removes files in a directory.
    def removeFilesInDirectory(self, destination_directory: str) -> None:
        for file in os.listdir(destination_directory):
            filepath = os.path.join(destination_directory, file)
            os.remove(filepath)

    # Removes a directory and all the files within it.
    def removeDirectory(self, destination_directory: str) -> None:
        for file in os.listdir(destination_directory):
            filepath = os.path.join(destination_directory, file)
            os.remove(filepath)
        os.rmdir(destination_directory)

    # Copies files from one directory to another.
    def copyFilesFromDirectory(self, source_directory: str, destination_directory: str) -> None:
        for file in os.listdir(source_directory):
            print(file)
            source_file_path = os.path.join(source_directory, file)
            destination_file_path = os.path.join(destination_directory, file)
            shutil.copyfile(source_file_path, destination_file_path)