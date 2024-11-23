import adsk.core, adsk.fusion, adsk.cam, traceback
import time
import math
import os

# Initialize the Fusion 360 app and UI
app = adsk.core.Application.get()
ui = app.userInterface

def switch_to_render_workspace():
    render_workspace = ui.workspaces.itemById('FusionRenderEnvironment')
    if render_workspace:
        if ui.activeWorkspace != render_workspace:
            render_workspace.activate()
            adsk.doEvents()
            time.sleep(2)
    else:
        ui.messageBox("Render workspace not found.")
        return False
    return True

def switch_to_design_workspace():
    design_workspace = ui.workspaces.itemById('FusionSolidEnvironment')
    if design_workspace:
        design_workspace.activate()
    else:
        ui.messageBox("Design workspace not found.")
        return False
    return True

def inches_to_cm(value_in_inches):
    return value_in_inches * 2.54

def calculate_view_target(position, heading, pitch):
    """
    Calculates the target point for the rat's view based on position, heading, and pitch.
    """
    heading_rad = math.radians(heading)
    pitch_rad = math.radians(pitch)
    
    # Direction vector components
    dx = math.cos(pitch_rad) * math.cos(heading_rad)
    dy = math.cos(pitch_rad) * math.sin(heading_rad)
    dz = math.sin(pitch_rad)
    
    # Target point at a reasonable distance along the direction vector
    # Adjust the distance based on the scale of your model
    distance = 100  # cm, adjust as needed
    target_x = position[0] + dx * distance
    target_y = position[1] + dy * distance
    target_z = position[2] + dz * distance
    
    target = adsk.core.Point3D.create(target_x, target_y, target_z)
    return target

def calculate_eye_positions(position, heading, EYE_SEPARATION):
    """
    Calculates the positions of the left and right eyes based on the position and heading.
    """
    heading_rad = math.radians(heading)
    
    # Direction vectors for left/right offset
    left_x = -math.sin(heading_rad)
    left_y = math.cos(heading_rad)
    
    # Half of the eye separation
    half_eye_sep = EYE_SEPARATION / 2.0
    
    # Create eye positions
    left_eye = adsk.core.Point3D.create(
        position[0] + left_x * half_eye_sep,
        position[1] + left_y * half_eye_sep,
        position[2]
    )
    
    right_eye = adsk.core.Point3D.create(
        position[0] - left_x * half_eye_sep,
        position[1] - left_y * half_eye_sep,
        position[2]
    )
    
    return left_eye, right_eye

def set_camera_for_eye(viewport, eye_position, target, fov):
    camera = viewport.camera
    camera.isSmoothTransition = False
    camera.isPerspective = True
    camera.eye = eye_position
    camera.target = target
    camera.upVector = adsk.core.Vector3D.create(0, 0, 1)
    camera.viewAngle = fov
    viewport.camera = camera
    adsk.doEvents()
    
def render_and_save_image(viewport, output_path):
    try:
        success = viewport.saveAsImageFile(output_path, 1200, 1200)
        if not success:
            ui.messageBox(f'Failed to save image at {output_path}')
            return False
        return True
    except Exception as e:
        ui.messageBox(f'Error saving image {output_path}: {str(e)}')
        return False
        
def run(context):
    try:
        # Constants
        EYE_SEPARATION = inches_to_cm(0.5)  # Rat's eye separation in cm
        MONOCULAR_FOV = 150  # Field of view in degrees per eye
        EYE_HEIGHT = inches_to_cm(33.577 + 1)  # Constant height in cm
        PITCH_ANGLE = 15  # Degrees upward
        
        # Grid coordinates
        GRID = {
            'bottom_left': {'x': inches_to_cm(16.336), 'y': inches_to_cm(14.317)},
            'top_left': {'x': inches_to_cm(16.336), 'y': inches_to_cm(92.683)},
            'top_right': {'x': inches_to_cm(94.702), 'y': inches_to_cm(92.683)},
            'bottom_right': {'x': inches_to_cm(94.702), 'y': inches_to_cm(14.317)},
            'middle': {'x': inches_to_cm(55.519), 'y': inches_to_cm(53.50)}
        }
    
        OUTPUT_DIR = '/Users/gravelbridge/Desktop/RatEyes/track_images'
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
    
        # Switch to render workspace
        if not switch_to_render_workspace():
            return
    
        viewport = app.activeViewport
    
        # Only middle position
        positions = [
            (GRID['middle']['x'], GRID['middle']['y'], EYE_HEIGHT)
        ]
    
        # Cardinal directions (0 = East, 90 = North, 180 = West, 270 = South)
        headings = [0, 90, 180, 270]
    
        for position in positions:
            for heading in headings:
                # Calculate target point (where the rat is looking), with pitch
                target = calculate_view_target(position, heading, PITCH_ANGLE)
                
                # Calculate eye positions
                left_eye, right_eye = calculate_eye_positions(position, heading, EYE_SEPARATION)
    
                # Render left eye view
                set_camera_for_eye(viewport, left_eye, target, MONOCULAR_FOV)
                time.sleep(0.5)
                output_path = os.path.join(
                    OUTPUT_DIR, 
                    f'left_x{position[0]/2.54:.2f}_y{position[1]/2.54:.2f}_h{heading}.png'
                )
                render_and_save_image(viewport, output_path)
    
                # Render right eye view
                set_camera_for_eye(viewport, right_eye, target, MONOCULAR_FOV)
                time.sleep(0.5)
                output_path = os.path.join(
                    OUTPUT_DIR, 
                    f'right_x{position[0]/2.54:.2f}_y{position[1]/2.54:.2f}_h{heading}.png'
                )
                render_and_save_image(viewport, output_path)
    
        # Switch back to design workspace
        switch_to_design_workspace()
        ui.messageBox("Script completed successfully.")
    
    except Exception as e:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
