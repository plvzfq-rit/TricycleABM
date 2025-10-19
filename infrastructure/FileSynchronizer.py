import os
import shutil
class FileSynchronizer:
    def removeFilesInDirectory(self, destination_directory: str) -> None:
        for file in os.listdir(destination_directory):
            filepath = os.path.join(destination_directory, file)
            os.remove(filepath)

    def copyFilesFromDirectory(self, source_directory: str, destination_directory: str) -> None:
        for file in os.listdir(source_directory):
            source_file_path = os.path.join(source_directory, file)
            destination_file_path = os.path.join(destination_directory, file)
            shutil.copyfile(source_file_path, destination_file_path)