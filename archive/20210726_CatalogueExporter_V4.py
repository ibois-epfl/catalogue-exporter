import os
from distutils.dir_util import copy_tree 
import System
import System.Collections.Generic.IEnumerable as IEnumerable
import math, time
import uuid
import Rhino
import scriptcontext as sc
import rhinoscriptsyntax as rs
import MinimumBoundingBox as MinBBox

doc = sc.doc.ActiveDoc

def catalogueProcessing():
    
    # Get point clouds GUID list
    gPC = Rhino.Input.Custom.GetObject()
    gPC.SetCommandPrompt("Select point clouds")
    gPC.GeometryFilter = Rhino.DocObjects.ObjectType.PointSet
    gPC.GetMultiple(1,0)
    if gPC.CommandResult()!=Rhino.Commands.Result.Success:
        return gPC.CommandResult()
    idListPC = [gPC.Object(i).ObjectId for i in range(gPC.ObjectCount)]
    doc.Objects.UnselectAll()
    
    # Get params: mesh Poisson
    Rhino.RhinoApp.WriteLine("Set parameters for the 'Mesh Poisson' operation")
    downsample = rs.GetInteger(
        message = "Downsample",
        number = 1000,
    )
    normalsNeighbours = rs.GetInteger(
        message = "NormalsNeighbours",
        number = 30,
    )
    poisonMaxDepth = rs.GetInteger(
        message = "PoisonMaxDepth",
        number = 6,
    )
    poisonMinDepth = rs.GetInteger(
        message = "PoisonMinDepth",
        number = 0,
    )
    poisonScale = rs.GetReal(
        message = "PoisonScale",
        number = 1.1,
    )
    poissonLinear = rs.GetBoolean(
        message="PoissonLinear",
        items = [("PoissonLinear", "False", "True")],
        defaults = [False],
    )[0]
    
    # Get params :voxel downsample
    Rhino.RhinoApp.WriteLine("Set parameters for the 'Voxel downsample' operation")
    voxelSize = rs.GetReal(
        message = "VoxelSize",
        number = 0.002,
    )
    
    # Copy static files to the catalogue dir
    pathCatalogueExporter = os.path.dirname(os.path.realpath(__file__)) + "\\"
    pathCurrent3dmFileDir = doc.Path[:-len(doc.Name)]
    pathWebRoot = pathCurrent3dmFileDir + "catalogue\\"
    copy_tree(pathCatalogueExporter + "static", pathCurrent3dmFileDir)

    
    # Point cloud 1-by-1 processing
    for idPC in idListPC:
        
        # Generate and set physicalObjectId to point cloud
        objPC = doc.Objects.FindId(idPC)
        physicalObjectId = str(uuid.uuid4())
        objPC.Attributes.SetUserString("physicalObjectId", physicalObjectId)
        
        # Mesh Poisson
        objMostRecent = doc.Objects.MostRecentObject()
        doc.Objects.UnselectAll()
        doc.Objects.Select(idPC)
        Rhino.RhinoApp.RunScript(
            "Cockroach_MeshPoisson"
            +" Downsample="
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
            + " -Cancel"
            , True
        )
        objListLastCreated = doc.Objects.AllObjectsSince(objMostRecent.RuntimeSerialNumber)
        objmesh = None
        for item in objListLastCreated:
            if(item.ObjectType != Rhino.DocObjects.ObjectType.Mesh):
                doc.Objects.Delete(item, True)
            else:
                item.Attributes.SetUserString("physicalObjectId", physicalObjectId)
                objMesh = item
        
        # Point cloud voxel downsample
        doc.Objects.UnselectAll()
        doc.Objects.Select(idPC)
        Rhino.RhinoApp.RunScript(
            "Cockroach_VoxelDownsample"
            +" VoxelSize="
            + str(voxelSize)
            + " -Enter"
            , True
        )
        objPCDownsampled = doc.Objects.MostRecentObject()
        objPCDownsampled.Attributes.SetUserString("physicalObjectId", physicalObjectId)
        
        # Minimal BBox computation
        MinBBox.CombinedMinBB([idPC])
        objMinBBox = doc.Objects.MostRecentObject()
        arrayCrvMinBBoxWireFrame = objMinBBox.Geometry.GetWireframe()
        for crv in arrayCrvMinBBoxWireFrame:
            doc.Objects.Find(crv.Id).Attributes.SetUserString("physicalObjectId", physicalObjectId)
        arrayIdMinBBoxWireFrame = [crv.Id for crv in arrayCrvMinBBoxWireFrame]
        objMinBBoxWireFrame = doc.Objects.Find(crvMinBBoxWireFrame.Id)
        doc.Objects.Delete(objMinBBox, True)
        objMinBBoxWireFrame.Attributes.SetUserString("physicalObjectId", physicalObjectId)
        
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
        for i in range(len(idList)) :
            newLayer = Rhino.DocObjects.Layer()
            newLayer.Name = objectSuffix[i]
            doc.Layers.Add(newLayer)
            obj = doc.Objects.Find(idList[i])
            obj.Attributes.LayerIndex = doc.Layers.FindName(objectSuffix[i]).Index
            obj.CommitChanges()
        
        # Exports
        
        # Geometries export
        path3dm = pathWebRoot + "3dm\\"
        if(not os.path.exists(path3dm)):
            os.makedirs(path3dm)
            
        for i in range(len(idList)) :
            doc.Objects.UnselectAll()
            doc.Objects.Select(idList[i])
            Rhino.RhinoApp.RunScript(
                "-Export \"" + path3dm
                + physicalObjectId
                + "_" + objectSuffix[i]
                + ".3dm\" -Enter", True)
        
        # Iris export
        pathIris = pathWebRoot + "iris\\"
        pathIrisData = pathIris + "data\\"
        if(not os.path.exists(pathIrisData)):
            os.makedirs(pathIrisData)
        
        doc.Objects.UnselectAll()
        doc.Objects.Select.Overloads[IEnumerable[System.Guid]]([idPC, objMesh.Id, objPCDownsampled.Id, objMinBBox.Id])
        pathIrisDataJson = pathIrisData + physicalObjectId + ".json"
        Rhino.RhinoApp.RunScript("-Export \"" + pathIrisDataJson + "\" -Enter", True)
        
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
        
        # Build JSON

catalogueProcessing()