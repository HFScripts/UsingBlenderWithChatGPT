import os
import speech_recognition as sr
import openai
import requests
import json
import bpy
from gtts import gTTS
from pydub.utils import mediainfo
from pydub import AudioSegment
import time
from mutagen.mp3 import MP3

# Using phoenem based speech should fix the over calculation of keyframes.
# Using googles text to speech API also gives timings for each word but the voice isn't something we want.

# Set up OpenAI credentials
openai.api_key = "APIKEYHERE"

# Set up Elvenlabs credentials
api_key = "APIKEYHERE"

# Mapping characters to shape key names
character_to_shapekey = {
    'a': '10 a',
    'i': '11 i',
    'u': '12 u',
    'e': '13 e',
    'o': '14 o',
}

# Check if a sequence editor exists, create one if not
if bpy.context.scene.sequence_editor is None:
    bpy.context.scene.sequence_editor_create()

# Clear the current sequence editor by removing all sound strips
sequence_editor = bpy.context.scene.sequence_editor
if sequence_editor:
    for strip in sequence_editor.sequences_all:
        sequence_editor.sequences.remove(strip)

# Clear the current timeline markers
bpy.context.scene.timeline_markers.clear()

# Iterate over all objects in the scene
for obj in bpy.context.scene.objects:
    # Check if the object is a mesh
    if obj.type == 'MESH':
        mesh = obj.data

        # Check if the mesh has shape keys
        if mesh.shape_keys is not None:
            # Remove all shape key animation data
            if mesh.animation_data is not None:
                mesh.animation_data_clear()

# Define the function to get audio and send to OpenAI
def get_audio(context):
    
    # Check if a sequence editor exists, create one if not
    if bpy.context.scene.sequence_editor is None:
        bpy.context.scene.sequence_editor_create()
    
    # Clear the current sequence editor by removing all sound strips
    sequence_editor = bpy.context.scene.sequence_editor
    if sequence_editor:
        for strip in sequence_editor.sequences_all:
            sequence_editor.sequences.remove(strip)
    
    # Clear the current timeline markers
    bpy.context.scene.timeline_markers.clear()
    
    # Iterate over all objects in the scene
    for obj in bpy.context.scene.objects:
        # Check if the object is a mesh
        if obj.type == 'MESH':
            mesh = obj.data
    
            # Check if the mesh has shape keys
            if mesh.shape_keys is not None:
                # Remove all shape key animation data
                if mesh.animation_data is not None:
                    mesh.animation_data_clear()
                    
    # Record audio from microphone
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Say something!")
        audio = r.listen(source)

    # Convert audio to text using speech recognition library
    try:
        text = r.recognize_google(audio)
        print("You said: " + text)

        # Check if the user said "ask AI" and send the rest of the text to OpenAI
        if "ask AI" in text:
            said = text.split("ask AI", 1)[1].strip()
            tosend = "respond in a short precise manner" + said
            print("Sending to OpenAI: " + said)
            try:
                completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": tosend}])
                ChatGPTresponse = completion.choices[0].message.content
                print("OpenAI response: " + ChatGPTresponse)
                
                # Call the elvenlabs_audio function to create an audio file
                mp3_file = elvenlabs_audio(ChatGPTresponse)
                if mp3_file is not None:
                    animate_text(ChatGPTresponse, mp3_file)
                    
            except openai.OpenAIError as e:
                print("OpenAI API error:", e)
        else:
            print("Please say 'ask AI' followed by your question or statement.")
    except sr.UnknownValueError:
        print("Could not understand audio")
        return
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))
        return
    context.scene.audio_listen_running = False


# Call the elvenlabs_audio function to create an audio file
def animate_text(ChatGPTresponse, audio_filepath):
    # Get the duration of the audio file in seconds
    audio_duration = get_audio_duration(audio_filepath)
    print(f"audio_duration is {audio_duration}")

    # Import the audio file into Blender
    sound = bpy.data.sounds.load(audio_filepath)

    # Create a new scene and link it to the sequence editor
    sequence_editor = bpy.context.scene.sequence_editor_create()

    # Create a new sound strip
    sound_strip = sequence_editor.sequences.new_sound("Sound", audio_filepath, 1, 1)

    # Frame rate of the scene
    frame_rate = bpy.context.scene.render.fps

    # Get the current frame
    current_frame = bpy.context.scene.frame_current

    # Total number of frames available for animation
    total_frames = round(audio_duration * frame_rate)

    # Split the response into words
    words = ChatGPTresponse.split()

    # Frames per word, rounded down to the nearest integer
    frames_per_word = int(total_frames / len(words))
    print(f"frames per word is {frames_per_word}")
    # Iterate over all objects in the scene
    for obj in bpy.context.scene.objects:
        # Check if the object is a mesh
        if obj.type == 'MESH':
            mesh = obj.data

            # Check if the mesh has shape keys
            if mesh.shape_keys is not None:
                # Store the original frame value to restore later
                original_frame = current_frame

                # Reset all shape keys to default position (0)
                for key_block in mesh.shape_keys.key_blocks:
                    key_block.value = 0
                    key_block.keyframe_insert("value", frame=current_frame)  # Insert keyframe for initial state

                # Iterate over all words in response
                for i, word in enumerate(words):
                    for char in word.lower():  # converting to lowercase to match keys
                        shape_key_name = character_to_shapekey.get(char)
                        if shape_key_name is not None:
                            key_block = mesh.shape_keys.key_blocks.get(shape_key_name)
                            if key_block is not None:
                                # Calculate the start frame for this shape key from the timing information
                                start_frame = i * frames_per_word

                                # Set the current frame to the start frame
                                bpy.context.scene.frame_set(int(start_frame))

                                # Set the shape key value to the maximum value
                                if shape_key_name == '14 o':  # o max value 0.486957
                                    key_block.value = 0.486957
                                elif shape_key_name == '13 e':  # e max value 0.478261
                                    key_block.value = 0.478261
                                elif shape_key_name == '12 u':  # u max value 1
                                    key_block.value = 1.0
                                elif shape_key_name == '11 i':  # i max value 1
                                    key_block.value = 1.0
                                elif shape_key_name == '10 a':  # a max value 1
                                    key_block.value = 1.0

                                # Insert keyframe at current frame
                                key_block.keyframe_insert("value")

                                # Insert keyframe to reset value to 0 at the next frame
                                bpy.context.scene.frame_set(int(start_frame + frames_per_word))
                                key_block.value = 0
                                key_block.keyframe_insert("value")

                # Restore the original frame value
                current_frame = original_frame
                bpy.context.scene.frame_set(current_frame)


def elvenlabs_audio(ChatGPTresponse):
    url = 'https://api.elevenlabs.io/v1/text-to-speech/TxGEqnHWrfWFTfGW9XjX/stream?optimize_streaming_latency=0'

    headers = {
        'accept': '*/*',
        'xi-api-key': api_key,
        'Content-Type': 'application/json'
    }

    data = {
        "text": ChatGPTresponse,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0,
            "similarity_boost": 0
        }
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        # Get the current blend file directory
        blend_file_directory = bpy.path.abspath("//")
        # Create a unique filename using a timestamp
        timestamp = str(int(time.time()))
        mp3_file = os.path.join(blend_file_directory, 'output' + timestamp + '.mp3')
        with open(mp3_file, 'wb') as f:
            f.write(response.content)
        print("MP3 file saved to:", mp3_file)
        return mp3_file  # Return the filename
    else:
        print("Failed to download MP3 file. Status code:", response.status_code)
        return None

def get_audio_duration(filepath):
    try:
        audio = MP3(filepath)
        duration_seconds = audio.info.length
        return duration_seconds
    except Exception as e:
        print("Error occurred while getting MP3 duration:", str(e))
        return None

def run_get_audio_in_background(context):
    get_audio(context)
    
class AUDIO_OT_listen_operator(bpy.types.Operator):
    """Operator which runs get_audio"""
    bl_idname = "audio.listen"
    bl_label = "Listen for audio"

    def execute(self, context):
        context.scene.audio_listen_running = True
        get_audio(context)
        return {'FINISHED'}

class AUDIO_PT_listen_panel(bpy.types.Panel):
    """Creates a Panel in the 3D view context of the tools region"""
    bl_label = "Audio Listener"
    bl_idname = "AUDIO_PT_listen"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Audio Listener"

    def draw(self, context):
        layout = self.layout

        # Add the operator to the panel
        row = layout.row()
        row.operator("audio.listen")
        row.enabled = not context.scene.audio_listen_running

# Register the operator and panel
def register():
    bpy.utils.register_class(AUDIO_OT_listen_operator)
    bpy.utils.register_class(AUDIO_PT_listen_panel)
    bpy.types.Scene.audio_listen_running = bpy.props.BoolProperty(default=False)


def unregister():
    bpy.utils.unregister_class(AUDIO_OT_listen_operator)
    bpy.utils.unregister_class(AUDIO_PT_listen_panel)
    del bpy.types.Scene.audio_listen_running

if __name__ == "__main__":
    register()
