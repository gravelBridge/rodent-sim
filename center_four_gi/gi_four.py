import adsk.core, adsk.fusion, adsk.cam, traceback
import math

# Initialize the Fusion 360 app and UI
app = adsk.core.Application.get()
ui = app.userInterface

# Global position index (1-8)
# 1: Middle facing East (Left eye)
# 2: Middle facing East (Right eye)
# 3: Middle facing North (Left eye)
# 4: Middle facing North (Right eye)
# 5: Middle facing West (Left eye)
# 6: Middle facing West (Right eye)
# 7: Middle facing South (Left eye)
# 8: Middle facing South (Right eye)
POSITION_INDEX = 1

def switch_to_render_workspace():
    render_workspace = ui.workspaces.itemById('FusionRenderEnvironment')
    if render_workspace:
        if ui.activeWorkspace != render_workspace:
            render_workspace.activate()
            adsk.doEvents()
    else:
        ui.messageBox("Render workspace not found.")
        return False
    return True

def inches_to_cm(value_in_inches):
    return value_in_inches * 2.54

def calculate_view_target(position, heading, pitch, heading_offset):
    """
    Calculates the target point for the rat's view based on position, heading, pitch, and heading offset.
    """
    adjusted_heading = heading + heading_offset
    heading_rad = math.radians(adjusted_heading)
    pitch_rad = math.radians(pitch)
    
    # Direction vector components
    dx = math.cos(pitch_rad) * math.cos(heading_rad)
    dy = math.cos(pitch_rad) * math.sin(heading_rad)
    dz = math.sin(pitch_rad)
    
    # Target point at a reasonable distance along the direction vector
    distance = 100  # cm
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

def set_camera_for_eye(viewport, eye_position, target, vertical_fov_degrees):
    camera = viewport.camera
    camera.isSmoothTransition = False
    camera.isPerspective = True
    camera.eye = eye_position
    camera.target = target
    camera.upVector = adsk.core.Vector3D.create(0, 0, 1)
    # Set the vertical FOV
    camera.viewAngle = math.radians(vertical_fov_degrees)
    viewport.camera = camera
    adsk.doEvents()

def set_camera_position(index):
    try:
        # Switch to render workspace first
        if not switch_to_render_workspace():
            return

        # Constants
        EYE_SEPARATION = inches_to_cm(0.5)  # Rat's eye separation in cm
        EYE_HEIGHT = inches_to_cm(33.577 + 2.5)  # Rat's eye height from ground in cm
        PITCH_ANGLE = 15  # Degrees upward
        EYE_OFFSET_ANGLE = 50  # Degrees offset from straight ahead for each eye
        
        # Desired fields of view
        desired_vertical_fov = 150  # degrees

        # Middle position coordinates
        position = (
            inches_to_cm(55.519),  # x
            inches_to_cm(53.50),   # y
            EYE_HEIGHT             # z
        )

        # Map index to heading and eye
        direction_map = {
            1: {"heading": 0, "eye": "left"},     # East, Left eye
            2: {"heading": 0, "eye": "right"},    # East, Right eye
            3: {"heading": 90, "eye": "left"},    # North, Left eye
            4: {"heading": 90, "eye": "right"},   # North, Right eye
            5: {"heading": 180, "eye": "left"},   # West, Left eye
            6: {"heading": 180, "eye": "right"},  # West, Right eye
            7: {"heading": 270, "eye": "left"},   # South, Left eye
            8: {"heading": 270, "eye": "right"}   # South, Right eye
        }

        if index not in direction_map:
            ui.messageBox("Invalid position index. Please use a number from 1-8.")
            return

        # Get heading and eye type
        heading = direction_map[index]["heading"]
        eye_type = direction_map[index]["eye"]
        
        # Calculate eye positions
        left_eye, right_eye = calculate_eye_positions(position, heading, EYE_SEPARATION)
        
        # Set camera based on eye type
        if eye_type == "left":
            eye_position = left_eye
            heading_offset = EYE_OFFSET_ANGLE
        else:
            eye_position = right_eye
            heading_offset = -EYE_OFFSET_ANGLE
            
        target = calculate_view_target(position, heading, PITCH_ANGLE, heading_offset)
        set_camera_for_eye(app.activeViewport, eye_position, target, desired_vertical_fov)
        
        direction_names = {0: "East", 90: "North", 180: "West", 270: "South"}
        ui.messageBox(f"Camera positioned for {eye_type.upper()} eye, facing {direction_names[heading]}.")

    except Exception as e:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
            
def run(context):
    try:
        global POSITION_INDEX
        set_camera_position(POSITION_INDEX)
    except Exception as e:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))