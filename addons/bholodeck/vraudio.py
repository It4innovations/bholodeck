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
import threading

def check_pyaudio():
    import importlib
    pyaudio_spec = importlib.util.find_spec("pyaudio")
    found = pyaudio_spec is not None

    return found

class VRAudioStart(bpy.types.Operator):
    bl_idname = "vraudio.start"
    bl_label = "Audio Start"

    def execute(self,context):
        context.scene.vraudio.start(context)

        return {'FINISHED'}

class VRAudioStop(bpy.types.Operator):
    bl_idname = "vraudio.stop"
    bl_label = "Audio Stop"

    def execute(self,context):
        context.scene.vraudio.stop(context)

        return {'FINISHED'}

class VIEW_PT_VRAudioPanel(bpy.types.Panel):
    bl_label = "VRAudio"
    bl_idname = "VIEW_PT_VRAudioPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BHolodeck"
    
    def draw(self,context):
        layout = self.layout        
        
        row = layout.row()
        if context.scene.vraudio.enabled == False:
            row.operator("vraudio.start")
        else:
            row.operator("vraudio.stop")

# def stream_callback(in_data, frame_count, time_info, status):
#     return bpy.context.scene.vraudio.stream_callback(in_data, frame_count, time_info, status)

class VRAudio:
    def __init__(self):

        if check_pyaudio():
            import pyaudio
            
            self.FORMAT = pyaudio.paInt32
            self.CHANNELS = 1
            self.RATE = 44100
            #self.RATE = 1024
            #self.CHUNK = 4096
            self.CHUNK = 1024

            self.audio = pyaudio.PyAudio()
            #self.audio_sound = pyaudio.PyAudio()
            self.paContinue = pyaudio.paContinue
            
        self.changes_lock = threading.Lock()
        self.audio_data = None
        self.enabled = False

    def volume(self, audio_data, volume_factor):
        from math import sqrt
        import numpy as np
        # convert the linear volume to a logarithmic scale (see explanation below)
        #volume_factor = 2
        volume_multiplier = pow(2, (sqrt(sqrt(sqrt(volume_factor))) * 192 - 192)/6)

        # Doing Something To Data Here To Incrase Volume Of It
        numpy_data = np.fromstring(audio_data, dtype=np.int16)
        # double the volume using the factor computed above
        np.multiply(numpy_data, volume_multiplier, out=numpy_data, casting="unsafe")

        return numpy_data.tostring()

    def play_sound(self, audio_data):
        if self.enabled == False or len(audio_data) == 0: # or len(audio_data) != self.CHUNK:
            return

        self.stream_sound.write(audio_data)

    def stream_callback(self, in_data, frame_count, time_info, status):
        #for s in read_list[1:]:
        #s.send(in_data)

        #self.stream_sound.write(in_data)

        #bpy.context.scene.netsystem.send_audio(in_data)
        self.changes_lock.acquire()
        self.audio_data = in_data
        self.changes_lock.release()

        return (None, self.paContinue)

    def start(self, context):

        # print('\navailable devices:')

        # for i in range(self.audio.get_device_count()):
        #     dev = self.audio.get_device_info_by_index(i)
        #     name = dev['name'].encode('utf-8')
        #     print(i, name, dev['maxInputChannels'], dev['maxOutputChannels'])

        print('\ndefault input & output device:')
        print(self.audio.get_default_input_device_info())
        print(self.audio.get_default_output_device_info())

        # start Recording
        self.stream_mic = self.audio.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE, input=True, frames_per_buffer=self.CHUNK, stream_callback=self.stream_callback, start=False)
        self.stream_sound = self.audio.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE, output=True, frames_per_buffer=self.CHUNK)

        self.stream_mic.start_stream()

        self.enabled = True

    def stop(self, context):
        # stop Recording
        self.stream_mic.stop_stream()
        self.stream_mic.close()
        #self.audio_mic.terminate()

        #self.stream_sound.stop_stream()
        self.stream_sound.close()
        self.audio.terminate()

        self.enabled = False

def register():
    bpy.utils.register_class(VIEW_PT_VRAudioPanel)
    bpy.utils.register_class(VRAudioStart)
    bpy.utils.register_class(VRAudioStop)

    bpy.types.Scene.vraudio = VRAudio()

def unregister():
    delattr(bpy.types.Scene, "vraudio")

    bpy.utils.unregister_class(VIEW_PT_VRAudioPanel)
    bpy.utils.unregister_class(VRAudioStart)
    bpy.utils.unregister_class(VRAudioStop)