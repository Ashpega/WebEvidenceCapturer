import re
import urllib.parse
import tkinter as tk
from tkinter import simpledialog

def get_basename (rawUrl):
  
    # Remove scheme
    basename = re.sub(r'^https?://', '', rawUrl)

    # Replace slashes with underscore
    basename = re.sub(r'/', '_', basename)

    # Remove leading and trailing underscore sequences
    basename = re.sub(r'^_+|_+$', '',basename)

    # URL decode
    basename = urllib.parse.unquote(basename)

    # Replace ?, =, &, # with underscore
    basename = re.sub(r'[?=&#]', '_', basename)

    # Remove prohibited characters
    basename = re.sub(r'[<>:"/\\|*]', '', basename)

    # Remove trailing dots or spaces
    basename = re.sub(r'[. ]+$', '', basename)

    # Limit length to 200 characters
    if len(basename) > 200:
        basename = basename[0:200]

    return basename

