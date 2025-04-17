#!/usr/bin/env python3
import subprocess
import os
import time
import sys
import platform

# Configuration
# For cloud models, set this to None
FUSION_MODEL_PATH = None
# Use a cloud document URL/ID - you'll need to manually open your model if this is not set
FUSION_CLOUD_DOCUMENT_URL = None
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
        
    except Exception as e:
        if ui:
            ui.messageBox('Failed:\\n{{}}'.format(str(e)))
""".format(GRID_IMAGES_SCRIPT.replace('\\', '\\\\')))
    
    return temp_script_path

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
    
    # Create the temp runner script
    temp_script_path = create_run_script()
    
    print("Starting Fusion 360...")
    
    # Launch Fusion 360 with or without the model
    command = [fusion_path]
    
    # If we have a cloud URL, add it to the command
    if FUSION_CLOUD_DOCUMENT_URL:
        command.append("--open")
        command.append(FUSION_CLOUD_DOCUMENT_URL)
    elif FUSION_MODEL_PATH and os.path.exists(FUSION_MODEL_PATH):
        command.append(FUSION_MODEL_PATH)
    
    fusion_process = subprocess.Popen(command)
    
    # Give Fusion time to start and load
    print("Waiting for Fusion 360 to start...")
    time.sleep(30)  # Adjust this time based on your system performance
    
    print("\nFusion 360 is now running.")
    print("You'll need to:")
    print("1. Log in to your Autodesk account if prompted")
    print("2. Open your cloud model if it didn't open automatically")
    print("3. Then run the script manually:")
    print(f"   a. In Fusion 360, click on Scripts and Add-Ins (or press Shift+S)")
    print(f"   b. In the Scripts tab, click the + button to add a script")
    print(f"   c. Browse to and select: {temp_script_path}")
    print(f"   d. Select the added script and click Run")
    
    # Wait for Fusion process to complete
    fusion_process.wait()
    
    # Clean up temp file
    if os.path.exists(temp_script_path):
        os.remove(temp_script_path)
    
    print("Fusion 360 has closed. Process complete.")

if __name__ == "__main__":
    main() 