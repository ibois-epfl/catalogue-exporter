from System.Windows.Forms import OpenFileDialog, DialogResult
from System.IO import Path

def FolderSelect():
    folderBrowser = OpenFileDialog()
    folderBrowser.ValidateNames = False;
    folderBrowser.CheckFileExists = False;
    folderBrowser.CheckPathExists = True;
    # Always default to Folder Selection.
    folderBrowser.FileName = "Folder Selection.";
    folderPath = ""
    if (folderBrowser.ShowDialog() == DialogResult.OK):
        folderPath = Path.GetDirectoryName(folderBrowser.FileName)
    return folderPath
