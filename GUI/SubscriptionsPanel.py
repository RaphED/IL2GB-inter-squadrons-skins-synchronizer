from enum import Enum
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
import tk_async_execute as tae
import asyncio
from pythonServices.messageBrocker import MessageBrocker

from pythonServices.subscriptionService import getAllSubscribedCollectionByFileName
from pythonServices.remoteService import getSpaceUsageOfRemoteSkinCatalog, RemoteSkin
from ISSScanner import getSkinsMatchingWithSubscribedCollection, bytesToString

class PlanesLinked:
    name=None
    onLocal=False
    treeID=None

    def __init__(self,name,onLocal,treeID):
        self.name=name
        self.onLocal=onLocal
        self.treeID=treeID

class SubscriptionState(Enum):
    NOTLOADED = 1
    LOADED = 2
    DISABLED = 3

class Subscription:
    name=None
    treeID=None
    state=SubscriptionState.NOTLOADED
    size=None
    planesLinked=list[PlanesLinked]
    fileName=None

    def __init__(self,name,fileName,treeID,state):#,,size):
        self.name=name
        self.treeID=treeID
        self.state=state
        self.fileName=fileName
        # self.size=size


class SubscriptionPanel:

    subscriptions = []

    def __init__(self, root: tk):
        global subscriptions
        subscriptions = []
        self.root = root
        
        label = ttk.Label(text="Collections", font=("Arial", 10,"bold"))
        label.pack(side="left", fill="x",padx=5)  # Add some padding above the Treeview
        subscription_label_frame = ttk.LabelFrame(root, labelwidget=label, padding=(5, 5))
        subscription_label_frame.pack(fill="both",padx=2, pady=2)

        self.tree = ttk.Treeview(subscription_label_frame, show="tree", style="Treeview" )
        self.tree.pack(fill="both",  padx=5, pady=5)
        
        self.the_start_of_syncs()
     
        # Bind a selection event to the Treeview
        self.tree.bind("<<TreeviewSelect>>", self.on_item_selected)

        # Add background color to the button frame for visibility
        self.add_button = ttk.Button(subscription_label_frame, text="Import", command=self.add_item)
        self.add_button.pack(side="left", padx=10, pady=5)

        self.delete_button = ttk.Button(subscription_label_frame, text="Delete", command=self.delete_item)
        self.delete_button.pack(side="left", padx=5, pady=5)

        self.switch_state_button = ttk.Button(subscription_label_frame, text="Activate/Disable", command=self.switch_state)
        self.switch_state_button.pack(side="left", padx=5, pady=5)

    def the_start_of_syncs(self):
        tae.async_execute(self.async_populate_tree(), wait=False, visible=False, pop_up=False, callback=None, master=self.root)

    async def async_populate_tree(self):
        # Simulate the 5-second loading process with asyncio.sleep (replace this with actual data loading logic)
        self.populate_tree()

    def populate_tree(self):
        MessageBrocker.emitConsoleMessage("Getting collections from /Subscriptions folder")
        MessageBrocker.emitProgress(0.2)
        collectionByNameSubscribeFile = getAllSubscribedCollectionByFileName()
        global subscriptions
        subscriptions = []

        #Part adding the disactivated
        subscriptionPath = os.path.join(os.getcwd(),"Subscriptions")
        #create subsciption path of not exists
        for root, dirs, files in os.walk(subscriptionPath):
            for file in files:
                if file.endswith(".iss.disabled"): #We only consider files with iss extension
                    name=buildCollectionTreeLabel(file[:file.find(".iss.disabled")], isDisabled=True)
                    sub_id = self.tree.insert("", "end",text=name )
                    newSub=Subscription(name=name,fileName=file[:file.find(".iss.disabled")],treeID=sub_id,state=SubscriptionState.DISABLED)
                    subscriptions.append(newSub)        

        #We have the files, we add it to the tree and display the GUI as soon as possible and say it's loading
        for ISSFile in collectionByNameSubscribeFile.keys():
            text=buildCollectionTreeLabel(ISSFile, catalogSize=0,loading=True)
            tree_id = self.tree.insert("", "end", text=text)  # Add main item
            newSub=Subscription(name=text,fileName=ISSFile,treeID=tree_id,state=SubscriptionState.NOTLOADED)
            subscriptions.append(newSub)


        #This part needs to be even more async and fire and forget until it has the results
        tae.async_execute(self.async_populate_tree_after_calculate(collectionByNameSubscribeFile), wait=False, visible=False, pop_up=False, callback=None, master=self.root)

    async def async_populate_tree_after_calculate(self,collectionByNameSubscribeFile):        
        for ISSFile in collectionByNameSubscribeFile.keys():
            skinCollection = list[RemoteSkin]()
            catalogSize=0

            for collection in collectionByNameSubscribeFile[ISSFile]:
                skinCollection += getSkinsMatchingWithSubscribedCollection(collection)
            
            catalogSize+=getSpaceUsageOfRemoteSkinCatalog("HSD",skinCollection)#TODO change this ! This is bad and an aprox, you mays have a lot of repeats !

                #Get the current loading elements of the treeview:
            for obj in subscriptions:
                if obj.fileName == ISSFile:
                    self.tree.item(obj.treeID, text=buildCollectionTreeLabel(ISSFile, catalogSize=catalogSize)) 
                    for skin in skinCollection:
                        self.tree.insert(obj.treeID, "end", text=skin.getValue('name'))
                    break

    def on_item_selected(self, event):
        """Handle the selection event."""
        selected_item = self.tree.selection()

    def add_item(self):
        file_path = filedialog.askopenfilename(
            title="Select a File",
            filetypes=[("Subscriptions","*.iss")]
        )
        if file_path:  # Ensure the user selected a file
            # Ensure the 'Subscriptions' folder exists
            subscriptions_folder = "Subscriptions"
            os.makedirs(subscriptions_folder, exist_ok=True)

            # Copy the selected file to the 'Subscriptions' folder
            file_name = os.path.basename(file_path)  # Extract the file name
            destination_path = os.path.join(subscriptions_folder, file_name)
            shutil.copy(file_path, destination_path)

            # Add the file name to the Treeview// refresh like a *turd*
            for item in self.tree.get_children():
                self.tree.delete(item)

            self.populate_tree()

    def delete_item(self):
        selected_item = self.tree.selection()
        if selected_item:  # Ensure something is selected
            for item in selected_item:
                parent = self.tree.parent(item)  # Get the parent of the selected item
                if parent == "":  # Top-level items have an empty string as their parent
                    answer = messagebox.askyesno(title='confirmation',
                    message='Are you sure you want to delete this subscription ?')
                    if answer:
                        file_name = self.tree.item(item, 'text')
                        colelctionLabel = self.tree.item(item, 'text') 
                        collectionName = getCollectionNameFromTreeLabel(colelctionLabel)
                        isDisabled = colelctionLabel.endswith("DISABLED")
                        withoutExtensionFileName = os.path.join("Subscriptions", collectionName)
                        if isDisabled:
                            os.remove(withoutExtensionFileName + ".iss.disabled")
                        else:
                            os.remove(withoutExtensionFileName + ".iss")

                        for item in self.tree.get_children():
                            self.tree.delete(item)

                        self.populate_tree()
                else:
                    # TODO Thinking about planes you don't want and might have an exclusion list :)
                    print(f"Cannot delete item: {item}. Only top-level items can be deleted.")
        else:
            print("No item selected to delete.")

    def switch_state(self):
        selected_item = self.tree.selection()
        if selected_item:  # Ensure something is selected
            for item in selected_item:
                parent = self.tree.parent(item)  # Get the parent of the selected item
                if parent == "":  # Top-level items have an empty string as their parent
                    colelctionLabel = self.tree.item(item, 'text') 
                    collectionName = getCollectionNameFromTreeLabel(colelctionLabel)
                    isDisabled = colelctionLabel.endswith("DISABLED")
                    withoutExtensionFileName = os.path.join("Subscriptions", collectionName)
                    if isDisabled:
                        os.rename(withoutExtensionFileName+'.iss.disabled',withoutExtensionFileName+'.iss')
                    else:
                        os.rename(withoutExtensionFileName+'.iss',withoutExtensionFileName+'.iss.disabled')

                    for item in self.tree.get_children():
                        self.tree.delete(item)

                    self.populate_tree()


#TODO : Quite temporary solution before handling properly objects instead of strings and titles
treeLabelSeparator = "\t\t"
def buildCollectionTreeLabel(catalogName,catalogSize = 0, isDisabled = False,loading=False ):
    if loading:
        return f"{catalogName}{treeLabelSeparator} (LOADING ...)"
    if isDisabled:
        return f"{catalogName}{treeLabelSeparator}DISABLED"
    else:
        return f"{catalogName}{treeLabelSeparator}({bytesToString(catalogSize)})"

def getCollectionNameFromTreeLabel(treeLabel: str):
    splits = treeLabel.split(f"{treeLabelSeparator}")
    collectionName = splits[0]
    return collectionName
                 