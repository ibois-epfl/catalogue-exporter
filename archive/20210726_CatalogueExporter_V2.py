import os
import System
import System.Collections.Generic.IEnumerable as IEnumerable
import math, time
import uuid
import Rhino
import scriptcontext as sc
import rhinoscriptsyntax as rs
doc = sc.doc.ActiveDoc
import MinimumBoundingBox as MinBBox



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
        number = 100000,
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
        objMinBBox.Attributes.SetUserString("physicalObjectId", physicalObjectId)
        
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
        pathWebRoot = doc.Path[:-len(doc.Name)] + "catalogue\\"
        
        

        # Geometries export
        if(not os.path.exists(pathWebRoot + "geodata\\")):
            os.makedirs(pathWebRoot + "geodata\\")
        for i in range(len(idList)) :
            doc.Objects.UnselectAll()
            doc.Objects.Select(idList[i])
            Rhino.RhinoApp.RunScript(
                "-Export \"" + pathWebRoot + "geodata\\"
                + physicalObjectId
                + "_" + objectSuffix[i]
                + ".3dm\" -Enter", True)
        
        # Iris export
        doc.Objects.UnselectAll()
        doc.Objects.Select.Overloads[IEnumerable[System.Guid]]([idPC, objMesh.Id, objPCDownsampled.Id, objMinBBox.Id])
        irisJsonPath = doc.Path[:-len(doc.Name)] + physicalObjectId + ".json"
        Rhino.RhinoApp.RunScript("-Export \"" + irisJsonPath + "\" -Enter", True)
        irisJson = ""
        with open(irisJsonPath) as f:
            irisJson = f.read()
        os.remove(irisJsonPath)
        irisJs = "var irisdata = " + irisJson
        if(not os.path.exists(pathWebRoot + "irisdata\\")):
            os.makedirs(pathWebRoot + "irisdata\\")
        with open(pathWebRoot + "irisdata\\" + physicalObjectId + ".js", "w") as f:
            f.write(irisJs)
        
        # Build JSON

catalogueProcessing()