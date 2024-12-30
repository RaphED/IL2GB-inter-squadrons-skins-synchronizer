import sys

import logging
from versionManager import isCurrentVersionUpToDate
import ISSupdater
import tk_async_execute as tae

from GUI.mainGUI import runMainGUI
from GUI.updaterGUI import runUpdaterGUI
from GUI.crashGUI import runCrashGUI

######### MAIN ###############
if __name__ == "__main__":

    force_update = False
    updater_mode = False
    update_withPrerelease = False
    debug_mode = False

    for arg in sys.argv[1:]:
        if arg == '-updater':
            updater_mode = True
        elif arg == '-force-update':
            force_update = True
        elif arg == '-prerelease':
            update_withPrerelease = True
        elif arg == '-debug':
            debug_mode = True
    
    #INITIALISE LOGS
    logLevel = logging.DEBUG
    if not debug_mode:
        logLevel = logging.INFO
 
    logging.basicConfig(
        filename='iss.log',       # Le fichier de log où les messages seront enregistrés
        level= logLevel,          # Le niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format='%(asctime)s - %(levelname)s - %(message)s',  # Format du message
        datefmt='%Y-%m-%d %H:%M:%S'    # Format de la date
    )
    
    try:
        #Check if an update has to be launched
        if not isCurrentVersionUpToDate(prerelease = update_withPrerelease) or force_update:
            ISSupdater.downloadAndRunUpdater(prerelease = update_withPrerelease)
        #UPDATER MODE
        elif updater_mode:
            runUpdaterGUI(update_withPrerelease)
        #NORMAL MODE
        else:
            tae.start()
            runMainGUI()
            tae.stop()
    except Exception as e:
        logging.error(e)
        runCrashGUI(exception=e)