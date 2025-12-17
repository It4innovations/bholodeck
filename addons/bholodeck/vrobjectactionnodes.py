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
from bpy.types import NodeTree, Node, NodeSocket

from pathlib import Path

# Derived from the NodeTree base type, similar to Menu, Operator, Panel, etc.
class VRObjectActionTree(NodeTree):
    # Description string
    '''A custom node tree type that will show up in the node editor header'''
    # Optional identifier string. If not explicitly defined, the python class name is used.
    bl_idname = 'VRObjectActionTreeType'
    # Label for nice name display
    bl_label = 'VRObjectAction Node Tree'
    # Icon identifier
    bl_icon = 'NODETREE'

class VIEW_PT_VRObjectActionPanel(bpy.types.Panel):
    bl_label = "VRObjectAction"
    bl_idname = "VIEW_PT_VRObjectActionPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BHolodeck"
    
    def draw(self,context):
        layout = self.layout        
        
        row = layout.row()
        row.prop(context.scene.view_pg_vrobjectaction, "main_tree", text="Tree")

        row = layout.row()
        row.operator("vrobjectactionnodes.apply")

        row = layout.row()
        row.operator("vrobjectactionnodes.clear")

        row = layout.row()
        row.operator("vrobjectactionnodes.action")


vrobjectaction_property_type_items = [
    ("SCRIPT", "Script", ""),
]

class VRObjectActionNodeProperty(Node, VRObjectActionTree):
    # === Basics ===
    # Description string
    '''A ObjectAction node'''
    # Optional identifier string. If not explicitly defined, the python class name is used.
    bl_idname = 'VRObjectActionNodeProperty'
    # Label for nice name display
    bl_label = 'ObjectActionNodeProperty'
    # Icon identifier
    bl_icon = 'MENU_PANEL'

    object : bpy.props.PointerProperty(name="Object", type = bpy.types.Object)
    type : bpy.props.EnumProperty(name="Type", items=vrobjectaction_property_type_items)
    script : bpy.props.PointerProperty(name="Script", type = bpy.types.Text)
    
    def init(self, context):
        #out = self.outputs.new('VRMenuSocketOut', "Menu")
        #out.name = 'ROOT'
        pass

    def draw_buttons(self, context, layout):
        box = layout.box()
        #box.enabled=False
        #box.label(text="Active")
        box.prop(self, "object")   
        box.prop(self, "type")  
        if self.type == "SCRIPT":
            box.prop(self, "script")

    def draw_label(self):
        return "ObjectAction"                 

class VRObjectActionNodesApply(bpy.types.Operator):
    bl_idname = "vrobjectactionnodes.apply"
    bl_label = "Apply"

    def execute(self,context):
        context.scene.vrobjectactionnodes.apply(context)

        return {'FINISHED'}

class VRObjectActionNodesClear(bpy.types.Operator):
    bl_idname = "vrobjectactionnodes.clear"
    bl_label = "Clear"

    def execute(self,context):
        context.scene.vrobjectactionnodes.clear(context)

        return {'FINISHED'}

class VRObjectActionNodesAction(bpy.types.Operator):
    bl_idname = "vrobjectactionnodes.action"
    bl_label = "Action"

    def execute(self,context):
        context.scene.vrobjectactionnodes.action(context)

        return {'FINISHED'}

### Node Categories ###
# Node categories are a python system for automatically
# extending the Add menu, toolbar panels and search operator.
# For more examples see release/scripts/startup/nodeitems_builtins.py

import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem


# our own base class with an appropriate poll function,
# so the categories only show up in our own tree type
class VRObjectActionNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'VRObjectActionTreeType'

# all categories in a list
node_categories = [
    # identifier, label, items list
    VRObjectActionNodeCategory("VROBJECTACTIONNODES", "VR Nodes", items=[
        # our basic node
        NodeItem("VRObjectActionNodeProperty"),
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

class VIEW_PG_VRObjectAction(bpy.types.PropertyGroup):
    main_tree : bpy.props.PointerProperty(type = bpy.types.NodeTree)   

class VRObjectActionNodes:
    def __init__(self):
        self.enabled = False   

    def apply(self, context):
        if context.scene.view_pg_vrobjectaction.main_tree is None:
            return None
        
        for node in context.scene.view_pg_vrobjectaction.main_tree.nodes:
            if node.bl_idname == 'VRObjectActionNodeProperty':
                if node.object:
                    if node.type == "SCRIPT":
                        node.object[node.type] = node.script

    def clear(self, context):
        if context.scene.view_pg_vrobjectaction.main_tree is None:
            return None
        
        for node in context.scene.view_pg_vrobjectaction.main_tree.nodes:
            if node.bl_idname == 'VRObjectActionNodeProperty':
                if node.object:
                    if node.type == "SCRIPT":
                        #node.object[node.type] = node.script
                        #delattr(ob, "SCRIPT")
                        del node.object["SCRIPT"]

    def action(self, context):
        for ob in context.selected_objects:
            if "SCRIPT" in ob:
                txt = context.scene.netsystem.replace_tag_in_script(ob["SCRIPT"].as_string())
                txt = txt.replace('{OBNAME}', ob.name)
                context.scene.netsystem.send_python_script(txt)
                exec(txt)
                return True
        
        return False

    def get_node(self, context, name):
        if context.scene.view_pg_vrobjectaction.main_tree is None:
            return None
        
        return context.scene.view_pg_vrobjectaction.main_tree.nodes[name]

def register():
    bpy.utils.register_class(VRObjectActionTree)
    bpy.utils.register_class(VRObjectActionNodeProperty)

    bpy.utils.register_class(VRObjectActionNodesApply)
    bpy.utils.register_class(VRObjectActionNodesAction)
    bpy.utils.register_class(VRObjectActionNodesClear)    

    bpy.utils.register_class(VIEW_PT_VRObjectActionPanel)
    bpy.utils.register_class(VIEW_PG_VRObjectAction)

    bpy.types.Scene.vrobjectactionnodes = VRObjectActionNodes()
    bpy.types.Scene.view_pg_vrobjectaction = bpy.props.PointerProperty(type=VIEW_PG_VRObjectAction)

    nodeitems_utils.register_node_categories("VROBJECTACTIONNODES", node_categories)


def unregister():
    nodeitems_utils.unregister_node_categories("VROBJECTACTIONNODES")

    delattr(bpy.types.Scene, "view_pg_vrobjectaction")
    delattr(bpy.types.Scene, "vrobjectactionnodes")

    bpy.utils.unregister_class(VIEW_PT_VRObjectActionPanel)
    bpy.utils.unregister_class(VIEW_PG_VRObjectAction)

    bpy.utils.unregister_class(VRObjectActionNodesApply)
    bpy.utils.unregister_class(VRObjectActionNodesClear)
    bpy.utils.unregister_class(VRObjectActionNodesAction)

    bpy.utils.unregister_class(VRObjectActionTree)
    bpy.utils.unregister_class(VRObjectActionNodeProperty)
