import os
import tkinter as tk
from tkinter import ttk
import threading
from tkinter import messagebox
from tkinter import filedialog

from GUI.CreateNewISSPanel import CreateNewISSPanel
from ISSScanner import bytesToString, getSkinsFromSourceMatchingWithSubscribedCollections
from pythonServices.filesService import getIconPath
from pythonServices.remoteService import getSpaceUsageOfRemoteSkinCatalog
from pythonServices.subscriptionService import SubscribedCollection, activateSubscription, deleteSubscriptionFile, desactivateSubscription, getAllSubscribedCollectionByFileName, getSubcriptionNameFromFileName, getSubscribedCollectionFromFile, importSubcriptionFile
from GUI.Components.clickableIcon import CliquableIcon

class SubscriptionLine():
    def __init__(self, fileName: str, collections: list[SubscribedCollection]):
        self.name = getSubcriptionNameFromFileName(fileName)
        self.fileName = fileName
        self.state = not fileName.endswith(".disabled")
        self.collections = collections
        #calculate sizes
        concernedRemoteSkins = getSkinsFromSourceMatchingWithSubscribedCollections("HSD", self.collections)
        self.size = getSpaceUsageOfRemoteSkinCatalog(None, concernedRemoteSkins)    

class CollectionsPanel():
    def __init__(self, root, on_loading_complete=None, on_loading_start=None):
        self.root = root
        self.on_loading_complete = on_loading_complete
        self.on_loading_start = on_loading_start
        self.subscriptionLines: list[SubscriptionLine] = []

        label = ttk.Label(text="Collections", font=("Arial", 10,"bold"))
        label.pack(side="left", fill="x",padx=5)
        collection_frame = ttk.LabelFrame(root, labelwidget=label, padding=(5, 5))
        collection_frame.pack(fill=tk.BOTH,padx=2, pady=2)

        collection_list_frame = ttk.Frame(collection_frame)
        collection_list_frame.pack()
        
        self.canvas = tk.Canvas(collection_list_frame)
        scrollbar = ttk.Scrollbar(collection_list_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.list_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.list_frame, anchor='nw')
        
        bottom_frame = tk.Frame(collection_frame)
        bottom_frame.pack(pady=0)
        self.import_button = ttk.Button(bottom_frame, text="Import new file", command=self.import_item)
        self.import_button.pack(side=tk.LEFT, pady=10, padx=10)
        self.create_button = ttk.Button(bottom_frame, text="Create new collection", command=self.create_new_ISS)
        self.create_button.pack(side=tk.RIGHT, pady=10, padx=10)
        
        self.list_frame.bind('<Configure>',
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        

    def emit_loading(self):
        #local locks
        self.import_button["state"] = "disabled"
        self.create_button["state"] = "disabled"

        #external emit
        if self.on_loading_start:
            self.root.after(0, self.on_loading_start)

    def emit_loading_completed(self):
        #local unlocks
        self.import_button["state"] = "enabled"
        self.create_button["state"] = "enabled"

        #external emit
        if self.on_loading_complete:
            self.root.after(0, self.on_loading_complete)

    def loadCollections(self):
        
        self.emit_loading()
        
        #clear the collections
        self.subscriptionLines = []
        #This is the most time consuming part, as it has to download the remote catalog and the remote iss files
        issFilesCollections = getAllSubscribedCollectionByFileName(getDisabledFiles=True)
        
        for iss_file in issFilesCollections.keys():
            self.subscriptionLines.append(SubscriptionLine(iss_file, issFilesCollections[iss_file]))
            #quick update after each line (is it usefull ?)
            self.root.after(0, self._update_list)

        self.emit_loading_completed()

    def loadCollections_async(self):
        threading.Thread(target=self.loadCollections).start()

    def _update_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
            
        for line in self.subscriptionLines:
            frame = ttk.Frame(self.list_frame)
            frame.pack(fill=tk.X, padx=5, pady=2)

            if line.state:
                CliquableIcon(
                    root=frame,
                    icon_path=getIconPath("plain-circle.png"),
                    tooltip_text="Click here to disable collection (won't be synchonised)",
                    onClick=lambda o=line: self._toggle_item(o)
                ).pack(side=tk.LEFT, padx=2)
            else:
                CliquableIcon(
                    root=frame, 
                    icon_path=getIconPath("circle.png"),
                    tooltip_text="Click here to activate collection",
                    onClick=lambda o=line: self._toggle_item(o)
                ).pack(side=tk.LEFT, padx=2)
            
            text_line = f"{line.name} ({bytesToString(line.size)})"
            ttk.Label(frame, text=text_line, width=35).pack(side=tk.LEFT, padx=5)
            
            CliquableIcon(
                root=frame, 
                icon_path=getIconPath("trash-can.png"),
                tooltip_text="Remove collection",
                onClick=lambda o=line: self._delete_item(o)
            ).pack(side=tk.RIGHT, padx=2)
            
            CliquableIcon(
                root=frame, 
                icon_path=getIconPath("magnifying-glass.png"),
                tooltip_text="See collection details (not implemented yet)",
                onClick=lambda o=line: self._edit_item(o),
                disabled=True
            ).pack(side=tk.RIGHT, padx=2)

    def import_item(self):
        file_path = filedialog.askopenfilename(
            title="Select a File",
            filetypes=[("Subscriptions","*.iss")]
        )
        if file_path:  # Ensure the user selected a file
            # Ensure the 'Subscriptions' folder exists
            importedFilePath = importSubcriptionFile(file_path)
            #load only the new file (not clean, as it would be better to do it from the subscription service)
            collections = getSubscribedCollectionFromFile(importedFilePath)
            #To be improved : add it in the proper position
            self.subscriptionLines.append(SubscriptionLine(os.path.basename(importedFilePath), collections))
            self.root.after(0, self._update_list)

    def _toggle_item(self, item: SubscriptionLine):
        if item.state:
            item.fileName = desactivateSubscription(item.fileName)
            item.state = False
        else:
            item.fileName = activateSubscription(item.fileName)
            item.state = True
        
        self._update_list()

    def _edit_item(self, item: SubscriptionLine):
        #TODO : To be implemented
        pass

    def _delete_item(self, item: SubscriptionLine):
        answer = messagebox.askyesno(title='confirmation',
                    message=f'Are you sure you want to delete "{item.name}" collection ?')
        if answer:
            deleteSubscriptionFile(item.fileName)
            self.subscriptionLines = [l for l in self.subscriptionLines if l.name != item.name]
            self._update_list()

    def create_new_ISS(self):
        #TODO : to be really implemented and tested when creation panel done
        CreateNewISSPanel(self.root, on_close=self.loadCollections_async)