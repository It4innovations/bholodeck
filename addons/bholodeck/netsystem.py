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
import threading

from concurrent import futures

import grpc

from . import bholodeck_pref
from . import netsystem_pb2
from . import netsystem_pb2_grpc

import time
import traceback

############################### BPY #####################################################
def pretty_time(seconds):
    if seconds > 1.5: return "{:.2f} s".format(seconds)
    else: return "{:.4f} ms".format(seconds * 1000)

def print_exception(ex):
    print(traceback.format_exc())

class VIEW_PG_NetSystem(bpy.types.PropertyGroup):
    execution_time : bpy.props.FloatProperty(name = "Execution Time")

class VIEW_PT_NetSystemPanel(bpy.types.Panel):
    bl_label = "NetSystem"
    bl_idname = "VIEW_PT_NetSystemPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BHolodeck"
    
    def draw(self,context):
        layout = self.layout
        pref = bholodeck_pref.preferences()       
        
        row = layout.row()
        row.prop(pref, 'server_type', text='Type')

        if pref.is_client():
            row = layout.row()
            row.label(text='Client')
            row = layout.row()
            #row.enabled = False
            row.prop(pref, 'username', text='')
            row = layout.row()

            if context.scene.netsystem.enabled == False:
                row.operator("netsystem.start", text = "Connect")
            else:
                row.operator("netsystem.stop", text = "Disconnect")

                row = layout.row()
                #row.prop(context.scene.view_pg_vrmenu, "execution_time")
                row.label(text = pretty_time(context.scene.view_pg_netsystem.execution_time), icon = "TIME")
            #row.operator("netsystem.exec")

        if pref.is_server():
            row = layout.row()
            row.label(text='Server')
            row = layout.row()

            if context.scene.netsystem.enabled == False:
                row.operator("netsystem.start", text = "Start")
            else:
                row.operator("netsystem.stop", text = "Stop")
                row = layout.row()
                row.label(text='Clients')
                row = layout.row()
                row.template_list("BHOLODECK_UL_UsernamesGroup", "", context.scene, "view_pg_username", context.scene, "view_pg_username_index")         

class NetSystemStart(bpy.types.Operator):
    bl_idname = "netsystem.start"
    bl_label = "Start"
   
    def execute(self,context):
        context.scene.netsystem.init(context)

        return {'FINISHED'}

class NetSystemStop(bpy.types.Operator):
    bl_idname = "netsystem.stop"
    bl_label = "Stop"
   
    def execute(self,context):
        context.scene.netsystem.deinit(context)
        context.scene.view_pg_username.clear()
        context.scene.view_pg_username_index = -1

        return {'FINISHED'}

class BHOLODECK_PG_UsernamesGroup(bpy.types.PropertyGroup):
    username : bpy.props.StringProperty(name="Username")
    #code : bpy.props.StringProperty(name="Session Code")

class BHOLODECK_UL_UsernamesGroup(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.label(text=item.username)
        #layout.label(text=item.code)  

############################### GRPC #####################################################

class VRManagement(netsystem_pb2_grpc.VRManagementServicer):
    def RegisterUser(self, request, context):

        pref = bholodeck_pref.preferences() 
        if pref.login != request.login or pref.password != request.password:
            raise Exception('wrong credentials') 

        if len(request.username) < 3:
            raise Exception('username is too short')

        for client in bpy.context.scene.netsystem.netclient_list:
            if request.username == client.username:
                raise Exception('username %s exist - unregister first' % client.username)        

        bpy.context.scene.netsystem.netclient_list_lock.acquire()

        user = bpy.context.scene.view_pg_username.add()
        user.username = request.username

        netclient = NetClient()
        netclient.username = request.username

        response = netsystem_pb2.RegisterUserResponse()
        response.username = netclient.username

        users_count = len(bpy.context.scene.netsystem.netclient_list)

        netclient.landmark_location = [0,0,0]
        netclient.landmark_angle = 0.0

        if users_count == 0:
            netclient.landmark_location = [1,0,1]
            netclient.landmark_angle = 90.0

        if users_count == 1:
            netclient.landmark_location = [-1,0,1]
            netclient.landmark_angle = -90.0

        if users_count == 2:
            netclient.landmark_location = [0,1,1]
            netclient.landmark_angle = 180.0

        if users_count == 3:
            netclient.landmark_location = [0,-1,1]
            netclient.landmark_angle = 0.0

        response.landmark_location.extend(netclient.landmark_location)
        response.landmark_angle = 0 #netclient.landmark_angle * 3.14 / 180.0

        bpy.context.scene.netsystem.netclient_list.append(netclient)

        bpy.context.scene.netsystem.netclient_list_lock.release()

        return response

    def UnregisterUser(self, request, context):

        bpy.context.scene.netsystem.netclient_list_lock.acquire()

        for i in range(len(bpy.context.scene.view_pg_username)):
            if request.username == bpy.context.scene.view_pg_username[i].username:
                bpy.context.scene.view_pg_username.remove(i)
                break

        for client in bpy.context.scene.netsystem.netclient_list:
            if request.username == client.username:
                bpy.context.scene.netsystem.netclient_list.remove(client)
                break

        bpy.context.scene.netsystem.netclient_list_lock.release()

        return netsystem_pb2.Empty()

    def SendPythonScript(self, request, context):
        try: 
            #bpy.context.scene.netsystem.check_client(request.username)

            for client in bpy.context.scene.netsystem.netclient_list:
                if request.username != client.username and len(request.python_script) > 0:
                    client.changes_lock.acquire()
                    client.python_script_list.append(request.python_script)
                    client.changes_lock.release()
        except Exception as e:
            print_exception(e)

        return netsystem_pb2.Empty()

    def SendAudio(self, request, context):
        try: 
            #bpy.context.scene.netsystem.check_client(request.username)

            for client in bpy.context.scene.netsystem.netclient_list:
                if request.username != client.username and len(request.audio_data) > 0:
                    client.changes_lock.acquire()

                    if request.username not in client.other_netclient_dict:
                        client.other_netclient_dict[request.username] = NetClient()
                    
                    if len(client.other_netclient_dict[request.username].audio_data_list) == 0:
                        client.other_netclient_dict[request.username].audio_data_list.append(request.audio_data)

                    client.changes_lock.release()

        except Exception as e:
            print_exception(e)

        return netsystem_pb2.Empty()

    def ExData(self, request, context):
        try:
            response = netsystem_pb2.ExDataResponse()

            for client in bpy.context.scene.netsystem.netclient_list:
                if request.username != client.username and len(request.position_list) > 0:
                    client.changes_lock.acquire()

                    if request.username not in client.other_netclient_dict:
                        client.other_netclient_dict[request.username] = NetClient()
                    
                    if len(client.other_netclient_dict[request.username].position_list) == 0:
                        client.other_netclient_dict[request.username].position_list.append(request.position_list)

                    client.changes_lock.release()

            for client in bpy.context.scene.netsystem.netclient_list:
                if request.username == client.username:
                    position_list = []
                    python_script_list = []
                    audio_data_list = []

                    client.changes_lock.acquire()
                    if len(client.python_script_list) > 0:
                        python_script_list.append(client.python_script_list.pop(0))
                    
                    for other_netclient in client.other_netclient_dict.values():

                        if len(other_netclient.position_list) > 0:
                            pl = other_netclient.position_list.pop(0)
                            for position in pl:
                                position_list.append(position)

                        if len(other_netclient.audio_data_list) > 0:
                            audio_data_list.append(other_netclient.audio_data_list.pop(0))

                    client.changes_lock.release()

                    if len(position_list) > 0:
                        response.position_list.extend(position_list)

                    if len(python_script_list) > 0:
                        response.python_script_list.extend(python_script_list)

                    if len(audio_data_list) > 0:
                        response.audio_data_list.extend(audio_data_list)

                    break

            for client in bpy.context.scene.netsystem.netclient_list:
                if request.username != client.username and len(request.audio_data) > 0:
                    client.changes_lock.acquire()

                    if request.username not in client.other_netclient_dict:
                        client.other_netclient_dict[request.username] = NetClient()
                    
                    if len(client.other_netclient_dict[request.username].audio_data_list) == 0:
                        client.other_netclient_dict[request.username].audio_data_list.append(request.audio_data)

                    client.changes_lock.release()                

            
            return response

        except Exception as e:
            print_exception(e)

        return netsystem_pb2.ExDataResponse()
            
############################### GRPC #####################################################
class NetClient:
    def __init__(self):
        self.username = ''

        self.position_list = []
        #self.positions_lock = threading.Lock()
        self.audio_data_list = []
        #self.audio_data_lock = threading.Lock()
        self.python_script_list = []
        #self.python_script_lock = threading.Lock()

        self.landmark_location = [0,0,0]
        self.landmark_angle = 0

        self.other_netclient_dict = {}
        self.changes_lock = threading.Lock()

# def sync_data_timer():
#     window = bpy.context.window_manager.windows[0]
#     ops_ctx = {'window': window, 'screen': window.screen}

#     bpy.context.scene.netsystem.sync_data_timer(bpy.context, ops_ctx)

#     return 0.1

class NETSYSTEM_OT_sync_data_timer(bpy.types.Operator):
    bl_idname = "netsystem.sync_data_timer"
    bl_label = "Net Timer"

    def execute(self, context):
        self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}    

    def modal(self, context, event):
        # Check for XR action event.
        if not event.type == 'TIMER' or not context.window_manager.xr_session_state:
            return {'PASS_THROUGH'}

        # Finish when button is released.
        if context.scene.netsystem.enabled == False:
            context.window_manager.event_timer_remove(self._timer)
            return {'FINISHED'}

        context.scene.netsystem.sync_data_timer(context)
        #print(event.type)

        return {'RUNNING_MODAL'}   

def _sync_data_thread():
    bpy.context.scene.netsystem._sync_data_thread(bpy.context)

class NetSystem:

    def __init__(self):
        self.enabled = False

        self.netclient_list = []
        self.netclient_list_lock = threading.Lock()

        self.current_netclient = NetClient()

        self.execution_time = 0

        # self.username = ''
        # self.position_list = queue.Queue(1)
        # self.python_script = queue.Queue()
        # self.audio_data = queue.Queue(1)

    # def check_client(self, username):
    #     for client in bpy.context.scene.netsystem.netclient_list:
    #         if username == client.username:
    #             return

    #     raise Exception("User does not exist, please register client first") 

    def deinit(self, context):
        try:

            if self.enabled == False:
                return

            self.enabled = False

            pref = bholodeck_pref.preferences() 

            if pref.is_server():
                self.server.stop(0)

            if pref.is_client():
                self.sync_data_thread_exit = True
                self.sync_data_thread.join()

                if len(self.current_netclient.username) > 0:
                    self.vr_management_stub.UnregisterUser(netsystem_pb2.UnregisterUserRequest(username=self.current_netclient.username))

                #bpy.ops.screen.animation_play()
                #bpy.app.handlers.frame_change_pre.remove(draw_callback_3d)
                #bpy.app.timers.unregister(sync_data_timer)
                # self.new_positions = False
                # self.position_list = []
                #bpy.types.SpaceView3D.draw_handler_remove(self._handle_3d, 'WINDOW')
                

            self.netclient_list = []
            #self.username = ''
            #self.enabled = False

        except Exception as e:
            print_exception(e) 

    def _wait_on_exit(self):
        print('Start _wait_on_exitself')

        try:
            while self.enabled == True:
                time.sleep(1)
        except Exception as e:
            print_exception(e)

        print('Finish _wait_on_exitself')

    # def draw_callback_3d(self):
    #     if self.new_positions == True:
    #         for position in self.position_list:
    #             bpy.context.scene.xrsystem.set_position(bpy.context, position.object_name, position.object_location, position.object_rotation_quaternion)
                
    #         self.new_positions = False

    def set_position(self, context, position):
        self.context.scene.xrsystem.set_position(context, position.object_name, position.object_location, position.object_rotation_quaternion)

    def sync_data_timer(self, context):
        try:
            context.scene.view_pg_netsystem.execution_time = self.execution_time

            position_list = []
            python_script_list = []

            self.current_netclient.changes_lock.acquire()
            if len(self.current_netclient.position_list) > 0:
                position_list = self.current_netclient.position_list.pop(0)

            if len(self.current_netclient.python_script_list) > 0:
                python_script_list = self.current_netclient.python_script_list.pop(0)

            self.current_netclient.changes_lock.release()

            for position in position_list:
                self.set_position(context, position)

            for python_script in python_script_list:
                exec(python_script)
                      
        except Exception as e:
            print_exception(e)  
        
    def _sync_data_thread(self, context):
        print('Start sync_data_thread')

        try:
            while self.sync_data_thread_exit == False:
                #time.sleep(0.01)
                execution_start = time.perf_counter()
                
                # Set Positions
                #if len(self.current_netclient.username) > 0:
                send_data_request = netsystem_pb2.ExDataRequest()
                send_data_request.username = self.current_netclient.username
                #context = self.context
                xrsystem = context.scene.xrsystem

                try:
                    if xrsystem.enabled == True: # and self.new_positions == False:
                        #self.position_list = []
                                        
                        #HMD
                        object_location, object_rotation_quaternion = xrsystem.get_hmd_position(context)

                        hmd_position = send_data_request.position_list.add()                
                        hmd_position.object_name = self.current_netclient.username + "_HMD";
                        hmd_position.object_type = "HMD"
                        #hmd_position.object_location = struct.pack("%3f", *object_location)
                        hmd_position.object_location.extend(object_location)
                        hmd_position.object_rotation_quaternion.extend(object_rotation_quaternion)

                        # if bpy.data.objects[hmd_position.object_name].rotation_mode != 'QUATERNION':
                        #     bpy.data.objects[hmd_position.object_name].rotation_mode = 'QUATERNION'

                        #self.set_position(context, ops_ctx, hmd_position)                            

                        #BODY
                        object_location, object_rotation_quaternion = xrsystem.get_body_position(context)

                        body_position = send_data_request.position_list.add()                
                        body_position.object_name = self.current_netclient.username + "_BODY";
                        body_position.object_type = "BODY"
                        #body_position.object_location = struct.pack("%3f", *object_location)
                        body_position.object_location.extend(object_location)
                        body_position.object_rotation_quaternion.extend(object_rotation_quaternion)                                                    

                        #C0
                        if context.scene.view_pg_xrsystem.controller_type == "ACER":
                            object_location, object_rotation_quaternion = xrsystem.get_controller1_position(context)
                        else:
                            object_location, object_rotation_quaternion = xrsystem.get_controller0_position(context)

                        c0_position = send_data_request.position_list.add()
                        c0_position.object_name = self.current_netclient.username + "_CONTROLLER0"
                        c0_position.object_type = "CONTROLLER0"
                        c0_position.object_location.extend(object_location)
                        c0_position.object_rotation_quaternion.extend(object_rotation_quaternion)

                        # need_set_parent = False
                        # if not c0_position.object_name in bpy.data.objects:
                        #     need_set_parent = True

                        #self.set_position(context, ops_ctx, c0_position)

                        if context.scene.vrmenunodes.enabled == True:
                            context.scene.vrmenunodes.set_parent(context, bpy.data.objects[c0_position.object_name])
                                                                    
                        #C1
                        if context.scene.view_pg_xrsystem.controller_type == "ACER":
                            object_location, object_rotation_quaternion = xrsystem.get_controller0_position(context)
                        else:                        
                            object_location, object_rotation_quaternion = xrsystem.get_controller1_position(context)

                        c1_position = send_data_request.position_list.add()
                        c1_position.object_name = self.current_netclient.username + "_CONTROLLER1"
                        c1_position.object_type = "CONTROLLER1"
                        c1_position.object_location.extend(object_location)
                        c1_position.object_rotation_quaternion.extend(object_rotation_quaternion)

                        # if bpy.data.objects[c1_position.object_name].rotation_mode != 'QUATERNION':
                        #     bpy.data.objects[c1_position.object_name].rotation_mode = 'QUATERNION'

                        #self.set_position(context, ops_ctx, c1_position)

                        # Send Audio
                        if context.scene.vraudio.enabled == True:
                            context.scene.vraudio.changes_lock.acquire()
                            if not context.scene.vraudio.audio_data == None:
                                send_data_request.audio_data = context.scene.vraudio.audio_data
                                context.scene.vraudio.audio_data = None
                            context.scene.vraudio.changes_lock.release()

                except Exception as e:
                    print_exception(e)                                                                                        

                if len(self.current_netclient.username) > 0:
                    # Exchange data
                    recv_data_response = self.vr_management_stub.ExData(send_data_request)

                    # Recv Positions
                    try:
                            # if xrsystem.enabled == True: # and self.new_positions == False:
                            #for position in recv_data_response.position_list:
                                #self.set_position(context, ops_ctx, position)
                            if len(recv_data_response.position_list) > 0:
                                self.current_netclient.changes_lock.acquire()
                                if len(self.current_netclient.position_list) == 0:
                                    self.current_netclient.position_list.append(recv_data_response.position_list)
                                self.current_netclient.changes_lock.release()

                        # if xrsystem.enabled == True and self.new_positions == False:
                        #     self.new_positions = True
                        #pass

                    except Exception as e:
                        print_exception(e) 

                    # Recv Python Script
                    try:
                        if len(recv_data_response.python_script_list) > 0:
                            #exec(recv_data_response.python_script)
                            self.current_netclient.changes_lock.acquire()
                            self.current_netclient.python_script_list.append(recv_data_response.python_script_list)
                            self.current_netclient.changes_lock.release()

                    except Exception as e:
                        print_exception(e) 

                    # Recv Audio
                    try:
                        for audio_data in recv_data_response.audio_data_list:
                            context.scene.vraudio.play_sound(audio_data)
                    except Exception as e:
                        print_exception(e) 

                execution_end = time.perf_counter()
                self.execution_time = execution_end - execution_start

        except Exception as e:
            print_exception(e) 

        print('Finish sync_data_thread')

    def init(self, context):
        try:

            if self.enabled == True:
                return

            self.context = context

            pref = bholodeck_pref.preferences() 

            if pref.is_server():
                self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=16))

                netsystem_pb2_grpc.add_VRManagementServicer_to_server(VRManagement(), self.server)

                self.server.add_insecure_port('[::]:%d' % (pref.port))
                self.server.start()

            if pref.is_client():
                self.channel = grpc.insecure_channel('%s:%d' % (pref.server, pref.port))

                self.vr_management_stub = netsystem_pb2_grpc.VRManagementStub(self.channel)

                try:
                    response = self.vr_management_stub.RegisterUser(netsystem_pb2.RegisterUserRequest(username=pref.username, login=pref.login, password=pref.password))
                
                    self.current_netclient.username = response.username #response.username
                    self.current_netclient.landmark_location = response.landmark_location
                    self.current_netclient.landmark_angle = response.landmark_angle

                except Exception as e:
                    self.current_netclient.username = ''
                    print_exception(e) 
                    pass

                # self.position_list = []
                # self.new_positions = False

                self.sync_data_thread_exit = False
                self.sync_data_thread = threading.Thread(target=_sync_data_thread)
                self.sync_data_thread.start()

                # bpy.app.handlers.frame_change_pre.append(draw_callback_3d)
                # bpy.ops.screen.animation_play()

                #bpy.app.timers.register(sync_data_timer, persistent=True)
                
                # args = (self, context)        
                # self._handle_3d = bpy.types.SpaceView3D.draw_handler_add(draw_callback_3d, args, 'WINDOW', 'POST_VIEW')

            self.enabled = True

            if pref.is_client():
                bpy.ops.netsystem.sync_data_timer()

        except Exception as e:
            print_exception(e) 

    def wait_on_exit(self):
        if self.enabled == False:
            return

        self.wait_on_exit_thread = threading.Thread(target=self._wait_on_exit)
        self.wait_on_exit_thread.start()
        self.wait_on_exit_thread.join()

    # PositionManagement 
    def send_positions(self, position_list):
        if self.enabled == False:
            return

        if len(self.current_netclient.username) > 0:
            self.vr_management_stub.SendPositions(netsystem_pb2.SendPositionsRequest(username=self.current_netclient.username, position_list=position_list))
    
    # PythonScriptManagement 
    def send_python_script(self, python_script):
        if self.enabled == False:
            return

        if len(self.current_netclient.username) > 0:
            self.vr_management_stub.SendPythonScript(netsystem_pb2.SendPythonScriptRequest(username=self.current_netclient.username, python_script=python_script))
    
    # AudioManagement
    def send_audio(self, audio_data):
        if self.enabled == False:
            return

        if len(self.current_netclient.username) > 0:
            self.vr_management_stub.SendAudio(netsystem_pb2.SendAudioRequest(username=self.current_netclient.username, audio_data=audio_data))

    # def send(self, message):
    #     # bytes = message.encode("utf8")
    #     # self.sock_write.sendall(len(bytes).to_bytes(4, "little"))
    #     # self.sock_write.sendall(bytes)

    # def recv(self):
    #     # len = int.from_bytes(self.sock_read.recv(4), "little")
    #     # data = self.sock_read.recv(len).decode("utf-8")

    #     return

    def replace_tag_in_script(self, python_script):
        # if self.enabled == False:
        #     return python_script

        script = str(python_script)

        if bpy.context.scene.xrsystem.enabled == True:
            pref = bholodeck_pref.preferences()

            c0_name = pref.username + "_CONTROLLER0"
            c1_name = pref.username + "_CONTROLLER1"
            hmd_name = pref.username + "_HMD";

            script = script.replace("{CONTROLLER0}", c0_name)
            script = script.replace("{CONTROLLER1}", c1_name)
            script = script.replace("{HMD}", hmd_name)

        return script

def register():
    """register."""

    bpy.utils.register_class(NetSystemStart)    
    bpy.utils.register_class(NetSystemStop)
    bpy.utils.register_class(VIEW_PT_NetSystemPanel)

    bpy.utils.register_class(NETSYSTEM_OT_sync_data_timer)      

    bpy.utils.register_class(BHOLODECK_PG_UsernamesGroup)
    bpy.utils.register_class(BHOLODECK_UL_UsernamesGroup)
    bpy.utils.register_class(VIEW_PG_NetSystem)

    #bpy.bholodeck_netsystem = NetSystem()
    bpy.types.Scene.netsystem = NetSystem()

    bpy.types.Scene.view_pg_username = bpy.props.CollectionProperty(type=BHOLODECK_PG_UsernamesGroup)
    bpy.types.Scene.view_pg_username_index = bpy.props.IntProperty(default=-1)

    bpy.types.Scene.view_pg_netsystem = bpy.props.PointerProperty(type=VIEW_PG_NetSystem)    

    return


def unregister():
    """unregister."""

    bpy.utils.unregister_class(VIEW_PT_NetSystemPanel)
    bpy.utils.unregister_class(NetSystemStop)
    bpy.utils.unregister_class(NetSystemStart)

    bpy.utils.unregister_class(NETSYSTEM_OT_sync_data_timer)

    bpy.utils.unregister_class(BHOLODECK_PG_UsernamesGroup)
    bpy.utils.unregister_class(BHOLODECK_UL_UsernamesGroup)
    bpy.utils.unregister_class(VIEW_PG_NetSystem)

    #delattr(bpy, "bholodeck_netsystem")
    delattr(bpy.types.Scene, "view_pg_netsystem")

    delattr(bpy.types.Scene, "netsystem")
    delattr(bpy.types.Scene, "view_pg_username")
    delattr(bpy.types.Scene, "view_pg_username_index")

    return