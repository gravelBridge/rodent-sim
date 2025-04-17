#!/usr/bin/env python3
import subprocess
import os
import time
import sys
import platform

# Configuration
# For cloud models, set this to None or "" - we'll use the --open command-line option instead
FUSION_MODEL_PATH = None
# Alternative: Use a cloud document URL or ID if you have it
FUSION_CLOUD_DOCUMENT_URL = "fusion360://design/files?id=DT3b582QT3672c5e0db8ac93759b7df2570d"  # Replace with your document ID/URL
GRID_IMAGES_SCRIPT = "/Users/gravelbridge/Desktop/blairlab_fusion/dynamic/grid_images.py"

def get_fusion_path():
    """Get the path to Fusion 360 based on the operating system."""
    if platform.system() == "Darwin":  # macOS
        return "/Users/gravelbridge/Applications/Autodesk Fusion.app/Contents/MacOS/Autodesk Fusion"
    elif platform.system() == "Windows":
        # Common installation paths on Windows
        possible_paths = [
            os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Autodesk", "Fusion 360", "Fusion360.exe"),
            os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "Autodesk", "Fusion 360", "Fusion360.exe")
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None
    else:
        print(f"Unsupported operating system: {platform.system()}")
        return None

def create_run_script():
    """Create a temporary script that will run the grid_images.py script."""
    temp_script_path = os.path.join(os.path.dirname(GRID_IMAGES_SCRIPT), "temp_runner.py")
    
    with open(temp_script_path, "w") as f:
        f.write("""import adsk.core
import adsk.fusion
import importlib.util
import sys
import os
import time

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        # Make sure a document is active - wait if needed
        retries = 0
        max_retries = 30  # 30 seconds
        while not app.activeDocument and retries < max_retries:
            print("Waiting for document to load...")
            time.sleep(1)
            retries += 1
            adsk.doEvents()
        
        if not app.activeDocument:
            ui.messageBox('No active document after waiting. Please open your model manually.')
            return
            
        # Load the grid_images script
        script_path = r"{}"
        spec = importlib.util.spec_from_file_location("grid_images", script_path)
        grid_images = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(grid_images)
        
        # Run the script
        grid_images.run(context)
        
        # Optional: Close Fusion after completion
        # app.quit()
        
    except Exception as e:
        if ui:
            ui.messageBox('Failed:\\n{{}}'.format(str(e)))
""".format(GRID_IMAGES_SCRIPT.replace('\\', '\\\\')))
    
    return temp_script_path

def create_autodesk_script_location():
    """Create a script in the default Autodesk scripts location that will run our script."""
    # Find the user scripts folder
    if platform.system() == "Darwin":  # macOS
        scripts_folder = os.path.expanduser("~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/Scripts")
    elif platform.system() == "Windows":
        scripts_folder = os.path.expanduser("~/AppData/Roaming/Autodesk/Autodesk Fusion 360/API/Scripts")
    else:
        print(f"Unsupported operating system: {platform.system()}")
        return None
    
    # Create the scripts folder if it doesn't exist
    os.makedirs(scripts_folder, exist_ok=True)
    
    # Create the script file
    script_path = os.path.join(scripts_folder, "AutoGridImagesRunner.py")
    
    with open(script_path, "w") as f:
        f.write("""import adsk.core
import adsk.fusion
import importlib.util
import sys
import os
import time

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        # Make sure a document is active - wait if needed
        retries = 0
        max_retries = 30  # 30 seconds
        while not app.activeDocument and retries < max_retries:
            print("Waiting for document to load...")
            time.sleep(1)
            retries += 1
            adsk.doEvents()
        
        if not app.activeDocument:
            ui.messageBox('No active document after waiting. Please open your model manually.')
            return
            
        # Load the grid_images script
        script_path = r"{}"
        spec = importlib.util.spec_from_file_location("grid_images", script_path)
        grid_images = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(grid_images)
        
        # Run the script
        grid_images.run(context)
        
    except Exception as e:
        if ui:
            ui.messageBox('Failed:\\n{{}}'.format(str(e)))
""".format(GRID_IMAGES_SCRIPT.replace('\\', '\\\\')))
    
    return script_path

def main():
    # Get Fusion 360 path
    fusion_path = get_fusion_path()
    if not fusion_path:
        print("Could not find Fusion 360 installation.")
        sys.exit(1)
    
    # Check if script file exists
    if not os.path.exists(GRID_IMAGES_SCRIPT):
        print(f"Script file not found: {GRID_IMAGES_SCRIPT}")
        sys.exit(1)
    
    # Method 1: Create a script in the default Autodesk scripts location
    autodesk_script_path = create_autodesk_script_location()
    
    # Fusion Command Line options for cloud-based model
    command = [fusion_path]
    
    # If we have a cloud URL, add it to the command
    if FUSION_CLOUD_DOCUMENT_URL:
        command.append("--open")
        command.append(FUSION_CLOUD_DOCUMENT_URL)
    
    # Add script to run after startup
    command.append("/run")
    command.append(autodesk_script_path)
    
    print("Starting Fusion 360 with automatic script execution...")
    print(f"Running command: {' '.join(command)}")
    
    # Launch Fusion 360 and run script
    fusion_process = subprocess.Popen(command)
    
    print("\nFusion 360 started.")
    print("You'll need to:")
    print("1. Log in to your Autodesk account if prompted")
    print("2. Open your cloud model manually if it doesn't open automatically")
    print("3. The script should run once the model is open")
    print("\nIf the script doesn't run automatically, you can run it manually:")
    print(f"1. In Fusion 360, click on Scripts and Add-Ins (or press Shift+S)")
    print(f"2. Find and select 'AutoGridImagesRunner' in the Scripts tab")
    print(f"3. Click Run")
    
    # Wait for Fusion process to complete
    fusion_process.wait()
    
    print("Fusion 360 has closed. Script execution complete.")

if __name__ == "__main__":
    main() 