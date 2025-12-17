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

import functools
import logging
import os.path
import tempfile

import datetime
import typing

import bpy
from bpy.types import AddonPreferences, Operator, WindowManager, Scene, PropertyGroup
from bpy.props import StringProperty, EnumProperty, PointerProperty, BoolProperty, IntProperty
import rna_prop_ui

import uuid

ADDON_NAME = 'bholodeck'

@functools.lru_cache()
def factor(factor: float) -> dict:
    """Construct keyword argument for UILayout.split().

    On Blender 2.8 this returns {'factor': factor}, and on earlier Blenders it returns
    {'percentage': factor}.
    """
    if bpy.app.version < (2, 80, 0):
        return {'percentage': factor}
    return {'factor': factor}

server_type_items = [
    ("SERVER", "Server", ""),
    ("CLIENT", "Client", ""),
]

##################################################
from collections import namedtuple
import subprocess, sys, importlib

#grpcio, grpcio-tools, pillow, pyaudio/pipwin

Dependency = namedtuple("Dependency", ["module", "package", "name"])
python_dependencies = (Dependency(module="grpc", package="grpcio", name=None),
                    Dependency(module="grpc", package="grpcio-tools", name=None),
                    #Dependency(module="protobuf", package="protobuf", name=None),
                    Dependency(module="PIL", package="pillow", name=None),
                    Dependency(module="pyaudio", package="pyaudio", name=None),                                        
                )

internal_dependencies = []

def import_module(module_name, global_name=None, reload=True):
    if global_name is None:
        global_name = module_name

    if global_name in globals():
        importlib.reload(globals()[global_name])
    else:
        # Attempt to import the module and assign it to globals dictionary. This allow to access the module under
        # the given name, just like the regular import would.
        globals()[global_name] = importlib.import_module(module_name)

def install_pip():
    try:
        if bpy.app.version < (2, 90, 0):
            python_exe = bpy.app.binary_path_python
        else:
            python_exe = sys.executable

        # Check if pip is already installed
        subprocess.run([python_exe, "-m", "pip", "--version"], check=True)

        # Upgrade
        subprocess.run([python_exe, "-m", "pip", "install", "--upgrade", "pip"], check=True)

    except subprocess.CalledProcessError:
        import ensurepip

        ensurepip.bootstrap()
        os.environ.pop("PIP_REQ_TRACKER", None)

def install_and_import_module(module_name, package_name=None, global_name=None):
    if package_name is None:
        package_name = module_name

    if global_name is None:
        global_name = module_name

    # Create a copy of the environment variables and modify them for the subprocess call
    environ_copy = dict(os.environ)
    environ_copy["PYTHONNOUSERSITE"] = "1"

    if bpy.app.version < (2, 90, 0):
        python_exe = bpy.app.binary_path_python
    else:
        python_exe = sys.executable

    subprocess.run([python_exe, "-m", "pip", "install", package_name], check=True, env=environ_copy)

    # The installation succeeded, attempt to import the module again
    import_module(module_name, global_name)      

##################################################################
def install_dependencies():
    install_pip()
    for dependency in python_dependencies:
        install_and_import_module(module_name=dependency.module,
                                  package_name=dependency.package,
                                  global_name=dependency.name)                                  
    
class BHOLODECK_OT_install_dependencies(Operator):
    bl_idname = 'bholodeck.install_dependencies'
    bl_label = 'Install dependencies'
    bl_description = ("Downloads and installs the required python packages for this add-on. "
                      "Internet connection is required. Blender may have to be started with "
                      "elevated permissions in order to install the package")

    def execute(self, context):
        try:
            install_dependencies()
            
            #enable_internal_addons()
            #install_external_addons()

        except (subprocess.CalledProcessError, ImportError) as err:
            self.report({"ERROR"}, str(err))
            return {"CANCELLED"}

        preferences().dependencies_installed = True

        # Register the panels, operators, etc. since dependencies are installed
        #from . import sim_scene
        #sim_scene.register()

        self.report({'INFO'}, "'%s' finished" % (self.bl_label))
        return {"FINISHED"}

class BHOLODECK_OT_update_dependencies(Operator):
    bl_idname = 'bholodeck.update_dependencies'
    bl_label = 'Update dependencies'
    bl_description = ("Downloads and installs the required python packages for this add-on. "
                      "Internet connection is required. Blender may have to be started with "
                      "elevated permissions in order to install the package")

    def execute(self, context):
        try:
            install_dependencies()
            
            #enable_internal_addons()
            #install_external_addons()

        except (subprocess.CalledProcessError, ImportError) as err:
            self.report({"ERROR"}, str(err))
            return {"CANCELLED"}

        preferences().dependencies_installed = True

        # Register the panels, operators, etc. since dependencies are installed
        #from . import sim_scene
        #sim_scene.register()

        self.report({'INFO'}, "'%s' finished" % (self.bl_label))
        return {"FINISHED"}           
################################################################   

class BHolodeckPreferences(AddonPreferences):
    bl_idname = ADDON_NAME

    server: StringProperty(
        name='Server',
        default='localhost'
    )

    port: IntProperty(
        name='Port',
        default=7007
    )

    server_type : EnumProperty(
        items=server_type_items,
        name="Type"
    )

    username: StringProperty(
        name='Username',
        default=str(uuid.uuid4())
    )    

    login: StringProperty(
        name='Login',
        default='test'
    )

    password: StringProperty(
        name='Password',
        default='test',
        subtype='PASSWORD'
    )   

    dependencies_installed: BoolProperty(
        default=False
    )    

    def reset_messages(self):
        self.ok_message = ''
        self.error_message = ''

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        if not self.dependencies_installed:
            box.operator(BHOLODECK_OT_install_dependencies.bl_idname, icon="CONSOLE")
        else:
            box.operator(BHOLODECK_OT_update_dependencies.bl_idname, icon="CONSOLE")        

        box = layout.box()

        server_type_split = box.split(**factor(0.25), align=True)
        server_type_split.label(text='Type:')
        server_type_box = server_type_split.row(align=True)        
        server_type_box.prop(self, 'server_type', text='')

        if self.is_client():
            server_split = box.split(**factor(0.25), align=True)
            server_split.label(text='Server:')
            server_box = server_split.row(align=True)        
            server_box.prop(self, 'server', text='')

        port_split = box.split(**factor(0.25), align=True)
        port_split.label(text='Port:')
        port_box = port_split.row(align=True)        
        port_box.prop(self, 'port', text='') 

        if self.is_client():
            username_split = box.split(**factor(0.25), align=True)
            username_split.label(text='Username:')
            username_box = username_split.row(align=True)        
            username_box.prop(self, 'username', text='')

        box = layout.box()

        if self.is_client():
            login_split = box.split(**factor(0.25), align=True)
            login_split.label(text='Login:')
            login_box = login_split.row(align=True)        
            login_box.prop(self, 'login', text='')            

            password_split = box.split(**factor(0.25), align=True)
            password_split.label(text='Password:')
            password_box = password_split.row(align=True)        
            password_box.prop(self, 'password', text='')

    def is_server(self):
        return self.server_type == 'SERVER'

    def is_client(self):
        return self.server_type == 'CLIENT'                                 


def ctx_preferences():
    """Returns bpy.context.preferences in a 2.79-compatible way."""
    try:
        return bpy.context.preferences
    except AttributeError:
        return bpy.context.user_preferences

def preferences() -> BHolodeckPreferences:
    return ctx_preferences().addons[ADDON_NAME].preferences

def register():
    """register."""

    bpy.utils.register_class(BHolodeckPreferences)
    bpy.utils.register_class(BHOLODECK_OT_install_dependencies)
    bpy.utils.register_class(BHOLODECK_OT_update_dependencies)
       
    try:
        import grpc
        import PIL

        preferences().dependencies_installed = True
    except ModuleNotFoundError:
        preferences().dependencies_installed = False         

    return


def unregister():
    """unregister."""

    bpy.utils.unregister_class(BHOLODECK_OT_update_dependencies)
    bpy.utils.unregister_class(BHOLODECK_OT_install_dependencies)
    bpy.utils.unregister_class(BHolodeckPreferences)

    return
