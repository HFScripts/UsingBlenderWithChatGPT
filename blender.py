import os
import speech_recognition as sr
import openai
import requests
import json
import bpy
from gtts import gTTS
from pydub.utils import mediainfo
from pydub import AudioSegment

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
def get_audio():
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
                # Example usage
                animate_text(ChatGPTresponse)
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

def animate_text(ChatGPTresponse):
    # Call the elvenlabs_audio function to create an audio file
    elvenlabs_audio(ChatGPTresponse)

    # Define the audio file path
    audio_filepath = os.path.join(bpy.path.abspath("//"), 'output.mp3')

    # Get the duration of the audio file in seconds
    audio_duration = get_audio_duration(audio_filepath)

    # Import the audio file into Blender
    sound = bpy.data.sounds.load(audio_filepath)

    # Create a new scene and link it to the sequence editor
    sequence_editor = bpy.context.scene.sequence_editor_create()

    # Create a new sound strip
    sound_strip = sequence_editor.sequences.new_sound("Sound", audio_filepath, 1, 1)

    # Time per character in seconds, assuming a uniform distribution
    # This is a very rough approximation and won't match the audio well for real speech
    time_per_char = audio_duration / len(ChatGPTresponse)

    # Frame rate of the scene
    frame_rate = bpy.context.scene.render.fps

    # Get the current frame
    current_frame = bpy.context.scene.frame_current

    # Iterate over all objects in the scene
    for obj in bpy.context.scene.objects:
        # Check if the object is a mesh
        if obj.type == 'MESH':
            mesh = obj.data

            # Check if the mesh has shape keys
            if mesh.shape_keys is not None:
                # Store the original frame value to restore later
                original_frame = current_frame

                # Iterate over all characters in response
                for i, char in enumerate(ChatGPTresponse.lower()):  # converting to lowercase to match keys
                    shape_key_name = character_to_shapekey.get(char)
                    if shape_key_name is not None:
                        key_block = mesh.shape_keys.key_blocks.get(shape_key_name)
                        if key_block is not None:
                            # Calculate the start frame for this shape key from the timing information
                            start_frame = i * time_per_char * frame_rate

                            # Set the current frame to the start frame
                            bpy.context.scene.frame_set(int(start_frame))

                            # Set the shape key value to 0
                            key_block.value = 0.0

                            # Insert keyframe at current frame
                            key_block.keyframe_insert("value")

                            # Increment the frame
                            bpy.context.scene.frame_set(int(start_frame + 10))

                            # Set the shape key value to 1
                            key_block.value = 1.0

                            # Insert keyframe at current frame
                            key_block.keyframe_insert("value")

                            # Increment the frame
                            bpy.context.scene.frame_set(int(start_frame + 20))

                            # Set the shape key value back to 0
                            key_block.value = 0.0

                            # Insert keyframe at current frame
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
        mp3_file = os.path.join(blend_file_directory, 'output.mp3')
        with open(mp3_file, 'wb') as f:
            f.write(response.content)
        print("MP3 file saved to:", mp3_file)
    else:
        print("Failed to download MP3 file. Status code:", response.status_code)

def get_audio_duration(file_path):
    audio = AudioSegment.from_mp3(file_path)
    return len(audio) / 1000  # AudioSegment's duration is in milliseconds

# Continuously listen for audio and send to OpenAI
while True:
    get_audio()
