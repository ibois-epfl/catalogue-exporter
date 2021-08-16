import os
from distutils.dir_util import copy_tree
import System
import System.Collections.Generic.IEnumerable as IEnumerable
import math
import time
import uuid
import Rhino
import scriptcontext as sc
import rhinoscriptsyntax as rs
import MinimumBoundingBox as MinBBox
import FolderSelect as fs
import DictTools as dt
import csv
import datetime
import getpass
import random

__commandname__ = "CatalogueExporter"

# RunCommand is the called when the user enters the command name in Rhino.
# The command name is defined by the filname minus "_cmd.py"


def RunCommand(is_interactive):

    doc = sc.doc.ActiveDoc
    pathToExportCatalogue = fs.FolderSelect() + "\\"

    def catalogueProcessing():

        # Get point clouds GUID list
        gPC = Rhino.Input.Custom.GetObject()
        gPC.SetCommandPrompt("Select point clouds")
        gPC.GeometryFilter = Rhino.DocObjects.ObjectType.PointSet
        gPC.GetMultiple(1, 0)
        if gPC.CommandResult() != Rhino.Commands.Result.Success:
            return 1 # gPC.CommandResult()
        idListPC = [gPC.Object(i).ObjectId for i in range(gPC.ObjectCount)]
        doc.Objects.UnselectAll()
        
        # Get params
        
        # Defaults params
        downsample = 0
        normalsNeighbours = 30
        poisonMaxDepth = 6
        poisonMinDepth = 0
        poisonScale = 1.1
        poissonLinear = [False]
        voxelSize = 0.002

        specifyParameters = rs.GetBoolean(
            message = "Do you want to specify processing parameters or accept defaults?",
            items = [["ProcessingParameters", "Default", "Specify"]],
            defaults = [False]
        )
        if (specifyParameters == None):
            return 1
            
        specifyLabels = rs.GetBoolean(
            message = "Do you want to give each item a label (e.g.  'Stone42')? If given, it will prefix the item's asigned unique identifier (e.g. 'Stone42_d18812e8-9cc1-4992-b56b-571ad1f16832')",
            items = [["LabelEachItem", "UniqueIdentifier", "Label_UniqueIdentifier"]],
            defaults = [False]
        )
        if (specifyParameters == None):
            return 1
            
        if (specifyParameters[0]):
            
            # Get params: mesh Poisson
            Rhino.RhinoApp.WriteLine("Set parameters for the 'Mesh Poisson' operation")
            downsample = rs.GetInteger(
                message = "Downsample",
                number = downsample,
            )
            if (downsample == None):
                return 1
            normalsNeighbours = rs.GetInteger(
                message = "NormalsNeighbours",
                number = normalsNeighbours,
            )
            if (normalsNeighbours == None):
                return 1
            poisonMaxDepth = rs.GetInteger(
                message = "PoisonMaxDepth",
                number = poisonMaxDepth,
            )
            if (poisonMaxDepth == None):
                return 1
            poisonMinDepth = rs.GetInteger(
                message = "PoisonMinDepth",
                number = poisonMinDepth,
            )
            if (poisonMinDepth == None):
                return 1
            poisonScale = rs.GetReal(
                message = "PoisonScale",
                number = poisonScale,
            )
            if (poisonScale == None):
                return 1
            poissonLinear = rs.GetBoolean(
                message="PoissonLinear",
                items = [("PoissonLinear", "False", "True")],
                defaults = poissonLinear,
            )[0]
            if (poissonLinear == None):
                return 1
    
            # Get params :voxel downsample
            Rhino.RhinoApp.WriteLine(
                "Set parameters for the 'Voxel downsample' operation")
            voxelSize = rs.GetReal(
                message = "VoxelSize",
                number = voxelSize,
            )
            if (voxelSize == None):
                return 1
        
        # Get manual DataTree Branch
        strDataTreeBranch = rs.GetString(
            message = "DataTree branch (no space character, hierarchy delimited by '.') e.g. 'Stones.Basalt.Batch42'",
            defaultString = ""
        )
        if (strDataTreeBranch == None):
            return 1
        
        # Prepare CSV
        if (strDataTreeBranch == ""):
            arrDataTreePath = ["","root"]
        else:
            arrDataTreePath = ("root." + strDataTreeBranch).split(".")
        csvRowsDataTree = [["root", ""]]
        for i in range(len(arrDataTreePath) - 1):
            csvRowsDataTree.append([arrDataTreePath[i+1], arrDataTreePath[i]])
            
        parentItem = arrDataTreePath[-1]
        csvObjectRows = []
        
        # Copy static files to the catalogue dir
        pathCatalogueExporter = os.path.dirname(os.path.realpath(__file__)) + "\\"
        pathWebRoot = pathToExportCatalogue
        copy_tree(pathCatalogueExporter + "static", pathToExportCatalogue)
        
        labels = []

        # Point cloud 1-by-1 labelling
        for idPC in idListPC:

            # Prompt for a label
            if (specifyLabels[0]):
                doc.Objects.UnselectAll()
                doc.Objects.Select(idPC)
                doc.Views.Redraw()
                label = rs.GetString(
                    message = "Give selected item a label",
                    defaultString = ""
                )
                if (label == None):
                    return 1
                labels.append(label)

            else:
                labels.append("")
        
        # Point cloud 1-by-1 processing and exporting
        counter = -1
        for idPC in idListPC:
            counter += 1

            # Generate and set physicalObjectId to point cloud
            objPC = doc.Objects.FindId(idPC)
            physicalObjectId = objPC.Attributes.GetUserString("physicalObjectId")
            if (physicalObjectId == None):
                if (labels[counter] != ""):
                    physicalObjectId = labels[counter] + "_" + str(uuid.uuid4())
                else:
                    physicalObjectId = str(uuid.uuid4())
                objPC.Attributes.SetUserString("physicalObjectId", physicalObjectId)
            
            # Original point cloud info
            doc.Objects.UnselectAll()
            doc.Objects.Select(idPC)
            Rhino.RhinoApp.RunScript("Cockroach_Properties", True)
            pcNbOfPoints = Rhino.RhinoApp.CommandHistoryWindowText.splitlines()[-4][28:]
            
            # Mesh Poisson
            objMostRecent = doc.Objects.MostRecentObject()
            doc.Objects.UnselectAll()
            doc.Objects.Select(idPC)
            Rhino.RhinoApp.RunScript(
                "Cockroach_MeshPoisson"
                + " Downsample="
                + str(downsample)
                + " NormalsNeighbours="
                + str(normalsNeighbours)
                + " PoisonMaxDepth="
                + str(poisonMaxDepth)
                + " PoisonMinDepth="
                + str(poisonMinDepth)
                + " PoisonScale="
                + str(poisonScale)
                + " PoisonLinear="
                + str(poissonLinear)
                + " -Enter"
                + " -Enter"
                + " -Cancel", True
            )
            objListLastCreated = doc.Objects.AllObjectsSince(
                objMostRecent.RuntimeSerialNumber)
            objmesh = None
            meshVolume = 0
            for item in objListLastCreated:
                if(item.ObjectType != Rhino.DocObjects.ObjectType.Mesh):
                    doc.Objects.Delete(item, True)
                else:
                    item.Attributes.SetUserString("physicalObjectId", physicalObjectId)
                    objMesh = item
                    meshVolume = item.Geometry.Volume()
                    
            # Point cloud voxel downsample
            doc.Objects.UnselectAll()
            doc.Objects.Select(idPC)
            Rhino.RhinoApp.RunScript(
                "Cockroach_VoxelDownsample"
                + " VoxelSize="
                + str(voxelSize)
                + " -Enter", True
            )
            objPCDownsampled = doc.Objects.MostRecentObject()
            objPCDownsampled.Attributes.SetUserString(
                "physicalObjectId", physicalObjectId)

            # Minimal BBox computation
            minBBoxVol = MinBBox.CombinedMinBB([idPC])
            objMinBBox = doc.Objects.MostRecentObject()
            objMinBBox.Attributes.SetUserString(
                "physicalObjectId", physicalObjectId)

            # Arrange in layers
            objectSuffix = [
                "PointCloud",
                "Mesh",
                "PointCloud_Downsampled",
                "MinBBox"
            ]
            idList = [
                idPC,
                objMesh.Id,
                objPCDownsampled.Id,
                objMinBBox.Id
            ]
            for i in range(len(idList)):
                newLayer = Rhino.DocObjects.Layer()
                newLayer.Name = objectSuffix[i]
                doc.Layers.Add(newLayer)
                obj = doc.Objects.Find(idList[i])
                obj.Attributes.LayerIndex = doc.Layers.FindName(
                    objectSuffix[i]).Index
                obj.CommitChanges()

        # Exports

            # Geometries export
            path3dm = pathWebRoot + "data\\3dm\\"
            if(not os.path.exists(path3dm)):
                os.makedirs(path3dm)

            for i in range(len(idList)):
                doc.Objects.UnselectAll()
                doc.Objects.Select(idList[i])
                Rhino.RhinoApp.RunScript(
                    "-Export \"" + path3dm
                    + physicalObjectId
                    + "_" + objectSuffix[i]
                    + ".3dm\" -Enter", True)

            # Iris export
            pathIris = pathWebRoot + "data\\iris\\"
            pathIrisData = pathIris + "data\\"
            if(not os.path.exists(pathIrisData)):
                os.makedirs(pathIrisData)

            doc.Objects.UnselectAll()
            doc.Objects.Select.Overloads[IEnumerable[System.Guid]](
                [idPC, objMesh.Id, objPCDownsampled.Id, objMinBBox.Id])
            pathIrisDataJson = pathIrisData + physicalObjectId + ".json"
            Rhino.RhinoApp.RunScript(
                "-Export \"" + pathIrisDataJson + "\" -Enter", True)

            irisJson = ""
            with open(pathIrisDataJson) as f:
                irisJson = f.read()
            os.remove(pathIrisDataJson)
            irisJs = "var irisdata = " + irisJson
            with open(pathIrisData + physicalObjectId + ".js", "w") as f:
                f.write(irisJs)

            irisHtml = ""
            with open(pathCatalogueExporter + "iris\\templates\\" + "templateUi.html") as f:
                irisHtml = f.read()
            irisHtml = irisHtml.replace("physicalObjectId", physicalObjectId)
            with open(pathIris + physicalObjectId + ".html", "w") as f:
                f.write(irisHtml)
            
            now = datetime.datetime.now()
            date_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")
            
            # Build CSV row      ["item",           "parent",  "label",         "original_point_cloud_count", "minimal_bounding_box_volume", "mesh_volume", "date_created", "user"            ]
            csvObjectRows.append([physicalObjectId, parentItem, labels[counter], pcNbOfPoints               ,  minBBoxVol                  ,  meshVolume  ,  date_time,      getpass.getuser()])
        
        # Write CSV
        csv_header = ["item", "parent", "label", "original_point_cloud_count", "minimal_bounding_box_volume", "mesh_volume", "date_created", "user"]
        
        fullCsvDataTree = [csv_header] + csvRowsDataTree + csvObjectRows
        
        csvOldRows = []
        try:
            with open(pathWebRoot + "data\\database.csv", "r") as csv_file:
                csv_reader = csv.reader(csv_file)
                for row in csv_reader:
                    csvOldRows.append(row)
        except:
            pass
            
        with open(pathWebRoot + "data\\database.csv", "wb") as csv_file:
            if (len(csvOldRows) > 0):
                for rowO in csvOldRows:
                    appendOld = True
                    for rowN in  fullCsvDataTree:
                        if (rowO[0] == rowN[0]):
                            appendOld = False
                    if (appendOld):
                        fullCsvDataTree.append(rowO)
            
            
#            for newRow in fullCsvDataTree:
#                for i in range(len(csvOldRows)):
#                    if (newRow[0] == csvOldRows[i][0]):
#                        csvOldRows.pop(i)
#                csvOldRows.append(newRow)
            
            csv_writer = csv.writer(csv_file)
            for row in fullCsvDataTree:
                csv_writer.writerow(row)
        
        return 0

    catalogueProcessing()

    # you can optionally return a value from this function
    # to signify command result. Return values that make
    # sense are
    #   0 == success
    #   1 == cancel
    # If this function does not return a value, success is assumed
    


# RunCommand(True)