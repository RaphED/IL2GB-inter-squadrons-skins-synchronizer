import os
import tkinter as tk
from tkinter import ttk
import threading
from tkinter import messagebox
from tkinter import filedialog

from GUI.Components.resizeGrip import ResizeGrip
from GUI.ISSFileEditorGUI import ISSFileEditorWindow
from ISSScanner import bytesToString, getSkinsFromSourceMatchingWithSubscribedCollections
from pythonServices.filesService import getIconPath
from pythonServices.remoteService import getSpaceUsageOfRemoteSkinCatalog
from pythonServices.subscriptionService import SubscribedCollection, activateSubscription, deleteSubscriptionFile, desactivateSubscription, getAllSubscribedCollectionByFileName, getSubcriptionNameFromFileName, getSubscribedCollectionFromFilePath, importSubcriptionFile
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
    def __init__(self, root, on_loading_complete=None, on_loading_start=None, on_collections_change=None):
        self.root = root
        self.on_loading_complete = on_loading_complete
        self.on_loading_start = on_loading_start
        self.on_collections_change = on_collections_change
        self.subscriptionLines: list[SubscriptionLine] = []

        label = ttk.Label(text="Collections", font=("Arial", 10,"bold"))
        label.pack(side="left", fill="x",padx=5)
        collection_frame = ttk.LabelFrame(root, labelwidget=label, padding=(5, 5))
        collection_frame.pack(fill=tk.BOTH,padx=2, pady=2)

        collection_list_frame = ttk.Frame(collection_frame)
        collection_list_frame.pack(padx=0, pady=0)
        
        self.canvas = tk.Canvas(collection_list_frame)
        self.resize_grip = ResizeGrip(collection_list_frame, self.canvas, min_height=100, max_height=500, on_after_resize=self.on_resize)
        self.resize_grip.pack(fill='x', side='bottom')
        
        self.scrollbar = ttk.Scrollbar(collection_list_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.configure(height=152)
        

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Activate or desactivate mousewheel event
        self.canvas.bind('<Enter>', self._bind_mousewheel)
        self.canvas.bind('<Leave>', self._unbind_mousewheel)
        
        self.list_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.list_frame, anchor='nw')
        
        bottom_frame = tk.Frame(collection_frame)
        bottom_frame.pack(pady=0)
        self.import_button = ttk.Button(bottom_frame, text="Import new file", command=self.import_item)
        self.import_button.pack(side=tk.LEFT, pady=5, padx=10)
        self.create_button = ttk.Button(bottom_frame, text="Create new collection", command=self.create_new_ISS)
        self.create_button.pack(side=tk.RIGHT, pady=5, padx=10)
        
        self.list_frame.bind('<Configure>',
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        
        # Bind to check scrollbar visibility after content changes
        self.list_frame.bind('<Configure>', self._on_frame_configure)
        
        self.collections_buttons_registry:list[CliquableIcon] = []

    def emit_loading(self): 
        #local locks
        self.lock_actions()

        #external emit
        if self.on_loading_start:
            self.root.after(0, self.on_loading_start)

    def emit_loading_completed(self):
        #local unlocks
        self.unlock_actions()

        #external emit
        if self.on_loading_complete:
            self.root.after(0, self.on_loading_complete)
            
    def emit_collections_change(self):
        #external emit
        if self.on_collections_change:
            self.root.after(0, self.on_collections_change)

    def lock_actions(self):
        self.import_button["state"] = "disabled"
        self.create_button["state"] = "disabled"
        for button in self.collections_buttons_registry:
            button.disable()

    def unlock_actions(self):
        self.import_button["state"] = "enabled"
        self.create_button["state"] = "enabled"
        for button in self.collections_buttons_registry:
            button.enable()

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

        self.collections_buttons_registry = []

        for line in self.subscriptionLines:
            frame = ttk.Frame(self.list_frame)
            frame.pack(fill=tk.X, padx=5, pady=1)

            toggle_button = None
            if line.state:
                toggle_button = CliquableIcon(
                    root=frame,
                    icon_path=getIconPath("plain-circle.png"),
                    tooltip_text="Click to disable collection (won't be synchonised)",
                    onClick=lambda o=line: self._toggle_item(o)
                )
            else:
                toggle_button = CliquableIcon(
                    root=frame, 
                    icon_path=getIconPath("circle.png"),
                    tooltip_text="Click to activate collection",
                    onClick=lambda o=line: self._toggle_item(o)
                )
            toggle_button.pack(side=tk.LEFT, padx=2)
            self.collections_buttons_registry.append(toggle_button)
            
            text_line = f"{line.name} ({bytesToString(line.size)})"
            ttk.Label(frame, text=text_line, width=38).pack(side=tk.LEFT, padx=5)
            
            trash_button = CliquableIcon(
                root=frame, 
                icon_path=getIconPath("trash-can.png"),
                tooltip_text="Remove collection",
                onClick=lambda o=line: self._delete_item(o)
            )
            trash_button.pack(side=tk.RIGHT, padx=2)
            self.collections_buttons_registry.append(trash_button)
            
            edit_button = CliquableIcon(
                root=frame, 
                icon_path=getIconPath("magnifying-glass.png"),
                tooltip_text="See/edit collection details",
                onClick=lambda o=line: self._edit_item(o),
            )
            edit_button.pack(side=tk.RIGHT, padx=2)
            self.collections_buttons_registry.append(edit_button)
        
        # Check scrollbar visibility after updating the list
        self.root.after(10, self._update_scrollbar_visibility)

    def _update_scrollbar_visibility(self):
        # Get the height of the content and the canvas
        content_height = self.list_frame.winfo_reqheight()
        canvas_height = self.canvas.winfo_height()
        
        # Show/hide scrollbar based on content height
        if content_height > canvas_height:
            self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.canvas.configure(yscrollcommand=self.scrollbar.set)
        else:
            self.scrollbar.pack_forget()
            self.canvas.configure(yscrollcommand=None)
            # Reset view to top when hiding scrollbar
            self.canvas.yview_moveto(0)

    def _on_frame_configure(self, event=None):
        # Update the scrollregion to encompass the inner frame
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        
        # Check if scrolling is needed
        self._update_scrollbar_visibility()

    def import_item(self):
        file_path = filedialog.askopenfilename(
            title="Select a File",
            filetypes=[("Subscriptions","*.iss")]
        )
        if file_path:  # Ensure the user selected a file
            try:
                importedFilePath = importSubcriptionFile(file_path)
            except Exception as e:
                messagebox.showerror("Cannot import iss file", f"Error while importing the iss file.\n{e}")
                return
            #load only the new file (not clean, as it would be better to do it from the subscription service)
            collections = getSubscribedCollectionFromFilePath(importedFilePath)
            #To be improved : add it in the proper position
            self.subscriptionLines.append(SubscriptionLine(os.path.basename(importedFilePath), collections))
            self.root.after(0, self._update_list)
            self.on_collections_change()

    def _toggle_item(self, item: SubscriptionLine):
        if item.state:
            item.fileName = desactivateSubscription(item.fileName)
            item.state = False
        else:
            item.fileName = activateSubscription(item.fileName)
            item.state = True
        
        self._update_list()
        self.emit_collections_change()

    def _edit_item(self, item: SubscriptionLine):
            ISSFileEditorWindow(self.root, on_close=self.loadCollections_async, iss_file_name=item.fileName)

    def _delete_item(self, item: SubscriptionLine):
        answer = messagebox.askyesno(title='confirmation',
                    message=f'Are you sure you want to delete "{item.name}" collection ?')
        if answer:
            deleteSubscriptionFile(item.fileName)
            self.subscriptionLines = [l for l in self.subscriptionLines if l.name != item.name]
            self._update_list()
            #only perform change if the collection is activated
            if item.state:
                self.emit_collections_change()

    def create_new_ISS(self):
        #TODO : to be really implemented and tested when creation panel done
        ISSFileEditorWindow(self.root, on_close=self.loadCollections_async)

    #MOUSE EVENTS (for the scroll)
    def _bind_mousewheel(self, event):
        # Activer le scroll quand la souris entre dans le canvas
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    
    def _unbind_mousewheel(self, event):
        # Désactiver le scroll quand la souris quitte le canvas
        self.canvas.unbind_all("<MouseWheel>")
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_resize(self):
        self._update_scrollbar_visibility()