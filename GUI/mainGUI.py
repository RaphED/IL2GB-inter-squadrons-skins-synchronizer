from tkinter import ttk
import tkinter as tk
import logging
import tk_async_execute as tae
import webbrowser

from pythonServices.configurationService import configurationFileExists, getConf
from pythonServices.filesService import getRessourcePath, getIconPath, cleanTemporaryFolder

from GUI.SubscriptionsPanel import SubscriptionPanel
from GUI.parametersPanel import ParametersPanel
from GUI.consolePanel import ConsolePanel
from GUI.actionsPanel import ActionPanel
from GUI.progressBar import ProgressBar
from GUI.Components.clickableIcon import CliquableIcon
from GUI.firstLaunchGUI import runFirstLaunchGUI

import ISSsynchronizer
import ISSScanner

class MainGUI:
    
    def __init__(self, root):

        self.root = root

        self.root.iconbitmap(getRessourcePath("iss.ico"))

        style = ttk.Style(self.root)
        
        self.root.tk.call("source",getRessourcePath("forest-light.tcl"))
        style.theme_use("forest-light")

        self.root.title("InterSquadron Skin Synchronizer")
        self.root.geometry("850x600")
        
        # 1 - UPPER FRAME
        top_main_frame = tk.Frame(self.root)
        top_main_frame.pack(side="top", fill="both")
        # 1.1 - left upper frame
        left_upper_frame = tk.Frame(top_main_frame)
        left_upper_frame.pack(side="left", fill="both")

        self.subscriptionsPanel = SubscriptionPanel(left_upper_frame)

        # 1.2 - right upper frame
        right_upper_frame = tk.Frame(top_main_frame)
        right_upper_frame.pack(side="right", fill="both")
        
        self.parametersPanel = ParametersPanel(right_upper_frame)
        self.actionPanel = ActionPanel(right_upper_frame, scanCommand = self.start_scan, syncCommand=self.start_sync)

        # 2 - BOTTOM FRAME
        #2.1 info bar
        info_bar = tk.Frame(self.root)
        info_bar.pack(fill="both")

        info_bar.grid_columnconfigure(0, weight=0)  # Left column
        info_bar.grid_columnconfigure(1, weight=1)  # Middle colum, takes all possible width
        info_bar.grid_columnconfigure(2, weight=0)  # Right
        info_bar.grid_rowconfigure(0)
        
        self.irreIcon = CliquableIcon(
            info_bar, 
            icon_path=getIconPath("irre-logo-32.png"),
            onClick=open_link_IRREWelcome,
            opacityFactor=10,
            onMouseOverOpacityFactor=255
        )
        self.progressBar = ProgressBar(info_bar)

        self.helpIcon = CliquableIcon(
            info_bar, 
            icon_path=getIconPath("help-32.png"), 
            tooltip_text="Online ISS documentation", 
            onClick=open_link_ISSDocumentation
        )
        
        self.irreIcon.grid(column=0, row=0, padx=5, pady=2)
        self.progressBar.grid(column=1, row=0, padx=5, pady=5)
        self.helpIcon.grid(column=2, row=0, padx=5, pady=2)
        
        bottom_main_frame = tk.Frame(self.root)
        bottom_main_frame.pack(side="bottom", fill="both", expand=True)

        self.consolePanel = ConsolePanel(bottom_main_frame)

        #OTHER STORED INFORMATION
        self.currentScanResult: ISSsynchronizer.ScanResult = None


    def updateScanResult(self, scanResult: ISSsynchronizer.ScanResult):
        self.currentScanResult = scanResult

        if scanResult is None:
            self.consolePanel.clearPanel()
            self.actionPanel.lockSyncButton()
            self.actionPanel.setScanLabelText("...")
        else:
            #Display the scan result in the console
            self.consolePanel.addLine(scanResult.toString())

            if scanResult.IsSyncUpToDate():
                self.actionPanel.lockSyncButton()
                self.actionPanel.setScanLabelText("Skins are up to date.")

            else:
                self.actionPanel.unlockSyncButton()
                stats=scanResult.getDiskUsageStats()
                byteSizeToBeDownload=sum(stats["missingSkinsSpace"].values())+sum(stats["toBeUpdatedSkinsSpace"].values())+stats["toBeUpdatedCustomPhotos"]
                stringAddPart=""
                if byteSizeToBeDownload!=0:
                    stringAddPart="To download: "+ISSScanner.bytesToString(byteSizeToBeDownload)+"."
                byteSizeToBeRemoved=stats["toBeRemovedSkinsSpace"]
                stringRemovePart=""
                if byteSizeToBeRemoved!=0 and getConf("autoRemoveUnregisteredSkins"):
                    stringRemovePart="To remove: "+ISSScanner.bytesToString(byteSizeToBeRemoved)+"."

                self.actionPanel.setScanLabelText(stringAddPart+" "+stringRemovePart)# TODO rajouter un vrai print en allant peux être faire un refactif du scanResult pour les avoir propre, possiblement en même temps que les prints dans le scan...

    def start_scan(self):
        tae.async_execute(self.start_async_scan(), wait=True, visible=False, pop_up=False, callback=None, master=self.root)

    async def start_async_scan(self):
        self.updateScanResult(None)
        scanResult = ISSScanner.scanAll()
        if scanResult is not None:
            self.updateScanResult(scanResult)
    
    def start_sync(self):
        if self.currentScanResult is None:
            logging.error("Sync launched with no scan result")
            return
        tae.async_execute(ISSsynchronizer.updateAll(self.currentScanResult), wait=True, visible=False, pop_up=False, callback=None, master=self.root)

        #once sync done, lock it
        self.actionPanel.lockSyncButton()

#TOOLS

def open_link(link: str):
    webbrowser.open(link)

def open_link_ISSDocumentation():
    open_link("https://melodious-andesaurus-f9a.notion.site/IL2GB-Inter-squadron-Skin-Synchronizer-ISS-1477b1e5c2b8803db322d0daba993f94")

def open_link_IRREWelcome():
    open_link("https://www.lesirreductibles.com")

#MAIN RUN
def runMainGUI():
    
    #make sure the temporary folder is clean -> do not do that due to update !
    cleanTemporaryFolder()

    #check conf file is generated
    if not configurationFileExists():
        runFirstLaunchGUI()
    
    root = tk.Tk()
    mainGUI = MainGUI(root)

    # tae.start()
    root.mainloop()
    # tae.stop()