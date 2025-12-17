#####################################################################################################################
# Copyright(C) 2023-2026 IT4Innovations National Supercomputing Center, VSB - Technical University of Ostrava
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
from bpy.types import NodeTree, Node, NodeSocket

from pathlib import Path

import mathutils
import math
import bmesh
import sys
import os

#from bpy import context
from mathutils import Vector

vrmenu_type_items = [
    ("FLOAT", "Float", ""),
    ("SCRIPT", "Script", ""),
]

class VRMenuTree(NodeTree):
    bl_idname = 'VRMenuTreeType'
    bl_label = 'VRMenu Node Tree'
    bl_icon = 'NODETREE'

class VRMenuSocketIn(NodeSocket):
    bl_idname = 'VRMenuSocketIn'
    bl_label = 'Menu'

    # Optional function for drawing the socket input value
    def draw(self, context, layout, node, text):
        layout.label(text=text)

    # Socket color
    def draw_color(self, context, node):
        return (1.0, 0.0, 0.0, 1.0)

# VRMenu socket type
class VRMenuSocketOut(NodeSocket):
    # Description string
    '''VRMenu node socket'''
    # Optional identifier string. If not explicitly defined, the python class name is used.
    bl_idname = 'VRMenuSocketOut'
    # Label for nice name display
    bl_label = 'Menu'

    name : bpy.props.StringProperty(name="Name")
    #command = bpy.props.StringProperty(name="Command")

    # Optional function for drawing the socket input value
    def draw(self, context, layout, node, text):
        #layout.label(text=text)
        #row = layout.row()
        #row.prop(self, "command")
        #row.prop(self, "name")
        layout.prop(self, "name", text="")       

    # Socket color
    def draw_color(self, context, node):
        return (0.0, 1.0, 0.0, 1.0)


class VRMenuTreeNode:
    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == 'VRMenuTreeType'

def update_input(self, context):
    self.update_input(context)

def update_output(self, context):
    self.update_output(context)       

# Derived from the Node base type.
class VRMenuNodeMenu(Node, VRMenuTreeNode):
    bl_idname = 'VRMenuNodeMenu'
    bl_label = 'VRMenu Node'
    bl_icon = 'MENU_PANEL'

    outputCountProperty : bpy.props.IntProperty(default=1, update=update_output, min=0, max=16, name="Items")
    active_item : bpy.props.IntProperty(name="Item")

    def init(self, context):
        self.inputs.new('VRMenuSocketIn', "Menu")

        self.outputCountProperty = 1
        self.update_output(context)

    def update_output(self, context):
        self.outputs.clear() 

        for i in range(self.outputCountProperty):
            out = self.outputs.new('VRMenuSocketOut', "Menu")
            #out.link_limit = 1

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.prop(self, "outputCountProperty")
        row = layout.row()
        row.enabled=False
        row.prop(self, "active_item", text="")

    def draw_label(self):
        return "Menu"


class VRMenuNodeRoot(Node, VRMenuTreeNode):
    # === Basics ===
    # Description string
    '''A Root node'''
    # Optional identifier string. If not explicitly defined, the python class name is used.
    bl_idname = 'VRMenuNodeRoot'
    # Label for nice name display
    bl_label = 'ROOT'
    # Icon identifier
    bl_icon = 'MENU_PANEL'

    active_node : bpy.props.StringProperty(name="Menu")
    #active_node : bpy.props.PointerProperty()
    #active_item : bpy.props.IntProperty(name="Item")
    
    def init(self, context):
        out = self.outputs.new('VRMenuSocketOut', "Menu")
        out.name = 'ROOT'

    def draw_buttons(self, context, layout):
        box = layout.box()
        box.enabled=False
        box.label(text="Active")
        box.prop(self, "active_node", text="")
        #box.prop(self, "active_item", text="")        

    def draw_label(self):
        return "Root"

def update_command(self, context):
    self.update_command(context)  

class VRMenuNodeFloat(Node, VRMenuTreeNode):
    # === Basics ===
    # Description string
    '''A Value node'''
    # Optional identifier string. If not explicitly defined, the python class name is used.
    bl_idname = 'VRMenuNodeFloat'
    # Label for nice name display
    bl_label = 'VRValue Node'
    # Icon identifier
    bl_icon = 'MENU_PANEL'

    # === VRMenu Properties ===
    #name : bpy.props.StringProperty(name="Name")
    #type : bpy.props.EnumProperty(name="Type", items=vrmenu_type_items)

    command : bpy.props.StringProperty(name="Command", update=update_command)
    command_hint : bpy.props.StringProperty(name="Hint")
    command_float_min : bpy.props.FloatProperty(name="Command Min")
    command_float_max : bpy.props.FloatProperty(name="Command Max")
    command_float_step : bpy.props.FloatProperty(name="Command Step")
    #command_count : bpy.props.IntProperty(name="Command Count")
    #text_block : bpy.props.PointerProperty(type = bpy.types.Text)

    # === Optional Functions ===
    # Initialization function, called when a new node is created.
    # This is the most common place to create the sockets for a node, as shown below.
    # NOTE: this is not the same as the standard __init__ function in Python, which is
    #       a purely internal Python method and unknown to the node system!
    def init(self, context):
        self.inputs.new('VRMenuSocketIn', "Menu")

        #self.inputCountProperty = 1
        #self.outputCountProperty = 1

        #self.update_input(context)
        #self.update_output(context)

    def update_command(self, context):
        try:
            try:
                command_count = eval('len(%s)' % self.command)
            except:
                command_count = 0

            if command_count > 0:
                self.command_hint = str(eval('type(%s[0])' % self.command)) + ', count: %d' % command_count
            else:
                self.command_hint = str(eval('type(%s)' % self.command))
        except:
            self.command_hint = "Unknown"

    # Additional buttons displayed on the node.
    def draw_buttons(self, context, layout):
        #layout.prop(self, "inputCountProperty")
        layout.prop(self, "name")

        layout.prop(self, "command")

        row = layout.row()
        row.enabled = False
        row.prop(self, "command_hint")

        row = layout.row()
        row.prop(self, "command_float_min")
        row.prop(self, "command_float_step")
        row.prop(self, "command_float_max")



    # Detail buttons in the sidebar.
    # If this function is not defined, the draw_buttons function is used instead
    # def draw_buttons_ext(self, context, layout):
    #     layout.prop(self, "myFloatProperty")
    #     # myStringProperty button will only be visible in the sidebar
    #     layout.prop(self, "myStringProperty")

    # Optional: custom label
    # Explicit user label overrides this, but here we can define a label dynamically
    def draw_label(self):
        return "Float"

class VRMenuNodeScript(Node, VRMenuTreeNode):
    # === Basics ===
    # Description string
    '''A Value node'''
    # Optional identifier string. If not explicitly defined, the python class name is used.
    bl_idname = 'VRMenuNodeScript'
    # Label for nice name display
    bl_label = 'VRScript Node'
    # Icon identifier
    bl_icon = 'MENU_PANEL'

    # === VRMenu Properties ===
    text_block : bpy.props.PointerProperty(type = bpy.types.Text)

    # === Optional Functions ===
    # Initialization function, called when a new node is created.
    # This is the most common place to create the sockets for a node, as shown below.
    # NOTE: this is not the same as the standard __init__ function in Python, which is
    #       a purely internal Python method and unknown to the node system!
    def init(self, context):
        self.inputs.new('VRMenuSocketIn', "Menu")

    # Additional buttons displayed on the node.
    def draw_buttons(self, context, layout):
        #layout.prop(self, "inputCountProperty")
        layout.prop(self, "name")
        layout.prop(self, "text_block")


    # Detail buttons in the sidebar.
    # If this function is not defined, the draw_buttons function is used instead
    # def draw_buttons_ext(self, context, layout):
    #     layout.prop(self, "myFloatProperty")
    #     # myStringProperty button will only be visible in the sidebar
    #     layout.prop(self, "myStringProperty")

    # Optional: custom label
    # Explicit user label overrides this, but here we can define a label dynamically
    def draw_label(self):
        return "Script"



### Node Categories ###
# Node categories are a python system for automatically
# extending the Add menu, toolbar panels and search operator.
# For more examples see release/scripts/startup/nodeitems_builtins.py

import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem


# our own base class with an appropriate poll function,
# so the categories only show up in our own tree type
class VRMenuNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'VRMenuTreeType'

# all categories in a list
node_categories = [
    # identifier, label, items list
    VRMenuNodeCategory("VRMENUNODES", "VR Nodes", items=[
        # our basic node
        NodeItem("VRMenuNodeRoot"),
        NodeItem("VRMenuNodeMenu"),
        NodeItem("VRMenuNodeScript"),
        NodeItem("VRMenuNodeFloat"),
        ]),
    # VRMenuNodeCategory("OTHERNODES", "Other Nodes", items=[
    #     # the node item can have additional settings,
    #     # which are applied to new nodes
    #     # NB: settings values are stored as string expressions,
    #     # for this reason they should be converted to strings using repr()
    #     NodeItem("VRMenuNodeType", label="Node A", settings={
    #         "myStringProperty": repr("Lorem ipsum dolor sit amet"),
    #         "myFloatProperty": repr(1.0),
    #         }),
    #     NodeItem("VRMenuNodeType", label="Node B", settings={
    #         "myStringProperty": repr("consectetur adipisicing elit"),
    #         "myFloatProperty": repr(2.0),
    #         }),
    #     ]),
    ]

class VRMenuNodes:
    def __init__(self):
        self.collection_name = 'VRMenu'
        self.item_w = 0.165
        self.item_h = self.item_w / 3.3

        self.item_image_w = int(1000)
        self.item_image_h = int(self.item_image_w / 3.3)

        self.item_image_color = (33, 33, 33, 255)

        self.item_font_size = int(120)
        self.item_font_color = (210, 210, 210, 255)

        self.enabled = False

    def create_collection(self, context, name):
        if name in bpy.data.collections:
            self.remove_collection(context, name)

        menu_collection = bpy.data.collections.new(name)
        context.scene.collection.children.link(menu_collection)

        return menu_collection

    def remove_collection(self, context, name):
        coll = bpy.data.collections.get(name)

        if coll:
            #if remove_collection_objects:
            obs = [o for o in coll.objects if o.users == 1]
            while obs:
                bpy.data.objects.remove(obs.pop())

            bpy.data.collections.remove(coll)

    def create_plane(self, context, name, x_min, y_min, x_max, y_max):

        # obj = context.object
        # coordinates = [obj.matrix_world @ v.co for v in obj.data.vertices]

        # x_list = [co.x for co in coordinates]
        # y_list = [co.y for co in coordinates]

        # x_min, x_max = min(x_list), max(x_list)
        # y_min, y_max = min(y_list), max(y_list)

        # verts = ((x_min, y_min, 0),(x_min, y_max, 0),
        #         (x_max, y_max, 0),(x_max, y_min,0))

        verts = ((x_min, 0, -y_min),(x_min, 0, -y_max),
                (x_max, 0, -y_max),(x_max, 0, -y_min))

        bm = bmesh.new()
        [bm.verts.new((v[0], v[1], v[2])) for v in verts]
        bm.faces.new(bm.verts)

        bm.normal_update()

        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)

        uvlayer = me.uv_layers.new() # default naem and do_init
        me.uv_layers.active = uvlayer

        uvlayer.data[0].uv = Vector((0,0))
        uvlayer.data[1].uv = Vector((0,1))
        uvlayer.data[2].uv = Vector((1,1))
        uvlayer.data[3].uv = Vector((1,0))

        plane = bpy.data.objects.new(name, me)
        #bpy.context.scene.collection.objects.link(plane)

        return plane


    def create_menu_item(self, context, name, menu_collection, tex_path, location_z, only_text):
        #bpy.ops.mesh.primitive_plane_add()
        plane = self.create_plane(context, name, -self.item_w / 2, -self.item_h / 2 - location_z, self.item_w / 2, self.item_h / 2 - location_z)
        #plane.name = name
        #plane.location = location
        plane.rotation_mode = 'QUATERNION'

        from PIL import Image, ImageDraw, ImageFont
        ##############################################
        tex_filename = str(Path(bpy.path.abspath(tex_path)) / (name + '.png'))

        #img = Image.new('RGB', (self.item_image_w, self.item_image_h), color = (33, 33, 33))
        img = Image.new('RGBA', (self.item_image_w, self.item_image_h), color = self.item_image_color)

        scripts_dir = bpy.utils.user_resource('SCRIPTS')
        font_file = os.path.join(scripts_dir, 'addons/bholodeck/bmonofont-i18n.ttf')

        #font_file = Path(sys.path[0]) / '..' / '..' / 'datafiles' / 'fonts' / 'bmonofont-i18n.ttf'
        font = ImageFont.truetype(str(font_file), self.item_font_size)
        bbox = font.getbbox(name)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        
        d = ImageDraw.Draw(img)
        d.text(((self.item_image_w - w) / 2, (self.item_image_h - h) / 2), name, font=font, fill=self.item_font_color)
        if not only_text:
            d.polygon([(self.item_image_w - self.item_font_size / 2, self.item_image_h / 2 + self.item_font_size / 4), (self.item_image_w - self.item_font_size / 2, self.item_image_h / 2 - self.item_font_size / 4), (self.item_image_w - self.item_font_size / 4, self.item_image_h / 2)], fill=(217,217,217,255))
        img.save(tex_filename)       
        
        #bmat = self.create_bmat(context, name, str(tex_filename))
        #plane.data.materials.append(bmat)   
        bmat = self.create_menu_bmat(context, name, tex_filename)
        plane.data.materials.append(bmat)     
        plane.data.materials.append(bmat)
        ##############################################
        if not only_text:        
            name_selected = name + '_selected'
            tex_filename_selected = str(Path(bpy.path.abspath(tex_path)) / (name_selected + '.png'))

            img_selected = Image.new('RGB', (self.item_image_w, self.item_image_h), color = (81, 119, 179))

            #font_file_selected = Path(sys.path[0]) / '..' / '..' / 'datafiles' / 'fonts' / 'bmonofont-i18n.ttf'
            font_selected = ImageFont.truetype(str(font_file), self.item_font_size)
            bbox = font.getbbox(name)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            
            d_selected = ImageDraw.Draw(img_selected)
            d_selected.text(((self.item_image_w - w) / 2, (self.item_image_h - h) / 2), name, font=font_selected, fill=(217,217,217,255))
            d_selected.polygon([(self.item_image_w - self.item_font_size / 2, self.item_image_h / 2 + self.item_font_size / 4), (self.item_image_w - self.item_font_size / 2, self.item_image_h / 2 - self.item_font_size / 4), (self.item_image_w - self.item_font_size / 4, self.item_image_h / 2)], fill=(217,217,217,255))
            img_selected.save(tex_filename_selected)

            bmat_selected = self.create_menu_bmat(context, name_selected, tex_filename_selected)
            plane.data.materials.append(bmat_selected)     
        #else:
        #    tex_filename_selected = None   

        # bmat = self.create_menu_bmat(context, name, tex_filename, tex_filename_selected)
        # plane.data.materials.append(bmat)
        plane.active_material = plane.data.materials[1]

        ##############################################


        menu_collection.objects.link(plane)          

        return plane

    def create_script_item(self, context, name, menu_collection, tex_path, location_z):
        #bpy.ops.mesh.primitive_plane_add()
        #plane = self.create_plane(context, name, -self.item_w / 2, -self.item_h / 2, self.item_w / 2, self.item_h / 2)
        plane = self.create_plane(context, name, -self.item_w / 2, -self.item_h / 2 - location_z, self.item_w / 2, self.item_h / 2 - location_z)
        #plane.name = name
        #plane.location = location

        from PIL import Image, ImageDraw, ImageFont
        ##############################################
        tex_filename = str(Path(bpy.path.abspath(tex_path)) / (name + '.png'))

        img = Image.new('RGB', (self.item_image_w, self.item_image_h), color = (81, 119, 179))

        scripts_dir = bpy.utils.user_resource('SCRIPTS')
        font_file = os.path.join(scripts_dir, 'addons/bholodeck/bmonofont-i18n.ttf')
        font = ImageFont.truetype(str(font_file), self.item_font_size)
        bbox = font.getbbox(name)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        
        d = ImageDraw.Draw(img)
        d.text(((self.item_image_w - w) / 2, (self.item_image_h - h) / 2), name, font=font, fill=(217,217,217,255))
        img.save(tex_filename)       
        
        #tex_filename_selected = None   

        bmat = self.create_menu_bmat(context, name, tex_filename)
        plane.data.materials.append(bmat)

        ##############################################


        menu_collection.objects.link(plane)          

        return plane

    def create_value_item(self, context, name, menu_collection, tex_path, location_z):
        #bpy.ops.mesh.primitive_plane_add()
        #plane = self.create_plane(context, name, -self.item_w / 2, -self.item_h / 2, self.item_w / 2, self.item_h / 2)
        plane = self.create_plane(context, name, -self.item_w / 2, -self.item_h / 2 - location_z, self.item_w / 2, self.item_h / 2 - location_z)
        #plane.name = name
        #plane.location = location

        ##############################################
        bmat = self.create_value_bmat(context, name)
        plane.data.materials.append(bmat)

        ##############################################

        menu_collection.objects.link(plane)          

        return plane

    def get_world_vectors(self, origin, direction, matrix_from):

        matrix_from_copy = matrix_from.copy()
        matrix_from_copy[0][3] = 0
        matrix_from_copy[1][3] = 0
        matrix_from_copy[2][3] = 0

        point_world = matrix_from @ origin
        dir_world = matrix_from_copy @ direction

        return (point_world, dir_world)  

    def deselect_all(self, context):
        for ob in context.selected_objects:
            ob.select_set(False)                      

    def ray_cast_scene(self, context, controller_obj, controller):
        # Create an initial origin vector, or rather the point from where the ray will be cast
        origin = mathutils.Vector(context.scene.xrsystem.line_coords[0])

        # Create an initial direction vector, it should be facing the projection plane 
        # and the corresponding axis from the front to the back of the projection screen is -z,
        # that is why the vector has -1 in the third column.
        direction = mathutils.Vector(context.scene.xrsystem.line_coords[1]) - mathutils.Vector(context.scene.xrsystem.line_coords[0])

        if controller_obj:        
            matrix_from = controller_obj.matrix_world
        else:
            if controller == 0:
                if context.scene.view_pg_xrsystem.controller_type == "ACER":
                    matrix_from = context.scene.xrsystem.get_controller_pose_matrix(context, 1, True, 1.0)
                else:
                    matrix_from = context.scene.xrsystem.get_controller_pose_matrix(context, 0, True, 1.0)

            if controller == 1:
                if context.scene.view_pg_xrsystem.controller_type == "ACER":
                    matrix_from = context.scene.xrsystem.get_controller_pose_matrix(context, 0, True, 1.0)
                else:
                    matrix_from = context.scene.xrsystem.get_controller_pose_matrix(context, 1, True, 1.0)            
        
        # Returns origin and direction vectors represented in the world space
        point_world, dir_world = self.get_world_vectors(origin, direction, matrix_from)

        depsgraph = context.evaluated_depsgraph_get()
        hit, loc, norm, index, obj, mat = context.scene.ray_cast(depsgraph, point_world, dir_world)

        # if hit:
        #     self.coords = [computed_vectors[0], loc]
        #     self.object_in_track = True
            
        # else: 
        #     self.coords = [computed_vectors[0], computed_vectors[1] * 100]
        #     self.object_in_track = False
       
        # self.ball.raycast_intersection.hide_viewport = True
        
        # if self.object_grabbed:
        #     self.active_object.location = self.right_controller.location() + self.active_object_location
        
        return hit, loc, obj, point_world, norm        

    def select_plane(self, context, id):
        if id < 0:
            id = 0

        if id > len(self.planes) - 1:
            id = len(self.planes) - 1            

        for plane in self.planes:
        #    plane.data.materials[0].node_tree.nodes['Mix Shader'].inputs[0].default_value = 0
            plane.active_material = plane.data.materials[1]

        #self.planes[id].data.materials[0].node_tree.nodes['Mix Shader'].inputs[0].default_value = 1
        self.planes[id].active_material = self.planes[id].data.materials[2]
        #self.selected_plane_id = id
        root_node = self.get_root_node(context)
        if root_node is None:
            return

        current_node = self.get_node(context, root_node.active_node)
        current_node.active_item = id

    def up(self, context):
        root_node = self.get_root_node(context)
        if root_node is None:
            return

        current_node = self.get_node(context, root_node.active_node)

        if current_node.bl_idname == 'VRMenuNodeMenu':
            self.select_plane(context, current_node.active_item - 1)

    def down(self, context):
        root_node = self.get_root_node(context)
        if root_node is None:
            return

        current_node = self.get_node(context, root_node.active_node)

        if current_node.bl_idname == 'VRMenuNodeMenu':
            self.select_plane(context, current_node.active_item + 1)

    def right(self, context):
        root_node = self.get_root_node(context)
        if root_node is None:
            return

        if not self.is_node(context, root_node.active_node):
            self.show(context)
            return

        current_node = self.get_node(context, root_node.active_node)

        if current_node.bl_idname == 'VRMenuNodeMenu':
            right_node = current_node.outputs[current_node.active_item].links[0].to_node

            if right_node.bl_idname == 'VRMenuNodeMenu':
                self.create_menu(context, right_node.name)

            if right_node.bl_idname == 'VRMenuNodeFloat':
                self.create_value_float(context, right_node.name)

            if right_node.bl_idname == 'VRMenuNodeScript':
                self.create_script(context, right_node.name)  

        if current_node.bl_idname == 'VRMenuNodeScript':
            if current_node.text_block:
                txt = context.scene.netsystem.replace_tag_in_script(current_node.text_block.as_string())
                context.scene.netsystem.send_python_script(txt)
                exec(txt)
                self.left(context)

    def click(self, context):
        if context.scene.xrsystem.enabled == True:
            xR,yR,xL,yL = context.scene.xrsystem.click(context) 

            # down -0.12806613743305206 -0.9920899271965027
            if yR < -0.6 or yL < -0.6:
                self.down(context)
            # up -0.006419455632567406 0.845078408718109
            if yR > 0.6 or yL > 0.6:
                self.up(context)
            # left -0.9425885677337646 -0.04341811686754227
            if xR < -0.6 or xL < -0.6:
                self.left(context)
            # right 0.8822823166847229 -0.20674721896648407
            if xR > 0.6 or xL > 0.6:
                self.right(context)

            print("click", xR,yR,xL,yL)     

    def left(self, context):
        root_node = self.get_root_node(context)
        if root_node is None:
            return

        if not self.is_node(context, root_node.active_node):
            self.show(context)
            return

        current_node = self.get_node(context, root_node.active_node)
        left_node = current_node.inputs[0].links[0].from_node

        if left_node.bl_idname == 'VRMenuNodeMenu':
            self.create_menu(context, left_node.name)

    def showhide(self, context):
        if context.scene.vrmenunodes.enabled:
            self.hide(context)
        else:
            self.show(context)

    def trigger0_press(self, context):
        #co0 = context.window_manager.xr_session_settings.controller0_object
        context.scene.xrsystem.controller_active = 0
        co0 = context.scene.xrsystem.controller0_object
        if context.scene.xrsystem.enabled == True:
            if co0:
                context.scene.xrsystem.hide_line(context, co0.name, False) 

    def trigger0_release(self, context):
        context.scene.xrsystem.controller_active = 0

        #co0 = context.window_manager.xr_session_settings.controller0_object
        co0 = context.scene.xrsystem.controller0_object
        if context.scene.xrsystem.enabled == True:
            if co0:
                context.scene.xrsystem.hide_line(context, co0.name, True)

        hit, loc, obj, p, n = self.ray_cast_scene(context, co0, 0)
        if hit == True:
            self.deselect_all(context)
            obj.select_set(True)
            context.view_layer.objects.active = obj
            res = context.scene.vrobjectactionnodes.action(context)
            if res == False:
                context.scene.xrsystem.vr_landmark_set(context, loc - p)

    def trigger1_press(self, context):
        context.scene.xrsystem.controller_active = 1
        # co1 = context.window_manager.xr_session_settings.controller1_object
        # if context.scene.xrsystem.enabled == True:
        #     context.scene.xrsystem.hide_line(context, co1.name, False)
        co1 = context.scene.xrsystem.controller1_object
        if context.scene.xrsystem.enabled == True:
            if co1:
                context.scene.xrsystem.hide_line(context, co1.name, False)  
        pass

    def trigger1_release(self, context):
        context.scene.xrsystem.controller_active = 1
        # co1 = context.window_manager.xr_session_settings.controller1_object
        # if context.scene.xrsystem.enabled == True:
        #     context.scene.xrsystem.hide_line(context, co1.name, True)  

        # hit, loc, obj, p, n = self.ray_cast_scene(context, co1)
        # if hit == True:
        #     self.deselect_all(context)
        #     obj.select_set(True)
        #     context.view_layer.objects.active = obj 
        #     res = context.scene.vrobjectactionnodes.action(context)
        #     if res == False:
        #         context.scene.xrsystem.vr_landmark_set(context, loc - p)
        co1 = context.scene.xrsystem.controller1_object
        if context.scene.xrsystem.enabled == True:
            if co1:
                context.scene.xrsystem.hide_line(context, co1.name, True)

        hit, loc, obj, p, n = self.ray_cast_scene(context, co1, 1)
        if hit == True:
            self.deselect_all(context)
            obj.select_set(True)
            context.view_layer.objects.active = obj
            res = context.scene.vrobjectactionnodes.action(context)
            if res == False:
                context.scene.xrsystem.vr_landmark_set(context, loc - p)
        pass              

    def hide(self, context):
        if self.collection_name in bpy.data.collections:
            self.remove_collection(context, self.collection_name)

        self.enabled = False

    def show(self, context):
        root_node = self.get_root_node(context)
        if root_node is None:
            return

        if self.is_node(context, root_node.active_node):
            active_node_name = root_node.active_node
        else:
            active_node_name = root_node.outputs[0].links[0].to_node.name

        self.create_menu(context, active_node_name)

        self.enabled = True

    def value_float_set(self, context, value):
        root_node = self.get_root_node(context)
        if root_node is None:
            return

        float_node = self.get_node(context, root_node.active_node)

        if float_node.bl_idname == 'VRMenuNodeFloat':
            v_min = float_node.command_float_min
            v_max = float_node.command_float_max

            v = float(value * (v_max - v_min) + v_min)
            exec('%s = %f' % (float_node.command, v))

            self.planes[1].data.materials[0].node_tree.nodes['ColorRamp'].color_ramp.elements[1].position = value

    def value_float_get(self, context):
        root_node = self.get_root_node(context)
        if root_node is None:
            return 0.0

        float_node = self.get_node(context, root_node.active_node)

        if float_node.bl_idname == 'VRMenuNodeFloat':
            v = float(eval(float_node.command))
            v_min = float_node.command_float_min
            v_max = float_node.command_float_max

            if v < v_min:
                v = v_min

            if v > v_max:
                v = v_max

            value = float((v - v_min) / (v_max - v_min))
            self.planes[1].data.materials[0].node_tree.nodes['ColorRamp'].color_ramp.elements[1].position = value
            return value

        return 0.0

    def get_root_node(self, context):
        return self.get_node(context, 'ROOT')

    def get_node(self, context, name):
        if context.scene.view_pg_vrmenu.main_tree is None:
            return None
        
        return context.scene.view_pg_vrmenu.main_tree.nodes[name]      
        
    def is_node(self, context, name):
        if context.scene.view_pg_vrmenu.main_tree is None:
            return False

        return name in context.scene.view_pg_vrmenu.main_tree.nodes


    def create_value_float(self, context, active_node):
        root_node = self.get_root_node(context)
        if root_node is None:
            return

        root_node.active_node = active_node
        value_node = self.get_node(context, active_node)

        menu_collection = self.create_collection(context, self.collection_name)

        location = Vector((0,0,0))
        self.planes = []
        location_z = (0 - 2) * self.item_h
        plane = self.create_menu_item(context, value_node.name, menu_collection, context.scene.view_pg_vrmenu.menu_path, location_z, True)
        location_z = (1 - 2) * self.item_h
        self.planes.append(plane)
        plane = self.create_value_item(context, value_node.name, menu_collection, context.scene.view_pg_vrmenu.menu_path, location_z)
        self.planes.append(plane)

    def create_script(self, context, active_node):
        root_node = self.get_root_node(context)
        if root_node is None:
            return

        root_node.active_node = active_node
        value_node = self.get_node(context, active_node)

        menu_collection = self.create_collection(context, self.collection_name)

        location = Vector((0,0,0))
        self.planes = []
        location_z = (0 - 2) * self.item_h
        plane = self.create_menu_item(context, value_node.name, menu_collection, context.scene.view_pg_vrmenu.menu_path, location_z, True)
        #location[2] = location[2] + self.item_h
        location_z = (1 - 2) * self.item_h
        self.planes.append(plane)
        plane = self.create_script_item(context, 'Run', menu_collection, context.scene.view_pg_vrmenu.menu_path, location_z)
        self.planes.append(plane)

    def set_parent(self, context, obj):
        if len(self.planes) > 0:
            self.planes[0].parent = obj

    def create_menu(self, context, active_node):
        root_node = self.get_root_node(context)
        if root_node is None:
            return
            
        root_node.active_node = active_node
        menu_node = self.get_node(context, active_node)          

        items = []

        for item in menu_node.outputs:
            items.append(item.name)

        menu_collection = self.create_collection(context, self.collection_name)

        location = Vector((0,0,0))
        #location[2] = self.item_h

        self.planes = []

        for i in range(len(items)):
            item_name = items[i]
            #location[2] = (i + 1) * self.item_h
            location_z = (i - len(items)) * self.item_h
            plane = self.create_menu_item(context, item_name, menu_collection, context.scene.view_pg_vrmenu.menu_path, location_z, False)
            self.planes.append(plane)

            if i!=0:
                plane.parent = self.planes[0]

        self.select_plane(context, menu_node.active_item)

    # def bmat_add_texture_selected(self, context, bmat, filename, filename_selected):
    #     principled_node = bmat.node_tree.nodes['Principled BSDF']
    #     bmat.node_tree.nodes.remove(principled_node)

    #     texture_node = bmat.node_tree.nodes.new("ShaderNodeTexImage")
    #     texture_node.location = (-270, 300)
    #     texture_node.image = bpy.data.images.load(filename)

    #     emission_node = bmat.node_tree.nodes.new("ShaderNodeEmission")
    #     emission_node.location = (70, 300)
    #     bmat.node_tree.links.new(texture_node.outputs['Color'], emission_node.inputs['Color'])

    #     texture_node_selected = bmat.node_tree.nodes.new("ShaderNodeTexImage")
    #     texture_node_selected.location = (-270, 0)
    #     texture_node_selected.image = bpy.data.images.load(filename_selected)        

    #     emission_node_selected = bmat.node_tree.nodes.new("ShaderNodeEmission")
    #     emission_node_selected.location = (70, 0)
    #     bmat.node_tree.links.new(texture_node_selected.outputs['Color'], emission_node_selected.inputs['Color'])  

    #     mix_node = bmat.node_tree.nodes.new("ShaderNodeMixShader")
    #     mix_node.location = (70, 160)
    #     mix_node.inputs[0].default_value = 0  

    #     bmat.node_tree.links.new(emission_node.outputs['Emission'], mix_node.inputs[1])
    #     bmat.node_tree.links.new(emission_node_selected.outputs['Emission'], mix_node.inputs[2])                       

    #     output_node = bmat.node_tree.nodes['Material Output']
    #     bmat.node_tree.links.new(mix_node.outputs[0], output_node.inputs['Surface'])

    def bmat_add_texture(self, context, bmat, filename):
        principled_node = bmat.node_tree.nodes['Principled BSDF']
        bmat.node_tree.nodes.remove(principled_node)

        texture_node = bmat.node_tree.nodes.new("ShaderNodeTexImage")
        texture_node.location = (-270, 300)
        texture_node.image = bpy.data.images.load(filename)

        emission_node = bmat.node_tree.nodes.new("ShaderNodeEmission")
        emission_node.location = (70, 300)
        bmat.node_tree.links.new(texture_node.outputs['Color'], emission_node.inputs['Color'])

        output_node = bmat.node_tree.nodes['Material Output']
        bmat.node_tree.links.new(emission_node.outputs[0], output_node.inputs['Surface'])

    def bmat_add_gradient(self, context, bmat):
        principled_node = bmat.node_tree.nodes['Principled BSDF']
        bmat.node_tree.nodes.remove(principled_node)

        gradient_node = bmat.node_tree.nodes.new("ShaderNodeTexGradient")
        gradient_node.location = (-270, 300)

        color_ramp_node = bmat.node_tree.nodes.new("ShaderNodeValToRGB")
        color_ramp_node.location = (-170, 0)
        color_ramp_node.color_ramp.interpolation = 'CONSTANT'
        color_ramp_node.color_ramp.elements[0].color = Vector((81, 119, 179, 255)) / 255.0
        color_ramp_node.color_ramp.elements[0].position = 0
        color_ramp_node.color_ramp.elements[1].color = Vector((33, 33, 33, 255)) / 255.0 
        color_ramp_node.color_ramp.elements[1].position = 0.5       
        bmat.node_tree.links.new(gradient_node.outputs[0], color_ramp_node.inputs[0])

        emission_node = bmat.node_tree.nodes.new("ShaderNodeEmission")
        emission_node.location = (70, 300)
        bmat.node_tree.links.new(color_ramp_node.outputs[0], emission_node.inputs['Color'])

        output_node = bmat.node_tree.nodes['Material Output']
        bmat.node_tree.links.new(emission_node.outputs[0], output_node.inputs['Surface'])

    # def create_menu_bmat(self, context, name, filename, filename_selected):
    #     bmat = bpy.data.materials.new(name)
    #     bmat.use_nodes = True

    #     if filename_selected is None:
    #         self.bmat_add_texture(context, bmat, filename)
    #     else:
    #         self.bmat_add_texture_selected(context, bmat, filename, filename_selected)

    #     return bmat

    def create_menu_bmat(self, context, name, filename):
        bmat = bpy.data.materials.new(name)
        bmat.use_nodes = True
        self.bmat_add_texture(context, bmat, filename)
        return bmat   
    
    def create_value_bmat(self, context, name):
        bmat = bpy.data.materials.new(name)
        bmat.use_nodes = True

        self.bmat_add_gradient(context, bmat)

        return bmat

class VRMenuNodesShow(bpy.types.Operator):
    bl_idname = "vrmenunodes.show"
    bl_label = "Show Menu"

    def execute(self,context):
        context.scene.vrmenunodes.show(context)

        return {'FINISHED'}

class VRMenuNodesShowHide(bpy.types.Operator):
    bl_idname = "vrmenunodes.showhide"
    bl_label = "ShowHide Menu"

    def execute(self,context):
        context.scene.vrmenunodes.showhide(context)

        return {'FINISHED'}        

class VRMenuNodesHide(bpy.types.Operator):
    bl_idname = "vrmenunodes.hide"
    bl_label = "Hide Menu"

    def execute(self,context):
        context.scene.vrmenunodes.hide(context)

        return {'FINISHED'}

class VRMenuNodesTrackpadEvent(bpy.types.Operator):
    bl_idname = "vrmenunodes.trackpad_event"
    bl_label = "Modal trackpad_event"

    def invoke(self, context, event):
        # Check for XR action event.
        if not event.xr:
            return {'PASS_THROUGH'}

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        # Check for XR action event.
        if not event.xr:
            return {'PASS_THROUGH'}

        # Check for correct VR action.
        # if event.xr.action != VRActions.MODAL.value:
        #     return {'PASS_THROUGH'}

        session = context.window_manager.xr_session_state
        action_state = event.xr.state

        if not context.scene.xrsystem.selected_object is None:            
            context.scene.xrsystem.selected_object.rotation_euler[2] = math.radians(action_state[0] * -90.0)
            #context.scene.xrsystem.selected_object.rotation_euler[0] = math.radians(action_state[1] * -90.0)

        # viewer_rotation = get_viewer_rotation_matrix(session)
        # hor = calc_horizontal_movement(*action_state, viewer_rotation)

        # session.navigation_location += hor

        # Finish when button is released.
        if event.value == 'RELEASE':
            return {'FINISHED'}

        return {'RUNNING_MODAL'}        

class VRMenuNodesTrigger0Press(bpy.types.Operator):
    bl_idname = "vrmenunodes.trigger0_press"
    bl_label = "trigger press"

    def execute(self,context):
        context.scene.vrmenunodes.trigger0_press(context)

        return {'FINISHED'}

class VRMenuNodesTrigger0Release(bpy.types.Operator):
    bl_idname = "vrmenunodes.trigger0_release"
    bl_label = "trigger release"

    def execute(self,context):
        context.scene.vrmenunodes.trigger0_release(context)

        return {'FINISHED'} 

class VRMenuNodesTrigger1Press(bpy.types.Operator):
    bl_idname = "vrmenunodes.trigger1_press"
    bl_label = "trigger press"

    def execute(self,context):
        context.scene.vrmenunodes.trigger1_press(context)

        return {'FINISHED'}

class VRMenuNodesTrigger1Release(bpy.types.Operator):
    bl_idname = "vrmenunodes.trigger1_release"
    bl_label = "trigger release"

    def execute(self,context):
        context.scene.vrmenunodes.trigger1_release(context)

        return {'FINISHED'}                        

class VRMenuNodesUp(bpy.types.Operator):
    bl_idname = "vrmenunodes.up"
    bl_label = "Up Menu"

    def execute(self,context):
        context.scene.vrmenunodes.up(context)

        return {'FINISHED'}

class VRMenuNodesDown(bpy.types.Operator):
    bl_idname = "vrmenunodes.down"
    bl_label = "Down Menu"

    def execute(self,context):
        context.scene.vrmenunodes.down(context)

        return {'FINISHED'}

class VRMenuNodesLeft(bpy.types.Operator):
    bl_idname = "vrmenunodes.left"
    bl_label = "Left Menu"

    def execute(self,context):
        context.scene.vrmenunodes.left(context)

        return {'FINISHED'}

class VRMenuNodesRight(bpy.types.Operator):
    bl_idname = "vrmenunodes.right"
    bl_label = "Right Menu"

    def execute(self,context):
        context.scene.vrmenunodes.right(context)

        return {'FINISHED'}

class VRMenuNodesClick(bpy.types.Operator):
    bl_idname = "vrmenunodes.click"
    bl_label = "Click Menu"

    def execute(self,context):
        context.scene.vrmenunodes.click(context)

        return {'FINISHED'}

class VRMenuNodesNavigationTeleport(bpy.types.Operator):
    bl_idname = "vrmenunodes.xr_navigation_teleport"
    bl_label = "Navigation Teleport"

    teleport_axes : bpy.props.BoolVectorProperty(size=3, default=(True, True, True))
    interpolation : bpy.props.FloatProperty(default=1.0,min=0.0,max=1.0)
    offset : bpy.props.FloatProperty(default=0.0,min=0.0)
    selectable_only : bpy.props.BoolProperty(default=True)
    distance : bpy.props.FloatProperty(default=1.70141e+38,min=0.0)
    from_viewer : bpy.props.BoolProperty(default=False)
    axis : bpy.props.FloatVectorProperty(size=3, default=(0.0, 0.0, -1.0), min=-1.0, max=1.0)
    color : bpy.props.FloatVectorProperty(size=4, default=(0.35, 0.35, 1.0, 1.0), min=0.0, max=1.0)

    def invoke(self, context, event):
        # Check for XR action event.
        if not event.xr:
            return {'PASS_THROUGH'}

        if 'left' in event.xr.user_path:
            context.scene.vrmenunodes.trigger0_press(context)
        else:
            context.scene.vrmenunodes.trigger1_press(context)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}    

    def modal(self, context, event):
        # Check for XR action event.
        if not event.xr:
            return {'PASS_THROUGH'}

        # Check for correct VR action.
        if event.xr.action != 'teleport':
            return {'PASS_THROUGH'}

        # bpy.ops.wm.xr_navigation_teleport(
        #     teleport_axes=self.teleport_axes, 
        #     interpolation=self.interpolation,
        #     offset=self.offset,
        #     selectable_only=self.selectable_only,
        #     distance=self.distance,
        #     from_viewer=self.from_viewer,
        #     axis=self.axis,
        #     color=self.color)

        # Finish when button is released.
        if event.value == 'RELEASE':
            if 'left' in event.xr.user_path:
                context.scene.vrmenunodes.trigger0_release(context)
            else:
                context.scene.vrmenunodes.trigger1_release(context)
            
            return {'FINISHED'}

        #context.scene.xrsystem.sync_xr_timer(context)

        return {'RUNNING_MODAL'}

class VRMenuNodesNavigationGrab(bpy.types.Operator):
    bl_idname = "vrmenunodes.xr_navigation_grab"
    bl_label = "Navigation Grab"

    lock_location : bpy.props.BoolProperty(default=False)
    lock_location_z : bpy.props.BoolProperty(default=False)
    lock_rotation : bpy.props.BoolProperty(default=False)
    lock_rotation_z : bpy.props.BoolProperty(default=False)
    lock_scale : bpy.props.BoolProperty(default=False)

    def invoke(self, context, event):
        # Check for XR action event.
        if not event.xr:
            return {'PASS_THROUGH'}

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}    

    def modal(self, context, event):
        # Check for XR action event.
        if not event.xr:
            return {'PASS_THROUGH'}

        # Check for correct VR action.
        if event.xr.action != 'nav_grab':
            return {'PASS_THROUGH'}

        # bpy.ops.wm.xr_navigation_grab(
        #     lock_location=self.lock_location,
        #     lock_location_z=self.lock_location_z,
        #     lock_rotation=self.lock_rotation,
        #     lock_rotation_z=self.lock_rotation_z,
        #     lock_scale=self.lock_scale)

        # Finish when button is released.
        if event.value == 'RELEASE':
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

class VRMenuNodesNavigationFly(bpy.types.Operator):
    bl_idname = "vrmenunodes.xr_navigation_fly"
    bl_label = "Navigation Fly"

    mode : bpy.props.StringProperty(default='VIEWER_FORWARD')
    lock_location_z : bpy.props.BoolProperty(default=False)
    lock_direction : bpy.props.BoolProperty(default=False)
    speed_frame_based : bpy.props.BoolProperty(default=False)
    speed_min : bpy.props.FloatProperty(default=0.018,min=0.0, max=1000.0)
    speed_max : bpy.props.FloatProperty(default=0.054,min=0.0, max=1000.0)
    speed_interpolation0 : bpy.props.FloatVectorProperty(size=2, default=(0.0, 0.0),min=0.0, max=1.0)
    speed_interpolation1 : bpy.props.FloatVectorProperty(size=2, default=(1.0, 1.0),min=0.0, max=1.0)

    def invoke(self, context, event):
        # Check for XR action event.
        if not event.xr:
            return {'PASS_THROUGH'}

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}    

    def modal(self, context, event):
        # Check for XR action event.
        if not event.xr:
            return {'PASS_THROUGH'}

        # Check for correct VR action.
        # fly_forward
        # fly_back
        # fly_left
        # fly_right
        # fly_up
        # fly_down
        # fly_turnleft
        # fly_turnright
        # if event.xr.action != 'teleport':
        #     return {'PASS_THROUGH'}             

        # bpy.ops.wm.xr_navigation_fly(
        #     mode=self.mode, 
        #     lock_location_z=self.lock_location_z, 
        #     lock_direction=self.lock_direction, 
        #     speed_frame_based=self.speed_frame_based, 
        #     speed_min=self.speed_min, 
        #     speed_max=self.speed_max, 
        #     speed_interpolation0=self.speed_interpolation0, 
        #     speed_interpolation1=self.speed_interpolation1)

        # Finish when button is released.
        if event.value == 'RELEASE':
            return {'FINISHED'}

        return {'RUNNING_MODAL'}        

class VRMenuNodesNavigationReset(bpy.types.Operator):
    bl_idname = "vrmenunodes.xr_navigation_reset"
    bl_label = "Navigation Reset"

    location : bpy.props.BoolProperty(default=True)
    rotation : bpy.props.BoolProperty(default=True)
    scale : bpy.props.BoolProperty(default=True)

    def invoke(self, context, event):
        # Check for XR action event.
        if not event.xr:
            return {'PASS_THROUGH'}

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}    

    def modal(self, context, event):
        # Check for XR action event.
        if not event.xr:
            return {'PASS_THROUGH'}

        # Check for correct VR action.
        if event.xr.action != 'nav_reset':
            return {'PASS_THROUGH'}

        # bpy.ops.wm.xr_navigation_reset(
        #     location=self.location, 
        #     rotation=self.rotation, 
        #     scale=self.scale)

        # Finish when button is released.
        if event.value == 'RELEASE':
            return {'FINISHED'}

        return {'RUNNING_MODAL'}                  

class VIEW_PT_VRMenuPanel(bpy.types.Panel):
    bl_label = "VRMenu"
    bl_idname = "VIEW_PT_VRMenuPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BHolodeck"
    
    def draw(self,context):
        layout = self.layout        
        
        row = layout.row()
        row.prop(context.scene.view_pg_vrmenu, "menu_path", text="Path")

        row = layout.row()
        row.prop(context.scene.view_pg_vrmenu, "main_tree", text="Tree")

        if context.scene.vrmenunodes.enabled:
            row = layout.row()
            row.operator("vrmenunodes.hide")
        else:
            row = layout.row()
            row.operator("vrmenunodes.show") 

        box = layout.box()
        row = box.row()
        row.operator("vrmenunodes.up")

        row = box.row()
        row.operator("vrmenunodes.left")
        row.operator("vrmenunodes.right")

        row = box.row()
        row.operator("vrmenunodes.down") 

        row = layout.row()
        row.prop(context.scene.view_pg_vrmenu, "value_float", text="Value", slider=True)

def view_pg_vrmenu_value_get(self):
    if bpy.context.scene.vrmenunodes.enabled == False:
        return 0

    return bpy.context.scene.vrmenunodes.value_float_get(bpy.context)

def view_pg_vrmenu_value_set(self, value):
    if bpy.context.scene.vrmenunodes.enabled == False:
        return 0

    return bpy.context.scene.vrmenunodes.value_float_set(bpy.context, value)   

class VIEW_PG_VRMenu(bpy.types.PropertyGroup):
    menu_path : bpy.props.StringProperty(default = "", subtype = 'DIR_PATH')
    main_tree : bpy.props.PointerProperty(type = bpy.types.NodeTree)
    value_float : bpy.props.FloatProperty(min=0, max=1, get=view_pg_vrmenu_value_get, set=view_pg_vrmenu_value_set)
    execution_time : bpy.props.FloatProperty(name = "Execution Time")

def register():
    bpy.utils.register_class(VRMenuTree)
    bpy.utils.register_class(VRMenuSocketIn)
    bpy.utils.register_class(VRMenuSocketOut)
    bpy.utils.register_class(VRMenuNodeMenu)
    bpy.utils.register_class(VRMenuNodeFloat)
    bpy.utils.register_class(VRMenuNodeScript)
    bpy.utils.register_class(VRMenuNodeRoot)
    bpy.utils.register_class(VRMenuNodesShow)
    bpy.utils.register_class(VRMenuNodesHide)
    bpy.utils.register_class(VRMenuNodesShowHide)
    bpy.utils.register_class(VRMenuNodesUp)
    bpy.utils.register_class(VRMenuNodesDown)
    bpy.utils.register_class(VRMenuNodesLeft)
    bpy.utils.register_class(VRMenuNodesRight)
    bpy.utils.register_class(VRMenuNodesClick)
    bpy.utils.register_class(VRMenuNodesTrigger0Press)
    bpy.utils.register_class(VRMenuNodesTrigger0Release)
    bpy.utils.register_class(VRMenuNodesTrigger1Press)
    bpy.utils.register_class(VRMenuNodesTrigger1Release)
    bpy.utils.register_class(VRMenuNodesTrackpadEvent)         

    bpy.utils.register_class(VRMenuNodesNavigationTeleport)
    bpy.utils.register_class(VRMenuNodesNavigationGrab)
    bpy.utils.register_class(VRMenuNodesNavigationFly)
    bpy.utils.register_class(VRMenuNodesNavigationReset)

    bpy.utils.register_class(VIEW_PT_VRMenuPanel)
    bpy.utils.register_class(VIEW_PG_VRMenu)

    bpy.types.Scene.vrmenunodes = VRMenuNodes()
    bpy.types.Scene.view_pg_vrmenu = bpy.props.PointerProperty(type=VIEW_PG_VRMenu)

    nodeitems_utils.register_node_categories("VRMENUNODES", node_categories)


def unregister():
    nodeitems_utils.unregister_node_categories("VRMENUNODES")

    delattr(bpy.types.Scene, "view_pg_vrmenu")
    delattr(bpy.types.Scene, "vrmenunodes")

    bpy.utils.unregister_class(VIEW_PT_VRMenuPanel)
    bpy.utils.unregister_class(VIEW_PG_VRMenu)

    bpy.utils.unregister_class(VRMenuNodesShow)
    bpy.utils.unregister_class(VRMenuNodesHide)
    bpy.utils.unregister_class(VRMenuNodesShowHide)
    bpy.utils.unregister_class(VRMenuNodesUp)
    bpy.utils.unregister_class(VRMenuNodesDown)
    bpy.utils.unregister_class(VRMenuNodesLeft)
    bpy.utils.unregister_class(VRMenuNodesRight)
    bpy.utils.unregister_class(VRMenuNodesClick)

    bpy.utils.unregister_class(VRMenuTree)
    bpy.utils.unregister_class(VRMenuSocketIn)
    bpy.utils.unregister_class(VRMenuSocketOut)
    bpy.utils.unregister_class(VRMenuNodeMenu)
    bpy.utils.unregister_class(VRMenuNodeFloat)
    bpy.utils.unregister_class(VRMenuNodeScript)
    bpy.utils.unregister_class(VRMenuNodeRoot)

    bpy.utils.unregister_class(VRMenuNodesTrigger0Press)
    bpy.utils.unregister_class(VRMenuNodesTrigger0Release)    
    bpy.utils.unregister_class(VRMenuNodesTrigger1Press)
    bpy.utils.unregister_class(VRMenuNodesTrigger1Release)
    bpy.utils.unregister_class(VRMenuNodesTrackpadEvent)

    bpy.utils.unregister_class(VRMenuNodesNavigationTeleport)
    bpy.utils.unregister_class(VRMenuNodesNavigationGrab)
    bpy.utils.unregister_class(VRMenuNodesNavigationFly)
    bpy.utils.unregister_class(VRMenuNodesNavigationReset)     

    