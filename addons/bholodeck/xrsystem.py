#####################################################################################################################
# Copyright(C) 2011-2023 IT4Innovations National Supercomputing Center, VSB - Technical University of Ostrava
#
# This program is free software : you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#####################################################################################################################

import bpy
import mathutils
from . import bholodeck_pref
import os

from mathutils import Euler, Matrix, Quaternion, Vector

controller_type_items = [
    ("HTC", "HTC Vive Controller", ""),
    ("VALVE", "Valve Index Controller", ""),
    ("ACER", "Windows Mixed Reality (ACER)", ""),
]

avatar_type_items = [
    ("NONE", "None", ""),
]

class VIEW_PG_XRSystem(bpy.types.PropertyGroup):
    controller_type : bpy.props.EnumProperty(name="Controller Type", items=controller_type_items)
    avatar_type : bpy.props.EnumProperty(name="Avatar Type", items=avatar_type_items)

class XRSystemStart(bpy.types.Operator):
    bl_idname = "xrsystem.start"
    bl_label = "Start"
   
    def execute(self,context):
        context.scene.xrsystem.init(context) 

        return {'FINISHED'}

class XRSystemStop(bpy.types.Operator):
    bl_idname = "xrsystem.stop"
    bl_label = "Stop"
   
    def execute(self,context):
        context.scene.xrsystem.deinit(context)

        return {'FINISHED'}

def get_viewer_pose_matrix(context):
    wm = context.window_manager

    loc = wm.xr_session_state.viewer_pose_location
    rot = wm.xr_session_state.viewer_pose_rotation

    rotmat = Matrix.Identity(3)
    rotmat.rotate(rot)
    rotmat.resize_4x4()
    transmat = Matrix.Translation(loc)

    return transmat @ rotmat

def get_body_pose_matrix(context):
    wm = context.window_manager

    loc = wm.xr_session_state.viewer_pose_location
    rot = wm.xr_session_state.viewer_pose_rotation
    
    rotQ = Quaternion(Vector(rot))
    rotQ[1] = 0
    rotQ[2] = 0

    rotmat = Matrix.Identity(3)
    rotmat.rotate(rotQ)
    rotmat.resize_4x4()
    transmat = Matrix.Translation(loc)

    return transmat @ rotmat    

def get_controller_pose_matrix(context, idx, is_grip, scale):
    wm = context.window_manager

    loc = None
    rot = None
    if is_grip:
        loc = wm.xr_session_state.controller_grip_location_get(context, idx)
        rot = wm.xr_session_state.controller_grip_rotation_get(context, idx)
    else:
        loc = wm.xr_session_state.controller_aim_location_get(context, idx)
        rot = wm.xr_session_state.controller_aim_rotation_get(context, idx)

    rotmat = Matrix.Identity(3)
    rotmat.rotate(Quaternion(Vector(rot)))
    rotmat.resize_4x4()
    transmat = Matrix.Translation(loc)
    scalemat = Matrix.Scale(scale, 4)

    return transmat @ rotmat @ scalemat    

class VIEW_PT_XRPanel(bpy.types.Panel):
    bl_label = "XRSystem"
    bl_idname = "VIEW_PT_XRPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BHolodeck"
    
    def draw(self, context):
        layout = self.layout
        pref = bholodeck_pref.preferences()       

        #if pref.is_client():
        row = layout.row()
        row.prop(context.scene.view_pg_xrsystem, "controller_type")

        # row = layout.row()
        # row.prop(context.scene.view_pg_xrsystem, "avatar_type")

        row = layout.row()
        if context.scene.xrsystem.enabled == False:
            row.operator("xrsystem.start", text = "Start")
        else:
            row.operator("xrsystem.stop", text = "Stop")


class XRSYSTEM_OT_sync_xr_timer(bpy.types.Operator):
    bl_idname = "xrsystem.sync_xr_timer"
    bl_label = "XR Timer"

    def execute(self, context):
        self._timer = context.window_manager.event_timer_add(0, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self._timer = context.window_manager.event_timer_add(0, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}    

    def modal(self, context, event):
        # Check for XR action event.
        if not event.type == 'TIMER' or not context.window_manager.xr_session_state:
            return {'PASS_THROUGH'}

        # Finish when button is released.
        if context.scene.xrsystem.enabled == False:
            context.window_manager.event_timer_remove(self._timer)
            return {'FINISHED'}

        context.scene.xrsystem.sync_xr_timer(context)
        #print(event.type)

        return {'RUNNING_MODAL'}   

class XRSystem:
    def __init__(self):
        self.enabled = False
        #self.collection_lib_name = 'XRLibrary'
        self.collection_user_name = 'XRUsers'

        self.vr_landmark_z = mathutils.Vector((0,0,0))
        #self.line_coords = [(0,0,-0.1), (-5,0,-10)]
        self.line_coords = [(0,0,-0.13), (0,0,-13)]

        self.selected_object = None

        #[Vector((-0.05, -0.02, -0.08)), Vector((-0.36, -0.28, -0.46))]

        # temp_start = mathutils.Vector((-0.014244, -0.028966, -0.081782))
        # temp_stop = mathutils.Vector((-0.015575, -0.035258, -0.088866))
        # temp_vec = (temp_stop - temp_start) * 1000.0
        # temp_stop = temp_start + temp_vec

        # self.line_coords = [temp_start, temp_stop]
        #print(self.line_coords)

        self.HMD = 'HMD'
        self.HMD_EMPTY = 'HEMPTY'
        self.CONTROLLER = 'CONTROLLER'
        self.BODY = 'BODY'

        self.headset_object = None
        self.body_object = None
        self.controller0_object = None
        self.controller1_object = None        

    def create_collection(self, context, name):
        if name in bpy.data.collections:
            self.remove_collection(context, name)

        col = bpy.data.collections.new(name)
        context.scene.collection.children.link(col)

        return col

    def get_or_create_collection(self, context, name):
        if name in bpy.data.collections:
            return bpy.data.collections[name]

        col = bpy.data.collections.new(name)
        context.scene.collection.children.link(col)

        return col        

    def remove_collection(self, context, name):
        coll = bpy.data.collections.get(name)

        if coll:
            #if remove_collection_objects:
            obs = [o for o in coll.objects if o.users == 1]
            while obs:
                bpy.data.objects.remove(obs.pop())

            bpy.data.collections.remove(coll)

    # def load_model(self, context):
    #     xrlib_collection = self.create_collection(context, self.collection_lib_name)

    #     hmd_obj = self.create_model_from_file(context, self.HMD)
    #     xrlib_collection.objects.link(hmd_obj)

    #     controller_obj = self.create_model_from_file(context, self.CONTROLLER)
    #     xrlib_collection.objects.link(controller_obj)

    def sync_xr_timer(self, context):
        # bpy.ops.xrsystem.viewer_pose()
        # bpy.ops.xrsystem.controller_poses()
        #try:
            if self.headset_object:
                self.headset_object.matrix_world = get_viewer_pose_matrix(context)

            if self.body_object:
                self.body_object.matrix_world = get_body_pose_matrix(context)

            if self.controller0_object:
                if context.scene.view_pg_xrsystem.controller_type == "ACER":
                    self.controller0_object.matrix_world = get_controller_pose_matrix(context, 1, True, 1.0)
                else:
                    self.controller0_object.matrix_world = get_controller_pose_matrix(context, 0, True, 1.0)

            if self.controller1_object:
                if context.scene.view_pg_xrsystem.controller_type == "ACER":
                    self.controller1_object.matrix_world = get_controller_pose_matrix(context, 0, True, 1.0)
                else:
                    self.controller1_object.matrix_world = get_controller_pose_matrix(context, 1, True, 1.0)
        #except:
        #    pass

    def deinit(self, context):
        if self.xr_session_is_running(context):
            bpy.ops.wm.xr_session_toggle()    

        #bpy.app.timers.unregister(sync_xr_timer)    

        self.enabled = False

        return

    def get_or_create_model(self, context, name):
        if name in bpy.data.objects:
            obj = bpy.data.objects[name]
        else:
            #obj = self.dupli_model_from_library(context, name)
            obj = self.create_model_from_file(context, name)

        return obj

    def set_position(self, context, name, location, rotation):
        obj = self.get_or_create_model(context, name)
        #obj = self.create_model_from_file(context, ops_ctx, name)
        obj.location = location                                 
        obj.rotation_quaternion = rotation #.to_euler()  

        return obj

    def hide_line(self, context, name, hide):
        line_name = name + '_LINE'
        if line_name in bpy.data.objects:
            obj = bpy.data.objects[line_name]
            obj.hide_set(hide)

    def create_line(self, context, line_name):
        # sample data
        #coords = [(0,0.005,-0.13), (0,0.5,-13)]
        #coords = [(0,0,-0.1), (0,0,0)]
        coords = self.line_coords

        # create the Curve Datablock
        curveData = bpy.data.curves.new(line_name, type='CURVE')
        curveData.dimensions = '3D'
        curveData.resolution_u = 1
        #curveData.extrude = 0.003
        #curveData.extrude = 0.01
        curveData.offset = 0.0
        curveData.extrude = 0.0
        curveData.bevel_depth = 0.001
        curveData.bevel_resolution = 0
        curveData.use_fill_caps = True

        # map coords to spline
        polyline = curveData.splines.new('POLY')
        polyline.use_smooth=False
        polyline.points.add(len(coords)-1)
        for i, coord in enumerate(coords):
            x,y,z = coord
            polyline.points[i].co = (x, y, z, 1)

        # create Object
        curveOB = bpy.data.objects.new(line_name, curveData)

        # attach to scene and validate context
        xruser_collection = self.get_or_create_collection(context, self.collection_user_name)
        xruser_collection.objects.link(curveOB)

        curveOB.hide_set(True)

        return curveOB                

    def create_model_from_file(self, context, name):
        scene = context.scene
        scripts_dir = bpy.utils.user_resource('SCRIPTS')
        library_blend_file = os.path.join(scripts_dir, 'addons/bholodeck/library.blend')
        section = 'Object'

        if self.HMD in name:
            object_name = self.HMD

            if context.scene.view_pg_xrsystem.avatar_type != "NONE":
                object_name = context.scene.view_pg_xrsystem.avatar_type + '_' + self.HMD

        elif self.BODY in name:
            object_name = self.BODY

            if context.scene.view_pg_xrsystem.avatar_type != "NONE":
                object_name = context.scene.view_pg_xrsystem.avatar_type + '_' + self.BODY                

        elif self.HMD_EMPTY in name:
            object_name = self.HMD_EMPTY

        elif self.CONTROLLER in name:
            object_name = context.scene.view_pg_xrsystem.controller_type + '_' + self.CONTROLLER

            if context.scene.view_pg_xrsystem.avatar_type != "NONE":
                c0 = self.CONTROLLER + '0'
                c1 = self.CONTROLLER + '1'

                if c0 in name:
                    object_name = context.scene.view_pg_xrsystem.avatar_type + '_' + c0
                elif c1 in name:
                    object_name = context.scene.view_pg_xrsystem.avatar_type + '_' + c1

        else:
            raise Exception('unknown model')        

        filepath  = os.path.join(library_blend_file, section, object_name)        
        filename  = object_name
        directory = os.path.join(library_blend_file, section)

        self.get_or_create_collection(context, self.collection_user_name)
        context.view_layer.active_layer_collection = context.view_layer.layer_collection.children[self.collection_user_name]

        bpy.ops.wm.append(filepath=filepath, filename=filename, directory=directory)

        obj = bpy.data.objects[object_name] 
        obj.name = name
        obj.rotation_mode = 'QUATERNION'

        #xruser_collection = self.get_or_create_collection(context, self.collection_user_name)
        #xruser_collection.objects.link(obj)

        if self.CONTROLLER in name:
            line = self.create_line(context, name + '_LINE')
            line.parent = obj

        return obj

    # def dupli_model_from_library(self, context, name):
    #     if self.HMD in name:
    #         object_name = self.HMD

    #     elif self.CONTROLLER in name:
    #         object_name = self.CONTROLLER
        
    #     else:
    #         raise Exception('unknown model')        

    #     obj = bpy.data.objects[object_name] # Informa objeto à def
    #     obj_dupli = obj.copy()
    #     obj_dupli.name = name

    #     xruser_collection = self.get_or_create_collection(context, self.collection_user_name)
    #     xruser_collection.objects.link(obj_dupli)

    #     return obj_dupli        

    def xr_session_is_running(self, context):
        return bpy.types.XrSessionState.is_running(context)

    def click(self, context):
        wm = context.window_manager
        if wm.xr_session_state:
            xR = wm.xr_session_state.get_action_state(context, 'bholodeck', 'trackpad_x', '/user/hand/right')
            yR = wm.xr_session_state.get_action_state(context, 'bholodeck', 'trackpad_y', '/user/hand/right')

            xL = wm.xr_session_state.get_action_state(context, 'bholodeck', 'trackpad_x', '/user/hand/left')
            yL = wm.xr_session_state.get_action_state(context, 'bholodeck', 'trackpad_y', '/user/hand/left')

            return xR,yR,xL,yL

        return None, None

    def init(self, context):
        #self.load_model(context)

        self.action_set_init(context, context.scene)
        self.vr_landmark_init(context, context.scene)

        # stop if running
        if self.xr_session_is_running(context):
            bpy.ops.wm.xr_session_toggle()

        bpy.ops.wm.xr_session_toggle()

        #bpy.app.timers.register(sync_xr_timer, persistent=True)        

        self.enabled = True

        bpy.ops.xrsystem.sync_xr_timer()

        return

    def get_hmd_position(self, context):
        xr_session_state = bpy.context.window_manager.xr_session_state

        if xr_session_state is None:
            return mathutils.Vector((0,0,0)), mathutils.Vector((0,0,0,0))

        return xr_session_state.viewer_pose_location, xr_session_state.viewer_pose_rotation

        #return get_viewer_pose_matrix(context)

    def get_body_position(self, context):
        xr_session_state = bpy.context.window_manager.xr_session_state

        if xr_session_state is None:
            return mathutils.Vector((0,0,0)), mathutils.Vector((0,0,0,0))

        loc = xr_session_state.viewer_pose_location
        rot = xr_session_state.viewer_pose_rotation
        
        rotQ = Quaternion(Vector(rot))
        rotQ[1] = 0
        rotQ[2] = 0            

        return loc, rotQ
        #return get_viewer_pose_matrix(context)

    def get_controller0_position(self, context):
        xr_session_state = bpy.context.window_manager.xr_session_state

        if xr_session_state is None:
            return mathutils.Vector((0,0,0)), mathutils.Vector((0,0,0,0))

        return xr_session_state.controller_grip_location_get(context, 0), xr_session_state.controller_grip_rotation_get(context, 0)

    def get_controller1_position(self, context):
        xr_session_state = bpy.context.window_manager.xr_session_state

        if xr_session_state is None:
            return mathutils.Vector((0,0,0)), mathutils.Vector((0,0,0,0))

        #return xr_session_state.controller_pose1_location, xr_session_state.controller_pose1_rotation     
        return xr_session_state.controller_grip_location_get(context, 1), xr_session_state.controller_grip_rotation_get(context, 1)

    def update(self, context):     
        return

    def action_set_init(self, context, scene):
        #models
        pref = bholodeck_pref.preferences()
        objH = self.get_or_create_model(context, pref.username + "_HEMPTY")
        objB = self.get_or_create_model(context, pref.username + "_BODY")
        objC0 = self.get_or_create_model(context, pref.username + "_CONTROLLER0")
        objC1 = self.get_or_create_model(context, pref.username + "_CONTROLLER1")

        objH.rotation_mode = 'XYZ'
        objB.rotation_mode = 'XYZ'
        objC0.rotation_mode = 'XYZ'
        objC1.rotation_mode = 'XYZ'       

        #context.window_manager.xr_session_settings.headset_object = objH
        #context.window_manager.xr_session_settings.controller0_object = objC0
        ##context.window_manager.xr_session_settings.controller1_object = objC1

        self.headset_object = objH
        self.body_object = objB
        self.controller0_object = objC0
        self.controller1_object = objC1        

        #context.window_manager.xr_session_settings.headset_object_enable = True
        #context.window_manager.xr_session_settings.controller0_object_enable = True
        ##context.window_manager.xr_session_settings.controller1_object_enable = True

        context.window_manager.xr_session_settings.show_selection = True
        context.window_manager.xr_session_settings.use_positional_tracking = True
        context.window_manager.xr_session_settings.use_absolute_tracking = True
        context.window_manager.xr_session_settings.show_controllers = False

    def vr_landmark_init(self, context, scene):

        if len(scene.vr_landmarks) == 0:
            scene.vr_landmarks.add()

        vr_landmark = scene.vr_landmarks[0]
        vr_landmark.name = 'bholodeck'
        vr_landmark.type = 'CUSTOM'

        vr_landmark.base_pose_location = self.vr_landmark_z
        if context.scene.view_pg_xrsystem.controller_type == "ACER":
            vr_landmark.base_pose_location[2] = 1.5
        vr_landmark.base_pose_angle = 0

        # if context.scene.netsystem.enabled == True:
        #     vr_landmark.base_pose_location = context.scene.netsystem.current_netclient.landmark_location
        #     vr_landmark.base_pose_angle = context.scene.netsystem.current_netclient.landmark_angle
        
        scene.vr_landmarks_active = 0
        scene.vr_landmarks_selected = 0  

    def vr_landmark_set(self, context, loc):

        if len(context.scene.vr_landmarks) == 0:
            return

        vr_landmark = context.scene.vr_landmarks[0]
        if vr_landmark.name != 'bholodeck':
            return

        vr_landmark.base_pose_location = mathutils.Vector(loc) + vr_landmark.base_pose_location
        vr_landmark.base_pose_location[2] = 0

        if context.scene.view_pg_xrsystem.controller_type == "ACER":
            vr_landmark.base_pose_location[2] = 1.5

def register():
    """register."""

    bpy.utils.register_class(XRSystemStart)    
    bpy.utils.register_class(XRSystemStop)
    bpy.utils.register_class(VIEW_PT_XRPanel)
    bpy.utils.register_class(XRSYSTEM_OT_sync_xr_timer)
    bpy.utils.register_class(VIEW_PG_XRSystem)

    bpy.types.Scene.view_pg_xrsystem = bpy.props.PointerProperty(type=VIEW_PG_XRSystem)
           
    bpy.types.Scene.xrsystem = XRSystem()  

def unregister():
    """unregister."""

    bpy.utils.unregister_class(VIEW_PT_XRPanel)
    bpy.utils.unregister_class(XRSystemStop)
    bpy.utils.unregister_class(XRSystemStart)

    bpy.utils.unregister_class(VIEW_PG_XRSystem)
    bpy.utils.unregister_class(XRSYSTEM_OT_sync_xr_timer)

    delattr(bpy.types.Scene, "view_pg_xrsystem") 
    delattr(bpy.types.Scene, "xrsystem") 
