import os
import subprocess
import glob

# Change this path if Blender is installed in a different location
blender_install_path = r"C:\Program Files\Blender Foundation"

# Find the Blender version
os.chdir(blender_install_path)
blender_version = glob.glob("Blender*")[0]
blender_version_number = blender_version.split()[1]

# Construct the paths to the Python executable and site-packages
python_executable = os.path.join(
    blender_install_path, blender_version, blender_version_number, "python", "bin", "python.exe"
)
site_packages_path = os.path.join(
    blender_install_path, blender_version, blender_version_number, "python", "lib", "site-packages"
)

# Run the commands
commands = [
    f'"{python_executable}" -m ensurepip',
    f'"{python_executable}" -m pip install --upgrade pip',
    f'"{python_executable}" -m pip install --target "{site_packages_path}" SpeechRecognition',
    f'"{python_executable}" -m pip install --target "{site_packages_path}" bpy',
    f'"{python_executable}" -m pip install --target "{site_packages_path}" PyAudio',
    f'"{python_executable}" -m pip install --target "{site_packages_path}" openai',
    f'"{python_executable}" -m pip install --target "{site_packages_path}" gtts',
    f'"{python_executable}" -m pip install --target "{site_packages_path}" pydub',
    f'"{python_executable}" -m pip install --target "{site_packages_path}" mutagen',
]

for command in commands:
    subprocess.run(command, shell=True)
