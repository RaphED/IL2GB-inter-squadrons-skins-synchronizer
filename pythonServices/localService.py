import os
import hashlib
import shutil
import json

from pythonServices.configurationService import getConf

def getSkinDirectory():
    return os.path.join(getConf("IL2GBGameDirectory"), "data\\graphics\\skins")

def getCustomPhotosDirectory():
    return os.path.join(getConf("IL2GBGameDirectory"), "data\\graphics\\planes")

def getSkinsList():

    skinList = []
    skinsDirectory = getSkinDirectory()
    
    for root, dirs, files in os.walk(skinsDirectory):
        
        #continue if no files
        if len(files) == 0:
            continue

        #get only dds files
        ddsfiles = [f for f in files if f.lower().endswith('.dds')]

        if len(ddsfiles) == 0:
            continue

        parentDir = os.path.dirname(root)
        
        #only manage 1 level skins (otherwise i suspect badly placed sinks)
        if parentDir != skinsDirectory:
            print(f"Unexpected skin(s) {ddsfiles} placement at {root}. Not managed")
            continue
        
        aircraft =  os.path.basename(os.path.normpath(root))

        #parse only main skin files
        for ddsFileName in [file for file in ddsfiles if not file.endswith("#1.dds")]:
            fileFullPath = os.path.join(root,ddsFileName)
            filestats = os.stat(fileFullPath)

            skinList.append({
                "aircraft": aircraft,
                "name": ddsFileName[:-4], #remove extention to get the name
                "mainFileName": ddsFileName,
                "mainFileSize": filestats.st_size,
                "mainFileMd5": hashlib.md5(open(fileFullPath, "rb").read()).hexdigest()
            })

        #then if there are secondary files, attack them
        for ddsSecondaryFileName in [file for file in ddsfiles if file.endswith("#1.dds")]:
            fileFullPath = os.path.join(root,ddsSecondaryFileName)
            filestats = os.stat(fileFullPath)

            for index, skin in enumerate(skinList):
                if skin["mainFileName"][:-4] == ddsSecondaryFileName[:-6]:
                    skinList[index]["secondaryFileName"] = ddsSecondaryFileName
                    skinList[index]["secondaryFileSize"] = filestats.st_size
                    skinList[index]["secondaryFileMd5"] = hashlib.md5(open(fileFullPath, "rb").read()).hexdigest()
                    break
                    #TODO: manage the case of an orphan secondary file
    
    return skinList

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

def moveSkinFromPathToDestination(src_path, aircraft):
    return moveFile(src_path, os.path.join(getSkinDirectory(), aircraft))

def removeSkin(localSkinInfo):
    filePath = os.path.join(getSkinDirectory(), localSkinInfo["aircraft"], localSkinInfo["mainFileName"])
    os.remove(filePath)

    if localSkinInfo.get("secondaryFileName") is not None and  localSkinInfo["secondaryFileName"] != "":
        #there is a secondary file
        secondaryFilePath = os.path.join(getSkinDirectory(), localSkinInfo["aircraft"], localSkinInfo["secondaryFileName"])
        os.remove(secondaryFilePath)

def getSpaceUsageOfLocalSkinCatalog(skinList):
    totalDiskSpace = 0
    for skin in skinList:
        totalDiskSpace += int(skin["mainFileSize"])
        
        secondaryFileSpace = skin.get("secondaryFileSize")
        if secondaryFileSpace is not None and secondaryFileSpace != "":
            totalDiskSpace += int(secondaryFileSpace)
    
    return totalDiskSpace



def getCustomPhotosList():
    return getCustomPhotosListFromPath(getCustomPhotosDirectory())

def getCustomPhotosListFromPath(path):
    notesList = []
    
    for root, dirs, files in os.walk(path):
        
        #continue if no files
        if len(files) == 0:
            continue

        #get only custom photos files
        customPhotosfiles = [f for f in files if f == 'custom_photo.dds']

        if len(customPhotosfiles) != 1:
            continue
        currentPhotoFile = customPhotosfiles[0]

        #parent dir should be "textures"
        if os.path.basename(os.path.normpath(root)) != "Textures":
            print(f"Found unexpected custom photo at {root}")
            continue

        aircraft =  os.path.basename(os.path.normpath(os.path.dirname(root)))

        notesList.append({
            "aircraft": aircraft,
            "md5": hashlib.md5(open(os.path.join(root,currentPhotoFile), "rb").read()).hexdigest()
        })
        
    return notesList

def getAndGenerateCustomPhotosCatalogFromPath(parentPath, catalogName):
    catalogPath = os.path.join(parentPath, catalogName)
    cockpitNotesList = getCustomPhotosListFromPath(catalogPath)
    generateCockpitNotesCatalogFileName = f"{catalogName}CustomPhotosManifest.json"
    fullFilePath = os.path.join(parentPath, generateCockpitNotesCatalogFileName)
    with open(fullFilePath, 'w') as f:
        json.dump(cockpitNotesList, f, indent=4)

    return cockpitNotesList

def moveCustomPhotoFromPathToDestination(src_path, aircraft):
    destinationPath = os.path.join(getCustomPhotosDirectory(), aircraft, "Textures")
    return moveFile(src_path, destinationPath)