import subprocess
import os

def jojn_user_profile():
    user_profile = os.path.expanduser('~')

    # Construct the complete path to the apsimx directory
    apsimx_path = os.path.join(user_profile, 'apsimx')

    # Print the complete path
    print(apsimx_path)
jojn_user_profile()
# Define the command with expanded environment variables
command = [
    'dotnet',
    'build',
    '-o', os.path.expandvars('%USERPROFILE%\\apsimx'),
    '-c', 'Release',
    'ApsimX/Models/Models.csproj'
]

# Run the command
try:
    subprocess.run(command, check=True, shell=True)
    print("Build successful.")
except subprocess.CalledProcessError as e:
    print(f"Build failed with exit code {e.returncode}.")
