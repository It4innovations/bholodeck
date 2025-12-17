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

bl_info = {
    "name" : "bholodeck",
    "author" : "Milan Jaros, Petr Strakos, Marketa Hrabankova",
    "description" : "Collaborate and Create in VR",
    "blender" : (3, 3, 0),
    "version" : (0, 0, 4),
    "location": "3D View > Sidebar > VR",
    "category" : "3D View",
}

if "bpy" in locals():
    import importlib
    importlib.reload(viewport_vr_preview)
    importlib.reload(bholodeck_pref)
    importlib.reload(netsystem)
    importlib.reload(vrmenunodes)
    importlib.reload(vrobjectactionnodes)
    importlib.reload(vraudio)
    importlib.reload(xrsystem)
else:
    from . import viewport_vr_preview      
    from . import bholodeck_pref

    try:
        from . import netsystem
        from . import vrmenunodes
    except:
        bholodeck_pref.install_dependencies()

    from . import netsystem
    from . import vrmenunodes

    from . import vrobjectactionnodes        
    from . import vraudio
    from . import xrsystem

import bpy

def register():
    """register"""

    viewport_vr_preview.register()            
    bholodeck_pref.register()
    netsystem.register()    
    vrmenunodes.register()
    vrobjectactionnodes.register()
    vraudio.register()
    xrsystem.register()

def unregister():
    """unregister"""

    viewport_vr_preview.unregister()  
    bholodeck_pref.unregister()
    netsystem.unregister()
    vrmenunodes.unregister()
    vrobjectactionnodes.unregister()
    vraudio.unregister()
    xrsystem.unregister()
