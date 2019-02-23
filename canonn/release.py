"""
Module to provide the news.
"""

import Tkinter as tk
from Tkinter import Frame
import uuid
from ttkHyperlinkLabel import HyperlinkLabel
import requests
import json
import re
import myNotebook as nb
from config import config
import zipfile
import StringIO
import os
import shutil

NEWS_CYCLE=60 * 1000 * 60 # 1 Hour
DEFAULT_URL = 'https://github.com/canonn-science/EDMC-Canonn/releases'
WRAP_LENGTH = 200

def _callback(matches):
    id = matches.group(1)
    try:
        return unichr(int(id))
    except:
        return id


def decode_unicode_references(data):
    return re.sub("&#(\d+)(;|(?=\s))", _callback, data)

class ReleaseLink(HyperlinkLabel):

    def __init__(self, parent):

        HyperlinkLabel.__init__(
            self,
            parent,
            text="Fetching...",
            url=DEFAULT_URL,
            wraplength=50,  # updated in __configure_event below
            anchor=tk.NW
        )
        self.bind('<Configure>', self.__configure_event)
 
    def __configure_event(self, event):
        "Handle resizing."

        self.configure(wraplength=event.width)
    
class Release(Frame):

    def __init__(self, parent,release,gridrow):
        "Initialise the ``News``."

        padx, pady = 10, 5  # formatting
        sticky = tk.EW + tk.N  # full width, stuck to the top
        anchor = tk.NW        
        
        Frame.__init__(
            self,
            parent
        )
                        
        self.auto=tk.IntVar(value=config.getint("AutoUpdate"))                
        
        
        self.columnconfigure(1, weight=1)
        self.grid(row = gridrow, column = 0, sticky="NSEW",columnspan=2)
        
        self.label=tk.Label(self, text=  "Release:")
        self.label.grid(row = 0, column = 0, sticky=sticky)
        
        self.hyperlink=ReleaseLink(self)
        self.hyperlink.grid(row = 0, column = 1,sticky="NSEW")
        
        self.release=release
        self.news_count=0
        self.news_pos=0
        self.minutes=0
        
        #self.hyperlink.bind('<Configure>', self.hyperlink.configure_event)
        self.after(250, self.release_update)
        
    def version2number(self,version):
        major,minor,patch=version.split('.')
        return (int(major)*1000000)+(int(minor)*1000)+int(patch)

    def release_update(self):
        "Update the news."
        
        #refesh every 60 seconds
        self.after(NEWS_CYCLE, self.release_update)
        
        
        
        self.latest=requests.get("https://api.github.com/repos/canonn-science/EDMC-Canonn/releases/latest").json()
        
        current=self.version2number(self.release)
        release=self.version2number(self.latest.get("tag_name"))
        
        self.hyperlink['url'] = self.latest.get("html_url")
        self.hyperlink['text'] = self.latest.get("tag_name")

        if current==release:
            self.grid_remove()
        elif current > release:
            self.hyperlink['text'] = "Experimental Release {}".format(self.release)
            self.grid()
        else:
            
            if self.auto.get() == 1:
                self.hyperlink['text'] = "Release {}  Installed Please Restart".format(self.latest.get("tag_name"))     
                self.installer(self.latest.get("tag_name"))
            else:
                self.hyperlink['text'] = "Please Upgrade {}".format(self.latest.get("tag_name"))
            self.grid()            
    
    def plugin_prefs(self, parent, cmdr, is_beta,gridrow):
        "Called to get a tk Frame for the settings dialog."

        self.auto=tk.IntVar(value=config.getint("AutoUpdate"))
        
        #frame = nb.Frame(parent)
        #frame.columnconfigure(1, weight=1)
        return nb.Checkbutton(parent, text="Auto Update THis Plugin", variable=self.auto).grid(row = gridrow, column = 0,sticky="NSEW")
        
        #return frame
    
    
    
    def prefs_changed(self, cmdr, is_beta):
        "Called when the user clicks OK on the settings dialog."
        config.set('AutoUpdate', self.auto.get())      
        
    def installer(self,tag_name):
        download=requests.get("https://github.com/canonn-science/EDMC-Canonn/archive/{}.zip".format(tag_name), stream=True)
        z = zipfile.ZipFile(StringIO.StringIO(download.content))
        z.extractall(os.path.dirname(Release.plugin_dir))
        
        #make a backup of the current plugin -- just in case I haven't checked it in yet
        recursive_overwrite(Release.plugin_dir,"{}.disabled".format(Release.plugin_dir))
        #copy the contents of the new release -- we should probably delete everything first
        recursive_overwrite("{}/EDMC-Canonn-{}".format(os.path.dirname(Release.plugin_dir),tag_name),Release.plugin_dir)
        #remove the downloaded directory
        shutil.rmtree("{}/EDMC-Canonn-{}".format(os.path.dirname(Release.plugin_dir),tag_name))
        
    @classmethod    
    def plugin_start(cls,plugin_dir):
        cls.plugin_dir=plugin_dir

        
def recursive_overwrite(src, dest, ignore=None):
    if os.path.isdir(src):
        if not os.path.isdir(dest):
            os.makedirs(dest)
        files = os.listdir(src)
        if ignore is not None:
            ignored = ignore(src, files)
        else:
            ignored = set()
        for f in files:
            if f not in ignored:
                recursive_overwrite(os.path.join(src, f), 
                                    os.path.join(dest, f), 
                                    ignore)
    else:
        shutil.copyfile(src, dest)    