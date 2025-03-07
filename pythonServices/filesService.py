import os
import sys
import shutil
import uuid
import requests
import hashlib
import logging

temporaryFolder = "temp"

def getTempFolderFullPath():
    return os.path.join(os.curdir, temporaryFolder)

def temporaryFolderExists():
    return os.path.exists(getTempFolderFullPath())

def cleanTemporaryFolder():
    if temporaryFolderExists():
        for root, dirs, files in os.walk(getTempFolderFullPath()):
            for f in files:
                filePath = os.path.join(root, f)
                try:
                    os.unlink(filePath)
                except:
                    logging.warning(f"Cannot clean temporary file {filePath}")
            for d in dirs:
                dirPath = os.path.join(root, d)
                try:
                    shutil.rmtree(dirPath)
                except:
                    logging.warning(f"Cannot clean temporary directory {dirPath}")
                

# Function to download a file from a URL and save it to a temporary directory
def downloadFile(url, expectedMD5 = None, prefix_with_uuid=False, destination_file_name=None):
    
    tempDir = getTempFolderFullPath()
    #create the temp directory if not exist
    if not os.path.exists(tempDir):
        os.makedirs(tempDir)
    
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Raise an exception for HTTP errors
    
    file_name = os.path.basename(url)
    #forced destination file name
    if destination_file_name is not None:
        file_name = destination_file_name

    if prefix_with_uuid:
        file_name = str(uuid.uuid4()) + "_" + file_name
    temp_file_path = os.path.join(tempDir, file_name)

    with open(temp_file_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):#TODO : check the chunk size is a good one
            f.write(chunk)
    
    if expectedMD5 is not None and hashlib.md5(open(temp_file_path, "rb").read()).hexdigest() != expectedMD5:
        #TODO, retry
        raise Exception(f"Bad file download {temp_file_path}")
    
    logging.info(f"File Downloaded : {temp_file_path}")
    return temp_file_path


# Function to move the file and replace if necessary
def moveFile(src_path, dest_dir):
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    dest_path = os.path.join(dest_dir, os.path.basename(src_path))
    
    # Remove the destination file if it exists
    if os.path.exists(dest_path):
        os.remove(dest_path)

    # Move the file
    shutil.move(src_path, dest_path)
    return dest_path

def copyFile(srcFilePath, destFilePath):
    if not os.path.exists(srcFilePath):
        raise Exception(f"Cannot copy unfindable file at {srcFilePath}")
    shutil.copy(srcFilePath, destFilePath)

def deleteFile(filePath):
    if os.path.exists(filePath):
        os.remove(filePath)
    else:
        logging.error(f"Cannot delete unfindable file {filePath}" )

#access to ressources 
def getRessourcePath(relativePath):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.curdir))
    return os.path.join(base_path, "Ressources", relativePath)

def getIconPath(iconfileName):
    return getRessourcePath(f"icons\\{iconfileName}")