import os
import json
import re
import logging
import shutil

from pythonServices.remoteService import getSourceInfo, RemoteSkin
from pythonServices.filesService import downloadFile

subscriptionPath = os.path.join(os.getcwd(),"Subscriptions")

class SubscribedCollection:
    def __init__(self, subcriptionName: str, source: str, criteria: dict[str,str] = None, proxy_chain: list[str] = []):
        
        self.subcriptionName = subcriptionName
        #default source is HSD
        sourceName = "HSD"
        if source is not None:
            sourceName = source
        self.source = getSourceInfo(sourceName)["source"]
        
        if criteria == None:
            self.criteria = dict[str,str]()
        else:    
            self.criteria = criteria

        self.proxy_chain = proxy_chain
        

    def match(self, remoteSkinInfo: RemoteSkin, applyCensorship = False) -> bool:
        
        #cannot take a skin if we want to apply censorship and there is not uncensored version
        if applyCensorship and not remoteSkinInfo.hasAnCensoredVersion():
            return False
        
        for criterion in self.criteria.keys():
            if remoteSkinInfo.infos.get(criterion) is None:
                logging.warning(f"Unexpected criteron '{criterion}' for skin source '{remoteSkinInfo.source}' and collection '{self.subcriptionName}'")
                return False
            #transform * in .*
            matchingRegExp =self.criteria[criterion].replace("*", ".*")
            #match is not key sensitive
            if not re.match(matchingRegExp.lower(),remoteSkinInfo.infos[criterion].lower()):
                return False
        return True
    
    def toString(self):
        return f"{self.subcriptionName} - source is {self.source} - {self.criteria}" 

def getSubscribedCollectionFromFilePath(subscriptionFilePath, proxy_chain: list[str] = []):
    
    subscribedCollectionlist: list[SubscribedCollection] = []
    try:
        file = open(subscriptionFilePath, "r")
        rawJsonData = json.load(file)

        #raw data should be a list
        for rawSubscription in rawJsonData:
            proxyFile = rawSubscription.get("ProxyISS")
            if proxyFile is None:   #OPTION 1 : this is a normal collection
                subscribedCollectionlist.append(
                    SubscribedCollection(
                        subcriptionName=os.path.basename(subscriptionFilePath).replace(".iss", "").replace(".disabled", ""),
                        source=rawSubscription.get("source"),
                        criteria=rawSubscription["criteria"],
                        proxy_chain=proxy_chain
                    )
                )
            else:   #OPTION 2 : this is a link to remote iss file
                downloadedFile = downloadFile(proxyFile, prefix_with_uuid=True)
                new_proxy_chain = proxy_chain[:] #make a copy to avoid reference
                new_proxy_chain.append(proxyFile)
                subscribedCollectionlist += getSubscribedCollectionFromFilePath(subscriptionFilePath=downloadedFile, proxy_chain=new_proxy_chain)

        
        return subscribedCollectionlist
                
    except Exception as e:
        logging.error(f"Error at loading subscription file {subscriptionFilePath}. Error detail : {e}")
        return []
        
def getAllSubscribedCollection() -> list[SubscribedCollection]:

    returnedCollections = []
    subscriptionDictionary = getAllSubscribedCollectionByFileName()
    for fileName in subscriptionDictionary.keys():
        returnedCollections += subscriptionDictionary[fileName]
        
    return returnedCollections

def createSubcriptionFolderIsNotExist():
    if not os.path.exists(subscriptionPath):
        os.makedirs(subscriptionPath)

def getAllSubscribedCollectionByFileName(getDisabledFiles = False) -> dict[str, list[SubscribedCollection]]:
    returnedCollections = dict[str, list[SubscribedCollection]]()
    #create subsciption path of not exists
    createSubcriptionFolderIsNotExist()
    
    for root, dirs, files in os.walk(subscriptionPath):
        for file in files:
            if file.endswith(".iss"): #We only consider files with iss extension
                returnedCollections[file] = getSubscribedCollectionFromFilePath(os.path.join(root,file))
            if getDisabledFiles and file.endswith(".iss.disabled"):
                returnedCollections[file] = getSubscribedCollectionFromFilePath(os.path.join(root,file))
    
    return returnedCollections

def getSubcriptionNameFromFileName(fileNameWithExtension):
    if fileNameWithExtension.endswith(".iss"):
        return fileNameWithExtension[:-4]
    elif fileNameWithExtension.endswith(".iss.disabled"):
        return fileNameWithExtension[:-13]
    else:
        raise Exception(f"Unexpected subscription file name {fileNameWithExtension}")
    
def getSubcriptionFilePathFromFileName(fileNameWithExtension):
    return os.path.join(subscriptionPath, fileNameWithExtension)

def activateSubscription(fileNameWithExtension):
    filePath = getSubcriptionFilePathFromFileName(fileNameWithExtension)
    if not os.path.exists(filePath) or not fileNameWithExtension.endswith(".iss.disabled"):
        raise Exception(f"Unexpected subscription to activate {fileNameWithExtension}")
    else:
        newFileName = fileNameWithExtension[:-9]
        newFilePath = os.path.join(subscriptionPath, newFileName)
        os.rename(filePath,newFilePath)
        return newFileName

def desactivateSubscription(fileNameWithExtension):
    filePath = getSubcriptionFilePathFromFileName(fileNameWithExtension)
    if not os.path.exists(filePath) or not fileNameWithExtension.endswith(".iss"):
        raise Exception(f"Unexpected subscription to activate {fileNameWithExtension}")
    else:
        newFileName = fileNameWithExtension + ".disabled"
        newFilePath = os.path.join(subscriptionPath, newFileName)
        os.rename(filePath,newFilePath)
        return newFileName

def deleteSubscriptionFile(fileNameWithExtension):
    filePath = getSubcriptionFilePathFromFileName(fileNameWithExtension)
    if not os.path.exists(filePath):
        raise Exception(f"Unexpected subscription to delete {fileNameWithExtension}")
    else:
        os.remove(filePath)

def importSubcriptionFile(file_path):
    # Copy the selected file to the 'Subscriptions' folder
    file_name = os.path.basename(file_path)  # Extract the file name
    destination_path = os.path.join(subscriptionPath, file_name)
    if os.path.exists(destination_path):
        raise Exception("You already have an iss file with the same name")
    shutil.copy(file_path, destination_path)
    return destination_path

def saveSubscriptionFile(fileNameWithExtension, subscribedCollections: list[SubscribedCollection]):
    
    json_content = []
    for collection in subscribedCollections:
        entry = {"source": "HSD", "criteria": {}}
        for criterion in collection.criteria.keys():
            entry["criteria"][criterion] = collection.criteria[criterion]
        json_content.append(entry)
    
    createSubcriptionFolderIsNotExist()

    filePath = os.path.join(subscriptionPath, fileNameWithExtension)
    with open(filePath, "w") as json_file:
            json_file.write(json.dumps(json_content))