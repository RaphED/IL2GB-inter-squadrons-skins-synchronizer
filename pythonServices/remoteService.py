import requests
import re
import os
import logging

from pythonServices.configurationService import getConf
from pythonServices.filesService import downloadFile


sourcesInfo = [
    {
        "source":"HSD",
        "catalogURL": "https://skins.combatbox.net/Info.txt",
        "skinsURL": "https://skins.combatbox.net/[aircraft]/[skinFileName]",
        "params":{
            "censored":{
                "aircraft": "Plane",
                "name": "Title",
                "mainSkinFileName": "Skin0",
                "mainFileMd5": "HashDDS0",
                "mainFileSize":"Filesize0",
                "secondarySkinFileName": "Skin01",
                "secondaryFileMd5": "HashDDS01",
                "secondaryFileSize":"Filesize01"
            },
            "uncensored":{
                "aircraft": "Plane",
                "name": "Title",
                "mainSkinFileName": "Skin1",
                "mainFileMd5": "HashDDS1",
                "mainFileSize":"Filesize1",
                "secondarySkinFileName": "Skin11",
                "secondaryFileMd5": "HashDDS11",
                "secondaryFileSize":"Filesize11"
            }
        }
    }
]

def getSourceInfo(source):
    for sourceIter in sourcesInfo:
        if sourceIter["source"] == source:
            return sourceIter
    raise Exception(f"Caanot find source {source}!")

def getSourceParam(source, param, censored):
    if censored:
        return getSourceInfo(source)["params"]["censored"][param]
    else:
        return getSourceInfo(source)["params"]["uncensored"][param]
    

class RemoteSkin:
    def __init__(self, source) -> None:
        self.source = source
        self.infos = dict()

    def addRawData(self, key, value) -> None:
        self.infos[key] = value

    def getValue(self, param: str):
        applyCensorship = getConf("applyCensorship")

        if applyCensorship:
            return self.infos.get(getSourceParam(self.source, param, censored=True))
        else:
            #take the uncensored value, and if value is None or "", then take censored
            uncensored_value = self.infos.get(getSourceParam(self.source, param, censored=False))
            if uncensored_value is not None and uncensored_value != "":
                return uncensored_value
            else:
                return self.infos.get(getSourceParam(self.source, param, censored=True))

    def hasAnCensoredVersion(self) -> bool:
        #we consider the first dds file
        firstUncensoredValue =  self.infos.get(getSourceParam(source=self.source, param="mainSkinFileName", censored=True))
        return firstUncensoredValue is not None and firstUncensoredValue != ""

_cached_skins_from_source = dict[str, list[RemoteSkin]]()

def getSkinsCatalogFromSource(source) -> list[RemoteSkin]:
    global _cached_skins_from_source # TODO Add timer and reset if user keeps the app open for long time ?
    if source in _cached_skins_from_source:
        return _cached_skins_from_source[source]    
    
    # Download the content of the file
    sourceInfo = getSourceInfo(source)
    if sourcesInfo is None: 
        raise Exception("Unexpected source")
    response = requests.get(sourceInfo["catalogURL"])

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        file_content = response.text
        
        # Dictionary to store the skins
        skins = {}

        # Use regular expression to split the content into skin sections
        sections = re.split(r'\[Skin-\d+\]', file_content)[1:]  # Ignore the part before the first skin

        # For each section after the header
        for i, section in enumerate(sections):
            # Clean up the section
            section = section.strip()
            if not section:
                continue

            skin_id = i

            # Dictionary to store the skin information
            remoteSkin = RemoteSkin(source)

            # Loop through each line of the section
            for line in section.splitlines():
                # Ignore empty lines or comment lines (lines starting with #)
                if line.strip() and not line.startswith("#"):
                    try:
                        key, value = line.split('=', 1)  # Split at the first '='
                        remoteSkin.addRawData(key=key.strip(), value=value.strip())# Store the key-value pair
                    except ValueError:
                        logging.error(f"Formatting error on line: {line}")

            # Add the skin information to the main dictionary
            skins[skin_id] = remoteSkin

        # return only the values (we do not need skins ids)
        _cached_skins_from_source[source]=skins.values()
        return skins.values()

    else:
        raise Exception(f"Error downloading the file. Status code: {response.status_code}")

def getSpaceUsageOfRemoteSkinCatalog(source, remoteSkinList: list[RemoteSkin]):
    totalDiskSpace = 0
    for skin in remoteSkinList:
        primaryFileSpace = skin.getValue("mainFileSize")
        if primaryFileSpace is not None and primaryFileSpace != "":
            totalDiskSpace += int(primaryFileSpace)
        
        secondaryFileSpace = skin.getValue("secondaryFileSize")
        if secondaryFileSpace is not None and secondaryFileSpace != "":
            totalDiskSpace += int(secondaryFileSpace)
    
    return totalDiskSpace

def downloadSkinToTempDir(source, skinInfo: RemoteSkin):

    #build skin URL
    url = getSourceInfo(source)["skinsURL"]
    url = url.replace("[aircraft]", skinInfo.getValue("aircraft"))
    urlMainSkin = url.replace("[skinFileName]", skinInfo.getValue("mainSkinFileName"))

    # Download the file(s) to the temporary folder
    downloadedFiles = []
    downloadedFiles.append(downloadFile(url=urlMainSkin, expectedMD5=skinInfo.getValue("mainFileMd5")))
    
    #if there is a second skin file
    secondarySkinFileName = skinInfo.getValue("secondarySkinFileName")
    if secondarySkinFileName is not None and secondarySkinFileName != "":
        #hack : works only for HSD, the #1 is replaced by %123 on the URL
        remoteFileName = skinInfo.getValue("secondarySkinFileName").replace("#1", "%231")
        urlSecondarySkin = url.replace("[skinFileName]", remoteFileName)
        downloadFileName = downloadFile(url=urlSecondarySkin, expectedMD5=skinInfo.getValue("secondaryFileMd5"))
        properFileName = downloadFileName.replace("%231","#1")
        os.rename(downloadFileName, properFileName)
        downloadedFiles.append(properFileName)
    
    return downloadedFiles


customPhotosCatalogURL = "https://www.lesirreductibles.com/irreskins/IRRE/CustomPhotos/[mode]CustomPhotosManifest.json"
customPhotosFilesURL = "https://www.lesirreductibles.com/irreskins/IRRE/CustomPhotos/[mode]/[aircraft]/Textures/custom_photo.dds"


def getCockpitNotesModeInfo(mode):
    match mode:
        case "noSync":
            return {
                "catalogURL": None,
                "filesURL": None
            }
        case "originalPhotos" | "officialNumbers" | "technochatNumbers":
            return {
                "catalogURL": customPhotosCatalogURL.replace("[mode]", mode),
                "filesURL": customPhotosFilesURL.replace("[mode]", mode),
            }
        case _:
            raise Exception(f"Unexpected cockpitNotesModes {mode}")

def getCustomPhotosList():
    #hard coded remote address for the cockpitNotesCatalog
    catalogURL = getCockpitNotesModeInfo(getConf("cockpitNotesMode"))["catalogURL"]
    if catalogURL is None:
        return []

    response = requests.get(catalogURL)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        file_content = response.json()
        return file_content
    return []

def getSpaceUsageOfCustomPhotoCatalog(customPhotosList):
    totalDiskSpace = 0
    for skin in customPhotosList:
        #This is soooo bad. custom photos are about 1 400 000 bites
        #TODO : addd the file size in the manifests
        totalDiskSpace += 1400000
    
    return totalDiskSpace

def downloadCustomPhoto(cockpitNotesMode, cockpitNote):
    filesURL = getCockpitNotesModeInfo(cockpitNotesMode)["filesURL"]

    targetURL = filesURL.replace("[aircraft]", cockpitNote["aircraft"])
    return downloadFile(targetURL, cockpitNote["md5"])