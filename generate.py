import adsk.core, adsk.fusion, adsk.cam, traceback
import time
import math
import os

# Initialize the Fusion 360 app and UI
app = adsk.core.Application.get()
ui = app.userInterface

def switch_to_render_workspace():
    # Get the workspace with the name 'Render'
    render_workspace = ui.workspaces.itemById('FusionRenderEnvironment')
    
    if render_workspace:
        # Check if the current workspace is not Render
        if ui.activeWorkspace != render_workspace:
            ui.messageBox("Switching to Render workspace.")
            render_workspace.activate()  # Activate the Render workspace
            # Allow some time for the workspace switch
            adsk.doEvents()
            time.sleep(2)
        else:
            ui.messageBox("Already in Render workspace.")
    else:
        ui.messageBox("Render workspace not found.")
        return False
    return True

def switch_to_design_workspace():
    # Get the workspace with the name 'Design'
    design_workspace = ui.workspaces.itemById('FusionSolidEnvironment')
    
    if design_workspace:
        # Activate the Design workspace
        design_workspace.activate()
        ui.messageBox("Switched back to Design workspace.")
    else:
        ui.messageBox("Design workspace not found.")
        return False
    return True

def calculate_eye_positions(head_center, heading, EYE_SEPARATION):
    """
    Calculates the positions of the left and right eyes based on the head center and heading.
    """
    # Convert heading to radians
    heading_rad = math.radians(heading)

    # Direction vectors
    forward = adsk.core.Vector3D.create(math.cos(heading_rad), math.sin(heading_rad), 0)
    left = adsk.core.Vector3D.create(-math.sin(heading_rad), math.cos(heading_rad), 0)

    # Half of the interocular distance
    half_eye_sep = EYE_SEPARATION / 2.0

    # Left eye position
    left_eye_pos = adsk.core.Point3D.create(
        head_center.x + left.x * half_eye_sep,
        head_center.y + left.y * half_eye_sep,
        head_center.z
    )

    # Right eye position
    right_eye_pos = adsk.core.Point3D.create(
        head_center.x - left.x * half_eye_sep,
        head_center.y - left.y * half_eye_sep,
        head_center.z
    )

    # Target point (a point ahead of the eyes)
    target = adsk.core.Point3D.create(
        head_center.x + forward.x,
        head_center.y + forward.y,
        head_center.z
    )

    return left_eye_pos, right_eye_pos, target

def set_camera_for_eye(viewport, eye_position, target, fov):
    # Set up the camera
    camera = viewport.camera
    camera.isSmoothTransition = False
    camera.isPerspective = True  # Ensure perspective view
    camera.eye = eye_position
    camera.target = target
    camera.upVector = adsk.core.Vector3D.create(0, 0, 1)  # Assuming up is along Z-axis
    camera.viewAngle = fov  # Set field of view
    viewport.camera = camera  # Apply the camera settings
    adsk.doEvents()

def render_and_save_image(viewport, output_path):
    # Capture the image
    try:
        # Use saveAsImageFile method
        success = viewport.saveAsImageFile(output_path, 1920, 1080)
        if not success:
            ui.messageBox(f'Failed to save image at {output_path}')
            return False
        # Fusion 360 may not support saving images in grayscale directly
        # Consider using an external tool or post-process if needed
    except Exception as e:
        ui.messageBox(f'Error saving image {output_path}: {e}')
        return False
    return True

def run(context):
    ui.messageBox("Script started.")
    try:
        # Rat visual parameters
        EYE_SEPARATION = 1.0  # in inches, adjust as needed
        MONOCULAR_FOV = 140  # degrees
        EYE_HEIGHT = 35  # Eye height in inches

        # Output directory for images
        OUTPUT_DIR = '/Users/gravelbridge/Desktop/RatEyes/stack_images'  # Adjust the path accordingly

        # Switch to Render workspace
        ui.messageBox("Switching to Render workspace.")
        if not switch_to_render_workspace():
            ui.messageBox("Failed to switch to Render workspace.")
            return

        viewport = app.activeViewport

        # Define positions within the maze
        # Adjust the start, end, and step values as per your maze dimensions

        # Example maze dimensions (in inches)
        start_x = 0.0
        end_x = 100.0  # Adjust as per your maze size
        step_x = 10.0  # Adjust step size as needed

        start_y = 0.0
        end_y = 100.0  # Adjust as per your maze size
        step_y = 10.0  # Adjust step size as needed

        x_positions = []
        y_positions = []
        x = start_x
        while x <= end_x:
            x_positions.append(x)
            x += step_x

        y = start_y
        while y <= end_y:
            y_positions.append(y)
            y += step_y

        positions = [(x, y, EYE_HEIGHT) for x in x_positions for y in y_positions]

        # Define headings
        headings = [0, 90, 180, 270]  # Degrees

        # Ensure output directory exists
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)

        for position in positions:
            for heading in headings:
                head_center = adsk.core.Point3D.create(position[0], position[1], position[2])
                left_eye_pos, right_eye_pos, target = calculate_eye_positions(head_center, heading, EYE_SEPARATION)

                # Set camera for left eye
                set_camera_for_eye(viewport, left_eye_pos, target, MONOCULAR_FOV)
                adsk.doEvents()
                time.sleep(1)  # Allow time for the camera to update
                output_path_left = os.path.join(OUTPUT_DIR, f'left_{position[0]}_{position[1]}_{heading}.png')
                render_and_save_image(viewport, output_path_left)

                # Set camera for right eye
                set_camera_for_eye(viewport, right_eye_pos, target, MONOCULAR_FOV)
                adsk.doEvents()
                time.sleep(1)
                output_path_right = os.path.join(OUTPUT_DIR, f'right_{position[0]}_{position[1]}_{heading}.png')
                render_and_save_image(viewport, output_path_right)

        # Switch back to Design workspace
        ui.messageBox("Switching back to Design workspace.")
        switch_to_design_workspace()
        ui.messageBox("Script completed successfully.")
    except Exception as e:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
