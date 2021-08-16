import rhinoscriptsyntax as rs
import Rhino

__commandname__ = "Cockroach_ComputeNormalsBatch"

def RunCommand(is_interactive):

    pcGUIDList = rs.GetObjects(
        message = "Select point clouds to compute the normals of",
        filter = 2, # Point cloud
        preselect = True
    )

    normalsNeighbours = rs.GetReal(
        message = "NormalsNeighbours"
    )

    for pcGUID in pcGUIDList:
        rs.SelectObject(pcGUID)
        rs.Command("Cockroach_ComputePointCloudNormals NormalsNeighbours " + str(normalsNeighbours) + " Enter")
        print(str(pcGUID) + " normals computed")