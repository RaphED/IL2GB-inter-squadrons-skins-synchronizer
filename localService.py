import os
import hashlib

def getSkinsList():

    skinsDirectory = "D:\SteamLibrary\steamapps\common\IL-2 Sturmovik Battle of Stalingrad\data\graphics\skins"
    
    dds_files = []
    
    for root, dirs, files in os.walk(skinsDirectory):
        
        #continue if no files
        if len(files) == 0:
            continue

        #get only dds files
        ddsfiles = [f for f in files if f.lower().endswith('.dds')]

        if len(ddsfiles) == 0:
            continue

        parentDir = os.path.dirname(root)
        
        #only manage 1 level skins (otherwise i suspect badly place sinks)
        if parentDir != skinsDirectory:
            print(f"Unexpected skin(s) {ddsfiles} placement at {root}. Not managed")
            continue
        
        aircraft =  os.path.basename(os.path.normpath(root))

        for ddsFileName in ddsfiles:
            fileFullPath = os.path.join(root,ddsFileName)
            filestats = os.stat(fileFullPath)
            file = open(fileFullPath, "rb")
            filereader = file.read()
            
            dds_files.append({
                "ddsFileName": ddsFileName,
                "aircraft": aircraft,
                "filesize": filestats.st_size,
                "md5": hashlib.md5(filereader).hexdigest()
            })
            #TODO : manage double DDS files
    
    return dds_files