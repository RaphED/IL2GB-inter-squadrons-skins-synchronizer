import json
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
import os 
from pythonServices.filesService import getRessourcePath

from pythonServices.subscriptionService import getSubcriptionNameFromFileName, getSubscribeCollectionFromRawJson, saveSubscriptionFile
from pythonServices.remoteService import getSkinsCatalogFromSource
from ISSScanner import getSkinsFromSourceMatchingWithSubscribedCollections

import tkinter as tk
from tkinter import ttk

class CreateNewISSPanel:
    def __init__(self, parent: tk.Tk,on_close,iss_file_name=None):
        self.runningTask=None
       

        self.editting_item_id=None

        self.on_close = on_close

        # Create a Toplevel window
        self.window = tk.Toplevel(parent)
        self.window.title("ISS file detail")
        self.window.iconbitmap(getRessourcePath("iss.ico"))

        self.window.geometry("1200x980")

        # Call on_close when the window is closed

        # Top Inputs in a LabelFrame
        frame_inputs = ttk.LabelFrame(self.window, text="Filters/ Criterias :", padding=5)
        frame_inputs.pack(fill="x", padx=10, pady=5)
        frame_inputs.grid_rowconfigure(1, weight=1)  # Adjust as needed for the row
        frame_inputs.grid_columnconfigure(0, weight=1)  # Adjust as needed for the column

        frame_queries = ttk.Frame(frame_inputs, padding=0)
        frame_queries.grid(row=0, column=0, padx=0, pady=0)

             
        self.title_var = tk.StringVar()
        ttk.Label(frame_queries, text="Title").grid(row=0, column=0, sticky="w", padx=5, pady=0)
        self.entry_title = ttk.Entry(frame_queries, textvariable=self.title_var, width=20)
        self.entry_title.grid(row=0, column=1, padx=5, pady=0)

        frame_queries.grid_columnconfigure(2, minsize=180)

        self.il2group_var = tk.StringVar()
        ttk.Label(frame_queries, text="il2Group:").grid(row=0, column=3, sticky="w", padx=5, pady=0)
        self.entry_il2group = ttk.Entry(frame_queries, textvariable=self.il2group_var,width=20,)
        self.entry_il2group.grid(row=0, column=4, padx=5, pady=0)
        
        frame_queries.grid_columnconfigure(5, minsize=180)

        self.skinPack_var = tk.StringVar()
        ttk.Label(frame_queries, text="SkinPack").grid(row=0, column=6, sticky="w", padx=5, pady=0)
        self.entry_skinPack = ttk.Entry(frame_queries,textvariable=self.skinPack_var, width=20)
        self.entry_skinPack.grid(row=0, column=7, padx=5, pady=0)        

        #Adding listening to input change       
        self.title_var.trace_add("write", self.update_dynamic_list)
        self.skinPack_var.trace_add("write", self.update_dynamic_list)
        self.il2group_var.trace_add("write", self.update_dynamic_list)


        #Planes of the current filters
        self.tree_creating_criterias = ttk.Treeview(frame_inputs, columns=("plane","IL2Group","SkinPack"), show="headings", height=10,)
        self.tree_creating_criterias.grid(row=1, columnspan=2, padx=5, pady=5,sticky="nsew")

        self.tree_creating_criterias.heading("plane", text="Title", anchor="w")
        self.tree_creating_criterias.heading("IL2Group", text="IL2Group", anchor="w")
        self.tree_creating_criterias.heading("SkinPack", text="SkinPack", anchor="w")
        for plane in getSkinsCatalogFromSource("HSD"):
            self.tree_creating_criterias.insert("", "end", values=(plane.infos["Title"],plane.infos["IL2Group"],plane.infos["SkinPack"]))


        # Buttons and comment to add it
        frame_comment_and_button = ttk.Frame(frame_inputs, padding=5)
        frame_comment_and_button.grid(row=2,padx=5, pady=5)
        

        self.comment_var=tk.StringVar()
        ttk.Label(frame_comment_and_button, text="Comments :").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.entry_comment = ttk.Entry(frame_comment_and_button,textvariable=self.comment_var, width=40)
        self.entry_comment.grid(row=0, column=1, padx=5, pady=0)


        button_add_param = ttk.Button(frame_comment_and_button, text="Save criterias", style="Accent.TButton", command=self.add_parameter)
        button_add_param.grid(row=0, column=3, columnspan=2, pady=0)

        # Treeview for Parameters in a LabelFrame
        frame_params = ttk.LabelFrame(self.window, text="Existing criterias", padding=10)
        frame_params.pack(fill="x", padx=10, pady=5)

        columns = ("comment", "il2Group", "skinPack", "title")
        self.tree_params = ttk.Treeview(frame_params, columns=columns, show="headings", height=5)  # Set height to 5 rows
        self.tree_params.pack(side="left", fill="x", expand=True)

        # Add vertical scrollbar
        scrollbar = ttk.Scrollbar(frame_params, orient="vertical", command=self.tree_params.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree_params.configure(yscrollcommand=scrollbar.set)

        # Configure columns
        for col in columns:
            self.tree_params.column(col, width=150, anchor="center")  # Center text in column
            self.tree_params.heading(col, text=col.capitalize(), anchor="center")  # Center-align text in header

        # Buttons
        button_delete_param = ttk.Button(frame_params, text="Delete", command=self.delete_parameter)
        button_delete_param.pack(side="right", padx=5)

        button_edit_param = ttk.Button(frame_params, text="Edit", command=self.edit_parameter)
        button_edit_param.pack(side="right", padx=5)

        
        # Save button
        frame_controls = ttk.Frame(self.window)
        frame_controls.pack(pady=10, fill="both", anchor="center", side="bottom")

        # Label
        label_title = ttk.Label(frame_controls, text="File name:")
        label_title.grid(row=0, column=0, padx=5, pady=5)

        # Entry field
        self.filename_var=tk.StringVar()
        entry_filename = ttk.Entry(frame_controls, textvariable=self.filename_var)
        #for the moment, we do not allow chaging name in edit mode
        if iss_file_name is not None:
            entry_filename.configure(state="disabled")
        entry_filename.grid(row=0, column=1, padx=5, pady=5)

        # Button
        button_save = ttk.Button(frame_controls, text="Save to .ISS", style="Accent.TButton", command=self.save_to_iss)
        button_save.grid(row=0, column=2, padx=5, pady=5)
      

        # Plane Selection in a LabelFrame
        frame_planes = ttk.LabelFrame(self.window, text="Resulting plane list", padding=10)
        frame_planes.pack(fill="both", expand=True, padx=10, pady=5)


        #Planes 
        self.tree_selected_planes = ttk.Treeview(frame_planes, columns=("plane","IL2Group","SkinPack"), show="headings", height=10,)
        self.tree_selected_planes.pack(fill="both",padx=5, pady=5)

        self.tree_selected_planes.heading("plane", text="Title", anchor="w")
        self.tree_selected_planes.heading("IL2Group", text="IL2Group", anchor="w")
        self.tree_selected_planes.heading("SkinPack", text="SkinPack", anchor="w")


        # Populate sample planes

        self.edited_iss_fileName = iss_file_name
        if iss_file_name!=None:
            self.filename_var.set(getSubcriptionNameFromFileName(iss_file_name))
            subscriptionPath = os.path.join(os.getcwd(),"Subscriptions",iss_file_name)

            file = open(subscriptionPath, "r")
            rawJsonData = json.load(file)

            for rawSubscription in rawJsonData:
                criteria = rawSubscription.get("criteria", {})
                comment =  rawSubscription.get("comment", "")
                il2Group = criteria.get("IL2Group", "")
                skinPack = criteria.get("SkinPack", "")
                title = criteria.get("Title", "")

                self.tree_params.insert("", "end", values=(comment, il2Group, skinPack, title))

            threading.Thread(target=self.actualiseSelectedPlanes()).start()
    
    def actualise_dynamic_planes(self):      
        il2Group = self.entry_il2group.get()
        if len(il2Group)>0 : il2Group="*"+il2Group.strip('*')+"*"
        
        skinPack = self.entry_skinPack.get()
        if len(skinPack)>0 : skinPack="*"+skinPack.strip('*')+"*"

        title = self.entry_title.get()
        if len(title)>0 : title="*"+title.strip('*')+"*"

        comment = self.entry_comment.get()

        rawjson=element_to_json(comment, il2Group, skinPack, title)
        collections= getSubscribeCollectionFromRawJson(rawjson,"test")
        skins=getSkinsFromSourceMatchingWithSubscribedCollections("HSD", collections)
        
        # Add these slins to the view below so the user can see the implied skins
        self.tree_creating_criterias.delete(*self.tree_creating_criterias.get_children())

        for skin in skins:
            self.tree_creating_criterias.insert("", "end", values=(skin.getValue("name"),skin.infos["IL2Group"],skin.infos["SkinPack"]))
        self.runningTask=None

    def update_dynamic_list(self, *args):
        if self.runningTask:
            self.runningTask.stop()
            
        self.runningTask=threading.Thread(target=self.actualise_dynamic_planes()).start()

    def add_parameter(self):
        comment = self.entry_comment.get()
        
        il2Group = self.entry_il2group.get()
        if len(il2Group)>0 : il2Group="*"+il2Group.strip('*')+"*"
        
        skinPack = self.entry_skinPack.get()
        if len(skinPack)>0 : skinPack="*"+skinPack.strip('*')+"*"

        title = self.entry_title.get()
        if len(title)>0 : title="*"+title.strip('*')+"*"

        if title or il2Group or skinPack:
            if self.editting_item_id==None:
                self.tree_params.insert("", "end", values=(comment, il2Group, skinPack, title))
            else: 
                self.tree_params.item(self.editting_item_id, values=(comment, il2Group, skinPack, title))
                self.editting_item_id=None
        
        threading.Thread(target=self.actualiseSelectedPlanes()).start()


    def delete_parameter(self):
        selected_item = self.tree_params.selection()
        for item in selected_item:
            self.tree_params.delete(item)
        
        threading.Thread(target=self.actualiseSelectedPlanes()).start()

    
    def edit_parameter(self):
        selected_items = self.tree_params.selection()
        if len(selected_items)==1:
            for item_id in selected_items:
                item_data = self.tree_params.item(item_id)
                values = item_data["values"]
                self.editting_item_id=item_id
        self.il2group_var.set(values[1])
        self.skinPack_var.set(values[2])
        self.title_var.set(values[3])
        self.comment_var.set(values[0])


    
    def actualiseSelectedPlanes(self):
        rawjson=treeview_to_json(self.tree_params)
        collections= getSubscribeCollectionFromRawJson(rawjson,"test")
        skins=getSkinsFromSourceMatchingWithSubscribedCollections("HSD", collections)
        
        # Add these slins to the view below so the user can see the implied skins
        self.tree_selected_planes.delete(*self.tree_selected_planes.get_children())

        for skin in skins:
            self.tree_selected_planes.insert("", "end", values=(skin.getValue("name"),skin.infos["IL2Group"],skin.infos["SkinPack"]))


    def save_to_iss(self):
        
        #generate the file name if we are in creation mode
        if self.edited_iss_fileName is None:
            self.edited_iss_fileName = self.filename_var.get() + ".iss"
        
        if self.filename_var.get() == "":
            messagebox.showerror("Collection name is required", "Please set a collection name before saving your file")
            return

        # Convert treeview data to JSON and save to file
        data = treeview_to_json(self.tree_params)  # Ensure this method returns the desired data as a dictionary or list
        try:
            saveSubscriptionFile(self.edited_iss_fileName, json_content=data)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while saving the file: {str(e)}")
            return
                
        threading.Thread(target=self.close_async()).start()


    def close_async(self):
        time.sleep(0.5)
        self.window.destroy()
        self.on_close()


def element_to_json(comment, il2Group, skinPack, title):   
    result = []
    entry = {"source": "HSD","comment": comment, "criteria": {}}
    if il2Group:
        entry["criteria"]["IL2Group"] = il2Group
    if skinPack:
        entry["criteria"]["SkinPack"] = skinPack
    if title:
        entry["criteria"]["Title"] = title
    result.append(entry)
    return json.dumps(result)

def treeview_to_json(treeview):
    rows = []
    for row_id in treeview.get_children():
        row_values = treeview.item(row_id)["values"]
        rows.append(row_values)

    result = []
    for row in rows:
        comment, il2Group, skinPack, title = row
        entry = {"source": "HSD","comment": comment, "criteria": {}}
        if il2Group:
            entry["criteria"]["IL2Group"] = il2Group
        if skinPack:
            entry["criteria"]["SkinPack"] = skinPack
        if title:
            entry["criteria"]["Title"] = title

        result.append(entry)

    return json.dumps(result)
