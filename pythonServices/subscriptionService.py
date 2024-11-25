import os
import json
import re

from pythonServices.remoteService import getSourceInfo 

subscriptionPath = os.path.join(os.getcwd(),"Subscriptions")

class SubscribedCollection:
    def __init__(self, subcriptionName, source, criteria):
        
        self.subcriptionName = subcriptionName
        #default source is HSD
        sourceName = "HSD"
        if source is not None:
            sourceName = source
        self.source = getSourceInfo(sourceName)["source"]
        
        self.criteria: dict[str,str]= criteria
        

    def match(self, remoteSkinInfo):
        for criterion in self.criteria.keys():
            #transform * in .*
            matchingRegExp =self.criteria[criterion].replace("*", ".*") 
            if not re.match(matchingRegExp,remoteSkinInfo[criterion]):
                return False
        return True
    
    def toString(self):
        return f"{self.subcriptionName} - source is {self.source} - {self.criteria}" 

def getSubscribedCollectionFromFile(subscriptionFilePath):
    file = open(subscriptionFilePath, "r")
    rawJsonData: list = json.load(file)

    subscribedCollectionlist = []
    #raw data should be a list
    for rawSubscription in rawJsonData:
        subscribedCollectionlist.append(
            SubscribedCollection(
                subcriptionName=os.path.basename(subscriptionFilePath).replace(".iss", ""),
                source=rawSubscription.get("source"),
                criteria=rawSubscription["criteria"]
            )
        )
    
    return subscribedCollectionlist

def getAllSubscribedCollection() -> list[SubscribedCollection]:

    returnedCollections = []
    #create subsciption path of not exists
    if not os.path.exists(subscriptionPath):
        os.makedirs(subscriptionPath)
    
    for root, dirs, files in os.walk(subscriptionPath):
        for file in files:
            if file.endswith(".iss"): #We only consider files with iss extension
                returnedCollections += getSubscribedCollectionFromFile(os.path.join(root,file))
    
    return returnedCollections

def isSubcriptionFolderEmpty():
    for root, dirs, files in os.walk(subscriptionPath):
        for file in files:
            if file.endswith(".iss"): #We only consider files with iss extension
                return False
    
    return True