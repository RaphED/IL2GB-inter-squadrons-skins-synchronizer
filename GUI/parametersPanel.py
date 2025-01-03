import tkinter as tk
from tkinter import ttk, filedialog

from pythonServices.configurationService import getConf, update_config_param, allowedCockpitNotesModes, checkIL2InstallPath

class ParametersPanel:

    def __init__(self, root: tk):

        self.root = root

        label = ttk.Label(text="Parameters", font=("Arial", 10,"bold"))
        label.pack(side="left", fill="x",padx=5)  # Add some padding above the Treeview
        params_label_frame = ttk.LabelFrame(root, labelwidget=label, padding=(5, 5))
        params_label_frame.pack(fill="both",padx=2, pady=2)
        
        path_frame = tk.Frame(params_label_frame)
        path_frame.pack(fill="x", pady=5)
        self.path_label = tk.Label(path_frame, text="", highlightbackground="red")
        self.update_pathLabel()
        self.path_label.pack(side="left", fill="x", expand=True, padx=5)
        self.path_button = ttk.Button(path_frame, text="Modify", command=self.modify_path)
        self.path_button.pack(side="right", padx=5)

        # Toggle Switch
        toggle_removeSkins_frame = tk.Frame(params_label_frame)
        toggle_removeSkins_frame.pack(fill="x", pady=5)
        tk.Label(toggle_removeSkins_frame, text="Auto remove unregistered skins", anchor="w").pack(side="left", padx=5)
        self.toggle_removeSkins_var = tk.BooleanVar(value=getConf("autoRemoveUnregisteredSkins"))
        self.toggle_removeSkins_button = ttk.Checkbutton(toggle_removeSkins_frame, variable=self.toggle_removeSkins_var, onvalue=True, offvalue=False, command=self.modify_auto_remove)
        self.toggle_removeSkins_button.pack(side="right", padx=5)

        
        toggle_applyCensorship_frame = tk.Frame(params_label_frame)
        toggle_applyCensorship_frame.pack(fill="x", pady=5)
        tk.Label(toggle_applyCensorship_frame, text="Apply censorship", anchor="w").pack(side="left", padx=5)
        self.toggle_applyCensorship_var = tk.BooleanVar(value=getConf("applyCensorship"))
        self.toggle_applyCensorship_button = ttk.Checkbutton(toggle_applyCensorship_frame, variable=self.toggle_applyCensorship_var, onvalue=True, offvalue=False, command=self.modify_apply_censorship)
        self.toggle_applyCensorship_button.pack(side="right", padx=5)

        # Dropdown Menu
        dropdown_frame = tk.Frame(params_label_frame)
        dropdown_frame.pack(fill="x", pady=5)
        tk.Label(dropdown_frame, text="Cockpit Photo", anchor="w").pack(side="left", padx=5)
        self.dropdown_var = tk.StringVar(value=getConf("cockpitNotesMode"))
        self.dropdown = ttk.Combobox(
            dropdown_frame,
            textvariable=self.dropdown_var,
            values=allowedCockpitNotesModes,
            state="readonly",
        )
        self.dropdown.pack(side="right", padx=5)
        self.dropdown.bind("<<ComboboxSelected>>", self.on_dropdown_change)

    def short_path(self,fullPath, maxLength = 50):
        if len(fullPath) > maxLength:
            return f"{fullPath[:maxLength]}..."
        return fullPath
    
    def update_pathLabel(self):
        currentIL2Path = getConf("IL2GBGameDirectory")
        self.path_label.config(text=self.short_path(currentIL2Path))
        #display error if conf is unproper
        if checkIL2InstallPath():
            self.path_label.config(highlightthickness=0)
        else:
            self.path_label.config(highlightthickness=2)
    
    def modify_path(self):
        file_path = filedialog.askdirectory(
            initialdir=getConf("IL2GBGameDirectory"),
            title="Select a folder"
        )
        if len(file_path)>0:
            update_config_param("IL2GBGameDirectory",file_path)
            self.update_pathLabel()
    
    def modify_auto_remove(self):
        lebooleanquejeveux=self.toggle_removeSkins_var.get()
        update_config_param("autoRemoveUnregisteredSkins", lebooleanquejeveux)

    def modify_apply_censorship(self):
        lebooleanquejeveux=self.toggle_applyCensorship_var.get()
        update_config_param("applyCensorship", lebooleanquejeveux)
    
    def on_dropdown_change(self, event):
        """Handle dropdown value change."""
        selected_value = self.dropdown_var.get()
        update_config_param("cockpitNotesMode", selected_value)