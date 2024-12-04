import sys
import ISSsynchronizer
import pythonServices.configurationService as configurationService
from pythonServices.subscriptionService import isSubcriptionFolderEmpty
from pythonServices.filesService import cleanTemporaryFolder
from pythonServices.messageBrocker import MessageBrocker

import pythonServices.loggingService
import logging
from versionManager import isCurrentVersionUpToDate
import ISSupdater
import ISSScanner
import tk_async_execute as tae

from GUI.mainGUI import mainGUI


def runMainConsole():
    try:
        performPreScanChecks()

        print("**********************************************")
        print("**************** SYNC STARTED ****************")
        print("**********************************************\n")

        print("\tSTEP 1/2 - SCAN\n")
        if isSubcriptionFolderEmpty():
            printWarning("There are no subscriptions.\nPlease import or activate .iss file(s) to subscribe to any skins collection")
        printWarning("Skins scan launched. Please wait...")
        scanResult = ISSScanner.scanAll()
        print(scanResult.toString())

        #then as the user for the update if any
        print("\tSTEP 2/2 - SYNC\n")
        if scanResult.IsSyncUpToDate():
            printSuccess("All skins are up to date.")
        else:
            while True:
                deletionMode = input("Do you want to perform the update ? yes (y) or no (n) ? ").lower()
                if deletionMode == "y":
                    printWarning("UPDATE STARTED...")
                    ISSsynchronizer.updateAll(scanResult)
                    printSuccess("UPDATE DONE")
                    break
                elif deletionMode == "n":
                    printWarning("NO UPDATE PERFORMED")
                    break
                else:
                    printError("unexpected anwser")

    except Exception as e:
        printError(e)

    print("**********************************************")
    print("***************** SYNC ENDED *****************")
    print("**********************************************")

    input("Press any key...")

def performAtProgramLauchChecks():

    #make sure the temporary folder is clean ->x do not o that due to update !
    cleanTemporaryFolder()

     #check conf file is generated
    if not configurationService.configurationFileExists():
        printError("No configuration file found")
        #and help the user to generate a new one
        generateConfFileWithConsole()


def performPreScanChecks():

    #check the game directory is properly parametered
    if not configurationService.checkConfParamIsValid("IL2GBGameDirectory"):
        raise Exception(
            f"Bad IL2 Game directory, current game path is set to : {configurationService.getConf("IL2GBGameDirectory")}\n"
            f"Directory must be the main game directory, generally named 'IL-2 Sturmovik Battle of Stalingrad' and containing two folders 'bin' and 'data'\n"
            f"Change value in the GUI 'Parameters' section"
        )
    
def generateConfFileWithConsole():
    printWarning("A new Configuration file is about to be generated")
    #at first create a conf file with default params
    newConf = configurationService.generateConfFile()

    
    printWarning("Please wait while trying to find IL2 directory on your HDDs...")
    foundIL2Path = configurationService.tryToFindIL2Path()
    #foundIL2Path = None
    if foundIL2Path is None:
        printError("Cannot find IL2 path")
        while True:
            manualPath = input("Please provide manually the path of your IL2 install directory : ")
            if configurationService.checkIL2InstallPath(manualPath):
                printSuccess("IL2 path found")
                foundIL2Path = manualPath
                break
            else:
                printError("Cannot identiry that directory as the main IL2 path")
                print("Please try again")
    else:
        printSuccess("IL2 path found")
    
    configurationService.update_config_param("IL2GBGameDirectory", foundIL2Path)

    print("ISS provides two modes :\n - (a) keep all downloaded skins\n - (b) remove all skins and keep only the ones you are subscripted to.")
    
    while True:
        deletionMode = input("What mode do you want ? (a) or (b) ? ").lower()
        if deletionMode == "a":
            configurationService.update_config_param("autoRemoveUnregisteredSkins", False)
            break
        elif deletionMode == "b":
            configurationService.update_config_param("autoRemoveUnregisteredSkins", True)
            break
        else:
            printError("Unknown anwser. Please anwser a or b")

    printSuccess("Configuration initialized with success")
    
def printError(text):
    print("\033[91m{}\033[00m".format(text))

def printWarning(text):
    print("\033[93m{}\033[00m".format(text))

def printSuccess(text):
    print("\033[92m{}\033[00m".format(text))

######### MAIN ###############
if __name__ == "__main__":

    force_update = False
    updater_mode = False
    update_withPrerelease = False
    console_mode = False #TODO : Not implemented yet
    debug_mode = False #TODO : Not implemented yet

    for arg in sys.argv[1:]:
        if arg == '-updater':
            updater_mode = True
        elif arg == '-force-update':
            force_update = True
        elif arg == '-prerelease':
            update_withPrerelease = True
        elif arg == '-console':
            console_mode = True
        elif arg == '-debug':
            debug_mode = True
    
    #Check if an update has to be launched
    if not isCurrentVersionUpToDate(prerelease = update_withPrerelease) or force_update:
        printError("A new version of ISS has been found")
        printWarning("Please wait for the update and the automatic restart...")
        ISSupdater.downloadAndRunUpdater(prerelease = update_withPrerelease)
        sys.exit()
    
    
    if updater_mode:
        ISSupdater.replaceAndLaunchMainExe(prerelease = update_withPrerelease)
        sys.exit()

    performAtProgramLauchChecks()
    
    if console_mode:
        #CONSOLE RUN
        
        #register the console to the message brocker
        MessageBrocker.registerConsoleHook(print)
        runMainConsole()
        sys.exit()

    else:
        #NORMAL GUI RUN
        tae.start()

        mainUI = mainGUI()
        mainUI.run()
        tae.stop()
    