import tkinter as tk
from tkinter import ttk

class ActionPanel:

    def __init__(self, root: tk, scanCommand, syncCommand):
    
        self.root = root

        frame = tk.Frame(root)
        frame.pack(expand=True)

        self.ScanButton = ttk.Button(frame, text="Scan", style="Accent.TButton", command=scanCommand)
        self.ScanButton.pack(side=tk.TOP, padx=10)

        self.SumaryScanLabel = ttk.Label(frame, text="", justify="center")
        self.SumaryScanLabel.pack(side=tk.TOP, padx=10,pady=20)

        self.SyncButton = ttk.Button(frame, text="Synchronize", style="Accent.TButton", command=syncCommand)
        self.SyncButton.pack(side=tk.TOP, padx=10)
        self.lockSyncButton()

    def lockSyncButton(self):
        
        self.SyncButton["state"] = "disabled"
        self.SyncButton.configure(style='')
    
    def unlockSyncButton(self):
        self.SyncButton.configure(style="Accent.TButton")

        self.SyncButton["state"] = "enabled"

