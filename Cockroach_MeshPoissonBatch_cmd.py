import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import scriptcontext

__commandname__ = "Cockroach_MeshPoissonBatch"

def RunCommand(is_interactive):

    doc = sc.doc.ActiveDoc

    # get point clouds
    pcGUIDList = rs.GetObjects(
        message = "Select point clouds to mesh",
        filter = 2,
        preselect = True,
        minimum_count = 1,
    )

    rs.UnselectAllObjects()

    if pcGUIDList != None:
        
        # get params
        downsample = rs.GetInteger(
            message = "Downsample",
            number = 0,
        )
        normalsNeighbours = rs.GetInteger(
            message = "NormalsNeighbours",
            number = 30,
        )
        poisonMaxDepth = rs.GetInteger(
            message = "PoisonMaxDepth",
            number = 10,
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
        
        for pcGUID in pcGUIDList:
            objMostRecent = doc.Objects.MostRecentObject()
            doc.Objects.UnselectAll()
            doc.Objects.Select(pcGUID)
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
            for item in objListLastCreated:
                if(item.ObjectType != Rhino.DocObjects.ObjectType.Mesh):
                    doc.Objects.Delete(item, True)
