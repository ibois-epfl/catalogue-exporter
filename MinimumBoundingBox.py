"""Combined 2D and 3D "fast" minimum bounding box calculator.
Accepts points, pointclouds, curves, surfaces, breps, extrusions, meshes.
Checks first for single object planarity or multi-object coplanarity.
User options for standard/fine sampling and intermediate result reporting
(3D BB only)

If planar/coplanar:
- Launches 2D planar bounding rectangle routine
- Finds a minimum bounding rectangle relative to a plane for a set of objects.
- Finds smallest area rectangle in plane first to 1 degree, then refines by 1/90
- continues looping with smaller increments until area no longer decreases. (tol)

If non planar/coplanar:
- Launches 3D bounding box routine
- Gets initial rough bounding box/plane: checks every 9 or 5 degrees in all 3 axes
- uses plane from previous check as start point for smaller refinements
- continues refnement stages until bounding box area no longer decreases. (tol)

Script by Mitch Heynick 23.06.18  Release version 1"""

import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino, math, time
import Rhino.DocObjects.ObjectType as OT

#get input objects plus settings
def GetObjectsPlus3Boolean(prompt,b_prompts,b_opts,g_filt=None):
    go = Rhino.Input.Custom.GetObject()
    go.SetCommandPrompt(prompt)
    blnOption0=Rhino.Input.Custom.OptionToggle(*b_opts[0])
    blnOption1=Rhino.Input.Custom.OptionToggle(*b_opts[1])
    blnOption2=Rhino.Input.Custom.OptionToggle(*b_opts[2])
    go.AddOptionToggle(b_prompts[0],blnOption0)
    go.AddOptionToggle(b_prompts[1],blnOption1)
    go.AddOptionToggle(b_prompts[2],blnOption2)
    #allow preselected object
    go.EnablePreSelect(True,True)
    #main object type filter
    if g_filt: go.GeometryFilter=g_filt
    while True:
        get_rc = go.GetMultiple(1,0)
        if get_rc==Rhino.Input.GetResult.Cancel: return
        if get_rc==Rhino.Input.GetResult.Object:
            objs=go.Objects()
            break
        elif get_rc==Rhino.Input.GetResult.Option:
            continue
    a=blnOption0.CurrentValue
    b=blnOption1.CurrentValue
    c=blnOption2.CurrentValue
    return (objs,a,b,c)

#multi-object planarity/coplanarity check function
def CheckObjCoPlanarity(objs,tol=sc.doc.ModelAbsoluteTolerance):
    #accepts points, pointclouds, curves, surfaces, breps and meshes
    #try to "short-circuit" out if any curve or brep element is not planar
    pt_list=[]
    for obj in objs:
        if isinstance(obj,Rhino.Geometry.Point3d):
            pt_list.append(obj)
        elif isinstance(obj,Rhino.Geometry.Point):
            pt_list.append(obj.Location)
        elif isinstance(obj,Rhino.Geometry.PointCloud):
            pt_list.extend(obj.GetPoints())
        elif isinstance(obj,Rhino.Geometry.Curve):
            rc,plane=obj.TryGetPlane(tol)
            if not rc: return
            nc = obj.ToNurbsCurve()
            if nc is None: return
            crv_pts=[nc.Points[i].Location for i in xrange(nc.Points.Count)]
            pt_list.extend(crv_pts)
        elif isinstance(obj,Rhino.Geometry.Brep):
            for face in obj.Faces:
                rc,plane=face.TryGetPlane(tol)
                if not rc: return
                srf=face.ToNurbsSurface()
                if not srf: return
                for cp in srf.Points: pt_list.append(cp.Location)
        elif isinstance(obj,Rhino.Geometry.Surface):
            rc,plane=obj.TryGetPlane(tol)
            if not rc: return
            srf=obj.ToNurbsSurface()
            if not srf: return
            for cp in srf.Points: pt_list.append(cp.Location)
        elif isinstance(obj,Rhino.Geometry.Extrusion):
            rc,plane=obj.TryGetPlane(tol)
            if not rc: return
            srf=face.ToNurbsSurface()
            if not srf: return
            for cp in srf.Points: pt_list.append(cp.Location)
        elif isinstance(obj,Rhino.Geometry.Mesh):
            verts=obj.Vertices
            for vert in obj.Vertices: pt_list.append(Rhino.Geometry.Point3d(vert))
        else:
            return
    if Rhino.Geometry.Point3d.ArePointsCoplanar(pt_list,tol):
        rc, plane = Rhino.Geometry.Plane.FitPlaneToPoints(pt_list)
        if rc==Rhino.Geometry.PlaneFitResult.Success: return plane

#gets a plane-aligned bounding box
def BoundingBoxPlane(objs,plane,ret_pts=False,accurate=True):
    """returns a plane-aligned bounding box in world coordinates
       - input geometry must be RhinoCommon geometry (not IDs)
       - adapted from python rhinoscriptsyntax rs.BoundingBox() code."""
    wxy_plane=Rhino.Geometry.Plane.WorldXY
    def __objectbbox(geom,xform):
        if isinstance(geom,Rhino.Geometry.Point):
            pt=geom.Location
            if xform: pt = xform * pt
            return Rhino.Geometry.BoundingBox(pt,pt)
        if xform: return geom.GetBoundingBox(xform)
        return geom.GetBoundingBox(accurate)
    
    xform = Rhino.Geometry.Transform.ChangeBasis(wxy_plane, plane)
    bbox = Rhino.Geometry.BoundingBox.Empty
    if type(objs) is list or type(objs) is tuple:
        for obj in objs:
            objectbbox = __objectbbox(obj, xform)
            bbox = Rhino.Geometry.BoundingBox.Union(bbox,objectbbox)
    else:
        objectbbox = __objectbbox(objs, xform)
        bbox = Rhino.Geometry.BoundingBox.Union(bbox,objectbbox)
    if not bbox.IsValid: return
    plane_to_world = Rhino.Geometry.Transform.ChangeBasis(plane,wxy_plane)
    if ret_pts:
        corners = list(bbox.GetCorners())
        for pt in corners: pt.Transform(plane_to_world)
        return corners
    else:
        box=Rhino.Geometry.Box(bbox)
        box.Transform(plane_to_world)
        return box

#used in initial 3D bb calculation
def RotateCopyPlanes(tot_ang,count,init_planes,dir_vec):
    """takes a single plane or list of planes as input
    rotates/copies planes through angle tot_ang
    number of planes=count, number of angle divisions=count-1"""
    if isinstance(init_planes,Rhino.Geometry.Plane): init_planes=[init_planes]
    inc=tot_ang/(count-1)
    origin=Rhino.Geometry.Point3d(0,0,0)
    planes=[]
    objs=[]
    for i in range(count):
        for init_plane in init_planes:
            new_plane=Rhino.Geometry.Plane(init_plane)
            new_plane.Rotate(inc*i,dir_vec,origin)
            planes.append(new_plane)
    return planes

#used in initial 3D bb calculation
def GenerateOctantPlanes(count):
    tot_ang=math.pi*0.5 #90 degrees
    #generates an array of count^3 planes in 3 axes covering xyz positive octant
    yz_plane=Rhino.Geometry.Plane.WorldYZ
    dir_vec=Rhino.Geometry.Vector3d(1,0,0) #X axis
    x_planes=RotateCopyPlanes(tot_ang,count,yz_plane,dir_vec)
    dir_vec=Rhino.Geometry.Vector3d(0,-1,0) #-Y axis
    xy_planes=RotateCopyPlanes(tot_ang,count,x_planes,dir_vec)
    dir_vec=Rhino.Geometry.Vector3d(0,0,1) #Z axis
    xyz_planes=RotateCopyPlanes(tot_ang,count,xy_planes,dir_vec)
    return xyz_planes

#used in 3D refinement calculation
def RotatedPlaneArray(plane,tot_ang,divs,axis):
    """creates an array of planes rotated in increments around an axis
    tot_ang=total array inc. angle (rads); divided into divs number of divisions
    included angle is interval from -tot_ang/2 to +tot_ang/2
    number of output planes is divs; number of angle divisions is divs-1 """
    out_planes=[]
    plane.Rotate(-tot_ang*0.5,axis)
    out_planes.append(Rhino.Geometry.Plane(plane))
    inc=tot_ang/(divs-1)
    for i in range(divs-1):
        plane.Rotate(inc,axis)
        out_planes.append(Rhino.Geometry.Plane(plane))
    return out_planes

#used in 3D refinement calculation 
def RotatePlaneArray3D(view_plane,tot_ang,divs):
    #generate a 3D array of refinement planes (works with narrow angles)
    out_planes=[]
    #use RotatedPlaneArray to generate 'horizontal' left-right array (yaw)
    yaw_planes=RotatedPlaneArray(view_plane,tot_ang,divs,view_plane.ZAxis)
    for y_plane in yaw_planes:
        #use RotatedPlaneArray to generate side-to-side 'tilt' array (roll)
        roll_planes=RotatedPlaneArray(y_plane,tot_ang,divs,y_plane.YAxis)
        for r_plane in roll_planes:
            #use RotatedPlaneArray to generate up-down 'tilt' array (pitch)
            pitch_planes=RotatedPlaneArray(r_plane,tot_ang,divs,r_plane.XAxis)
            for p_plane in pitch_planes:
                out_planes.append(p_plane)
    return out_planes

#this is the main 3D bb calculation search function
def MinBBPlane(objs,best_plane,planes,curr_box,curr_vol):
    """returns plane with smallest aligned bounding box volume
    from list of input objects, planes to test and initial compare volume
    best plane, volume, and bbox pass through if no better solution found"""
    for plane in planes:
        bb=BoundingBoxPlane(objs,plane,ret_pts=False)
        if bb.Volume<curr_vol:
            curr_vol=bb.Volume
            best_plane=plane
            curr_box=bb
    return best_plane,curr_box,curr_vol

#3D (non-planar) bounding box routine
def Min3DBoundingBox(objs,init_plane,count,rel_stop,im_rep):
    #for non-planar or non-coplanar object(s)
    #get initial fast bb in init plane (World XY), plus volume to compare
    curr_bb=BoundingBoxPlane(objs,init_plane,False)
    curr_vol=curr_bb.Volume
    
    tot_ang=math.pi*0.5 #90 degrees for intial octant
    factor=0.1 #angle reduction factor for each successive refinement pass
    max_passes=20 #safety factor
    prec=sc.doc.ModelDistanceDisplayPrecision
    us=rs.UnitSystemName(abbreviate=True)
    
    #run intitial bb calculation
    xyz_planes=GenerateOctantPlanes(count)
    best_plane,curr_bb,curr_vol=MinBBPlane(objs,init_plane,xyz_planes,curr_bb,curr_vol)
    #report results of intial rough calculation
#    if im_rep:
#        print "Initial pass 0, volume: {} {}3".format(round(curr_vol,prec),us)
    #refine with smaller angles around best fit plane, loop until...
    for i in range(max_passes):
        prev_vol=curr_vol
        #reduce angle by factor, use refinement planes to generate array
        tot_ang*=factor
        ref_planes=RotatePlaneArray3D(best_plane,tot_ang,count)
        best_plane,curr_bb,curr_vol=MinBBPlane(objs,best_plane,ref_planes,curr_bb,curr_vol)
        vol_diff=prev_vol-curr_vol #vol. diff. over last pass, should be positive or 0
        #print "Volume difference from last pass: {}".format(vol_diff) #debug
        #check if difference is less than minimum "significant"
        #rel_stop==True: relative stop value <.01% difference from previous
        if rel_stop:
            if vol_diff<0.0001*prev_vol: break
        else:
            if vol_diff<sc.doc.ModelAbsoluteTolerance: break
#        Rhino.RhinoApp.Wait()
#        if im_rep:
#            print "Refine pass {}, volume: {} {}3".format(i+1,round(curr_vol,prec),us)
        #get out of loop if escape is pressed
        if sc.escape_test(False):
#            print "Refinement aborted after {} passes.".format(i+1)
            break
            
    return curr_bb,curr_vol,i+1

#this is the main 2D bb calculation search function
def PlanarMinBB(objs,plane,tot_ang,divs):
    inc=tot_ang/divs
    #rotate plane half total angle minus direction
    plane.Rotate(-tot_ang*0.5,plane.ZAxis,plane.Origin)
    bb = BoundingBoxPlane(objs,plane)
    curr_plane=Rhino.Geometry.Plane(plane)
    curr_area=BoxArea(bb)
    #loop through angle increments
    for i in range(divs):
        plane.Rotate(inc,plane.ZAxis,plane.Origin)
        bb = BoundingBoxPlane(objs,plane)
        new_area=BoxArea(bb)
        if new_area<curr_area:
            #print curr_area #debug
            #print new_area #debug
            curr_area=new_area
            curr_plane=Rhino.Geometry.Plane(plane)
    return curr_plane, curr_area

#2D planar bounding rectangle routine
def MinBoundingRectanglePlane(objs,curr_plane,im_rep=False):
    #pass True argument above if you want to print intermediate results
    #initialize
    factor=0.01 #0.01 (1/100 of model abs tolerance)
    angle=math.pi*0.5 #start angle 90 degrees
    divs=90  #initial division 1 degree intervals
    tol = sc.doc.ModelAbsoluteTolerance
    err_msg="Unable to calculate bounding box area"
    st=time.time()
    
    #get initial rough bounding box
    init_bb=BoundingBoxPlane(objs,curr_plane,ret_pts=False)
    curr_area=BoxArea(init_bb)
#    if im_rep: 
#        print "Initial area: {}".format(curr_area)
    
    #main calculation loop
    safe=10 #set safety limit at 10
    for i in range(safe):
        curr_plane,new_area = PlanarMinBB(objs,curr_plane,angle,divs)
        #abort if area is 0 or extremely small
#        if new_area<tol*0.1:
#            print err_msg ; return
        #break out of loop if new area is the same as prev. area within limit
        if abs(curr_area-new_area)<factor*tol: break
        #otherwise, decrease increments and loop
        curr_area=new_area
        angle*=(1/divs)
#        if im_rep:
#            print "Refine stage {} Area: {}".format(i+1,curr_area)
#            Rhino.RhinoApp.Wait() #wait for command line to print...
#        if i==10:
#            print "Max loop limit reached" #debug
        
    f_bb=BoundingBoxPlane(objs,curr_plane,ret_pts=True)
    return f_bb,curr_area,i

#used for planar bounding rectangle calculation
def BoxArea(box):
    return (box.X[1]-box.X[0])*(box.Y[1]-box.Y[0])

def CombinedMinBB(objIDs, fine_sample = False, rel_stop = False, im_rep = False):
    #user input
    #get prev settings
    if "MinBBSample" in sc.sticky: u_samp = sc.sticky["MinBBSample"]
    else: u_samp = False #standard sampling
    if "MinBBStop" in sc.sticky: u_stop = sc.sticky["MinBBStop"]
    else: u_stop = True #relative volume stop value
    if "MinBBReports" in sc.sticky: u_rep = sc.sticky["MinBBReports"]
    else: u_rep = True #intermediate reports shown
    
    prec=sc.doc.ModelDistanceDisplayPrecision
    us=rs.UnitSystemName(abbreviate=True)
    
    # prompt="Select objects for minimum bounding box"
    # gf=OT.Point|OT.PointSet|OT.Curve|OT.Surface|OT.Extrusion|OT.Brep|OT.Mesh
    # bool_prompts=["Sampling","StopVal","ReportIntermedResults"]
    # bool_ini=[[u_samp,"Standard","Fine"],[u_stop,"Absolute","Relative"],[u_rep,"No","Yes"]]
    # result=GetObjectsPlus3Boolean(prompt,bool_prompts,bool_ini,gf)
    # if result is None: return
    # objIDs,fine_sample,rel_stop,im_rep=result


    
    #objIDs=rs.GetObjects(preselect=True)
    #if not objIDs: return
    objs=[rs.coercegeometry(objID) for objID in objIDs]
#    print "Checking object planarity/coplanarity..."
    st=time.time()
    plane=CheckObjCoPlanarity(objs,tol=sc.doc.ModelAbsoluteTolerance)
    
    if plane:
        if len(objs)==1: msg="Selected object is planar - "
        else: msg="All selected objects are coplanar - "
        msg+="launching 2D planar bounding rectangle calculation."
#        print msg
        #launch planar bounding box routine
        f_bb,curr_area,passes=MinBoundingRectanglePlane(objs,plane,im_rep)
        #add polyline, report message
        bbID=rs.AddPolyline([f_bb[0],f_bb[1],f_bb[2],f_bb[3],f_bb[0]])
        fa=round(curr_area,prec)
        msg="{} refinement stages. ".format(passes)
        msg+="Minimum bounding box area = {} sq. {}".format(fa,us)
        msg+=" Elapsed time: {:.2f} sec.".format(time.time()-st)
        
    else:
        #standard sample count=10 --> 1000 boxes per pass
        #fine sample count=18 --> 5832 boxes per pass
        if fine_sample: count=18
        else: count=10
        wxy_plane=Rhino.Geometry.Plane.WorldXY
        if len(objs)==1: cp_msg="Selected object is not planar - "
        else: cp_msg="Selected objects are not coplanar - "
        cp_msg+="launching 3D bounding box calculation."
#        print cp_msg
        rs.Prompt("Calculating... please wait.")
        #launch 3D bounding box routine
        curr_bb,curr_vol,passes=Min3DBoundingBox(objs,wxy_plane,count,rel_stop,im_rep)
        
        #add box, report message
        if Rhino.RhinoApp.ExeVersion<6:
            sc.doc.Objects.AddBrep(curr_bb.ToBrep()) #legacy
        else:
            sc.doc.Objects.AddBox(curr_bb)
        fv=round(curr_vol,prec)
        msg="Final volume after {} passes is {} {}3".format(passes,fv,us)
        msg+=" | Elapsed time: {:.2f} sec.".format(time.time()-st)
        
    #final result reporting
#    print msg
    sc.doc.Views.Redraw()
    #save user settings
    sc.sticky["MinBBSample"] = fine_sample
    sc.sticky["MinBBReports"] = im_rep
    sc.sticky["MinBBStop"] = rel_stop
    return curr_vol