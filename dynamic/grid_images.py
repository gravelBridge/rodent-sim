import adsk.core
import adsk.fusion
import adsk.cam
import traceback
import math
import os
import time
import sys
import datetime

# Configuration variables
exit_on_error = True
enable_logging = True  # Set to False to disable logging
log_file_path = "/Users/gravelbridge/Desktop/blairlab_fusion/fusion_script.log"  # Path to the log file

def log_message(message):
    """
    Log a message to the log file if logging is enabled.
    
    Args:
        message (str): Message to log
    """
    if not enable_logging:
        return
        
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    
    try:
        with open(log_file_path, "a") as f:
            f.write(log_entry)
    except Exception as e:
        # Silent failure if logging itself fails
        pass

def get_maze_coordinates(grid_x, grid_y):
    """
    Convert maze grid coordinates to Fusion model coordinates in inches.
    
    Args:
        grid_x (int): X coordinate on the grid (0-12)
        grid_y (int): Y coordinate on the grid (0-12)
    
    Returns:
        tuple: (x, y, z) coordinates in inches
    """
    log_message(f"get_maze_coordinates({grid_x}, {grid_y}) called")
    # Validate input coordinates
    if not (0 <= grid_x <= 12 and 0 <= grid_y <= 12):
        log_message(f"ERROR: Invalid grid coordinates ({grid_x}, {grid_y})")
        raise ValueError("Grid coordinates must be between 0 and 12")
    
    # Known reference points (grid_x, grid_y): (x_inches, y_inches)
    reference_points = {
        (1, 1): (8.039, 100.98),
        (2, 2): (16.336, 92.683),
        (6, 2): (55.519, 92.683),
        (6, 6): (55.519, 53.50),
        (10, 2): (94.702, 92.683),
        (11, 1): (102.999, 100.98),
        (2, 10): (16.336, 21.973),
        (1, 11): (8.039, 6.02),
        (11, 11): (102.999, 6.02)
    }
    
    Z_HEIGHT = 33.577

    # If the coordinate is one of our reference points, return it exactly
    if (grid_x, grid_y) in reference_points:
        x, y = reference_points[(grid_x, grid_y)]
        return (x, y, Z_HEIGHT)

    # Special handling for x coordinates
    if grid_x == 1:
        x = 8.039
    elif grid_x == 11:
        x = 102.999
    else:
        # For regular columns (2-10), use the reference points at y=2
        x_step = (94.702 - 16.336) / 8  # Distance between x=2 and x=10 at y=2
        x = 16.336 + (grid_x - 2) * x_step

    # Special handling for y coordinates
    if grid_y == 1:
        y = 100.98
    elif grid_y == 11:
        y = 6.02
    else:
        # Using (6,2) and (6,6) as reference for y-step calculation
        y_step = (92.683 - 53.50) / 4  # Distance between y=2 and y=6 at x=6
        if grid_y <= 6:
            y = 92.683 - (grid_y - 2) * y_step
        else:
            # For y > 6, interpolate between y=6 and y=10
            y_step_lower = (53.50 - 21.973) / 4  # Distance between y=6 and y=10
            y = 53.50 - (grid_y - 6) * y_step_lower

    coords = (round(x, 3), round(y, 3), Z_HEIGHT)
    log_message(f"Calculated coordinates for ({grid_x}, {grid_y}): {coords}")
    return coords

def inches_to_cm(value_in_inches):
    return value_in_inches * 2.54

def switch_to_render_workspace():
    """
    Switches Fusion 360 to the Render workspace if available.
    """
    log_message("Attempting to switch to Render workspace")
    app = adsk.core.Application.get()
    ui = app.userInterface
    render_workspace = ui.workspaces.itemById('FusionRenderEnvironment')
    if render_workspace:
        if ui.activeWorkspace != render_workspace:
            log_message("Activating Render workspace")
            render_workspace.activate()
            adsk.doEvents()
    else:
        log_message("ERROR: Render workspace not found")
        ui.messageBox("Render workspace not found.")
        return False
    log_message("Successfully switched to Render workspace")
    return True

def calculate_view_target(position, heading, pitch, heading_offset):
    """
    Calculates the target point for the rat's view based on position, heading, pitch, and heading offset.
    position: (x, y, z) in cm
    heading, pitch, heading_offset in degrees
    """
    adjusted_heading = heading + heading_offset
    heading_rad = math.radians(adjusted_heading)
    pitch_rad = math.radians(pitch)
    
    # Direction vector components
    dx = math.cos(pitch_rad) * math.cos(heading_rad)
    dy = math.cos(pitch_rad) * math.sin(heading_rad)
    dz = math.sin(pitch_rad)
    
    # Target point at a certain distance along the direction vector
    distance = 100.0  # cm
    target_x = position[0] + dx * distance
    target_y = position[1] + dy * distance
    target_z = position[2] + dz * distance
    
    return adsk.core.Point3D.create(target_x, target_y, target_z)

def calculate_eye_positions(position, heading, EYE_SEPARATION):
    """
    Calculates the positions of the left and right eyes based on the position and heading.
    position is (x, y, z) in cm.
    heading is in degrees.
    EYE_SEPARATION is in cm.
    """
    heading_rad = math.radians(heading)
    
    # Vector perpendicular to heading
    left_x = -math.sin(heading_rad)
    left_y = math.cos(heading_rad)
    
    # Half of the eye separation
    half_eye_sep = EYE_SEPARATION / 2.0
    
    # Left eye
    left_eye = adsk.core.Point3D.create(
        position[0] + left_x * half_eye_sep,
        position[1] + left_y * half_eye_sep,
        position[2]
    )
    
    # Right eye
    right_eye = adsk.core.Point3D.create(
        position[0] - left_x * half_eye_sep,
        position[1] - left_y * half_eye_sep,
        position[2]
    )
    
    return left_eye, right_eye

def set_camera_for_eye(viewport, eye_position, target, vertical_fov_degrees):
    """
    Configures the camera for the given eye position and target point,
    using a specified vertical field of view (in degrees).
    Clamps FOV to avoid invalid parameter errors.
    """
    camera = viewport.camera
    camera.isSmoothTransition = False
    
    # Ensure perspective camera
    camera.cameraType = adsk.core.CameraTypes.PerspectiveCameraType
    
    safe_fov = max(1, min(150, vertical_fov_degrees))
    camera.viewAngle = math.radians(safe_fov)
    
    camera.eye = eye_position
    camera.target = target
    camera.upVector = adsk.core.Vector3D.create(0, 0, 1)
    camera.isFitView = False  # Use exact camera settings (no auto-fit)
    
    # Apply camera to viewport
    viewport.camera = camera
    adsk.doEvents()

def setup_render_settings(width=1920, height=1080):
    """
    Configure rendering settings for high-quality output using the design's Render Manager.
    Returns an adsk.fusion.Rendering object on success, or None on failure.
    """
    log_message(f"Setting up render with dimensions {width}x{height}")
    app = adsk.core.Application.get()
    ui = app.userInterface
    
    try:
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            log_message("ERROR: No active Fusion design found")
            ui.messageBox("No active Fusion design found.")
            if exit_on_error:
                sys.exit(1)
            return None
        
        render_mgr = design.renderManager
        rendering = render_mgr.rendering

        # Set custom aspect ratio and resolution
        rendering.aspectRatio = adsk.fusion.RenderAspectRatios.CustomRenderAspectRatio
        rendering.resolutionWidth = width
        rendering.resolutionHeight = height

        # Set maximum render quality (100 = Excellent)
        rendering.renderQuality = 100
        log_message("Render settings configured successfully")
        return rendering
        
    except Exception as e:
        log_message(f"ERROR in setup_render_settings: {str(e)}\n{traceback.format_exc()}")
        ui.messageBox(f'Failed to setup render settings: {str(e)}')
        if exit_on_error:
            sys.exit(1)
        return None

def perform_render(rendering, camera, filename):
    """
    Perform a local render using the given camera and save to filename.
    Waits for completion before returning True (success) or False (failed).
    """
    log_message(f"Starting render to file: {filename}")
    try:
        # Start the local render
        render_future = rendering.startLocalRender(filename, camera)
        log_message("Render initiated, waiting for completion")
        
        last_progress = -1
        # Poll until render completes or fails
        while render_future.renderState == adsk.fusion.LocalRenderStates.ProcessingLocalRenderState or render_future.renderState == adsk.fusion.LocalRenderStates.QueuedLocalRenderState:
            adsk.doEvents()
            current_progress = round(render_future.progress * 100, 2)
            if current_progress != last_progress and current_progress - last_progress > 3 or current_progress == 100.0:
                log_message(f"Render progress: {current_progress}%")
                last_progress = current_progress
                
            time.sleep(0.5)  # Check more frequently (every second)
        
        # If state is Finished, return True - using correct enum value
        if render_future.renderState == adsk.fusion.LocalRenderStates.FinishedLocalRenderState:
            log_message("Render completed successfully")
            return True
        elif render_future.renderState == adsk.fusion.LocalRenderStates.FailedLocalRenderState:
            log_message(f"Render failed with state: {render_future.renderState}")
            return False
            
        log_message(f"Should not happen, need to check the code carefully ====================")
        return False
        
    except Exception as e:
        log_message(f"ERROR in perform_render: {str(e)}\n{traceback.format_exc()}")
        app = adsk.core.Application.get()
        ui = app.userInterface
        if ui:
            ui.messageBox(f'Failed to perform render: {str(e)}')
            if exit_on_error:
                sys.exit(1)
        return False

def capture_views(grid_positions, output_dir):
    """
    Capture 8 views (4 directions × 2 eyes) for each grid position.
    
    Args:
        grid_positions (list): List of (x, y) tuples representing grid coordinates.
        output_dir (str): Directory to save the rendered images.
    """
    log_message(f"Starting capture_views for {len(grid_positions)} positions to {output_dir}")
    app = adsk.core.Application.get()
    ui = app.userInterface

    try:
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            log_message("ERROR: No active Fusion design")
            ui.messageBox("No active Fusion design.")
            if exit_on_error:
                sys.exit(1)
            return

        # Ensure output directory exists
        if not os.path.exists(output_dir):
            log_message(f"Creating output directory: {output_dir}")
            os.makedirs(output_dir)

        # Switch to Render workspace
        if not switch_to_render_workspace():
            log_message("Failed to switch to Render workspace, aborting")
            if exit_on_error:
                sys.exit(1)
            return

        # Constants
        EYE_SEPARATION = inches_to_cm(0.5)       # 0.5 inches separation, in cm
        EYE_HEIGHT_OFFSET = inches_to_cm(2.5)    # Eye is 2.5 inches above the maze's Z-height
        PITCH_ANGLE = 15
        EYE_OFFSET_ANGLE = 50
        VERTICAL_FOV = 150
        log_message(f"Using constants: EYE_SEPARATION={EYE_SEPARATION}, EYE_HEIGHT_OFFSET={EYE_HEIGHT_OFFSET}, "
                   f"PITCH_ANGLE={PITCH_ANGLE}, EYE_OFFSET_ANGLE={EYE_OFFSET_ANGLE}, VERTICAL_FOV={VERTICAL_FOV}")

        # Direction configurations (heading in degrees)
        directions = {
            "East": 0,
            "North": 90,
            "West": 180,
            "South": 270
        }

        # Process each grid position
        for (grid_x, grid_y) in grid_positions:
            log_message(f"Processing grid position ({grid_x}, {grid_y})")
            # Get coordinates in inches from your custom function
            inches_coords = get_maze_coordinates(grid_x, grid_y)
            
            # Convert to cm for the camera
            position = (
                inches_to_cm(inches_coords[0]),
                inches_to_cm(inches_coords[1]),
                inches_to_cm(inches_coords[2]) + EYE_HEIGHT_OFFSET
            )
            log_message(f"Position in cm: {position}")

            # Capture views for each direction and eye
            for direction_name, heading in directions.items():
                log_message(f"Processing direction: {direction_name} (heading={heading})")
                # Calculate left/right eye positions
                left_eye, right_eye = calculate_eye_positions(position, heading, EYE_SEPARATION)
                log_message(f"Eye positions - Left: {(left_eye.x, left_eye.y, left_eye.z)}, "
                           f"Right: {(right_eye.x, right_eye.y, right_eye.z)}")

                # Get the active viewport
                viewport = app.activeViewport
                
                # --- Render Left Eye ---
                log_message("Setting up left eye render")
                # 1) Create rendering object & set up
                rendering = setup_render_settings(width=1920, height=1920)  # e.g., square 1920×1920
                if not rendering:
                    log_message(f"Failed to initialize rendering for ({grid_x}, {grid_y})")
                    ui.messageBox(f"Failed to initialize rendering for ({grid_x}, {grid_y}).")
                    if exit_on_error:
                        sys.exit(1)
                    continue
                
                # 2) Compute a target with an offset angle
                target_left = calculate_view_target(position, heading, PITCH_ANGLE, EYE_OFFSET_ANGLE)
                log_message(f"Left eye target: {(target_left.x, target_left.y, target_left.z)}")
                
                # 3) Configure the camera
                set_camera_for_eye(viewport, left_eye, target_left, VERTICAL_FOV)
                
                # 4) Render to file
                filename_left = os.path.join(output_dir, f"pos_{grid_x}_{grid_y}_{direction_name}_left.png")
                success_left = perform_render(rendering, viewport.camera, filename_left)
                if not success_left:
                    log_message(f"Failed left-eye render for ({grid_x}, {grid_y}) facing {direction_name}")
                    ui.messageBox(f"Failed left-eye render for ({grid_x}, {grid_y}) facing {direction_name}")
                    if exit_on_error:
                        sys.exit(1)
                    continue

                # --- Render Right Eye ---
                log_message("Setting up right eye render")
                rendering = setup_render_settings(width=1920, height=1920)
                if not rendering:
                    log_message(f"Failed to initialize rendering for ({grid_x}, {grid_y})")
                    ui.messageBox(f"Failed to initialize rendering for ({grid_x}, {grid_y}).")
                    if exit_on_error:
                        sys.exit(1)
                    continue

                target_right = calculate_view_target(position, heading, PITCH_ANGLE, -EYE_OFFSET_ANGLE)
                log_message(f"Right eye target: {(target_right.x, target_right.y, target_right.z)}")
                set_camera_for_eye(viewport, right_eye, target_right, VERTICAL_FOV)

                filename_right = os.path.join(output_dir, f"pos_{grid_x}_{grid_y}_{direction_name}_right.png")
                success_right = perform_render(rendering, viewport.camera, filename_right)
                if not success_right:
                    log_message(f"Failed right-eye render for ({grid_x}, {grid_y}) facing {direction_name}")
                    ui.messageBox(f"Failed right-eye render for ({grid_x}, {grid_y}) facing {direction_name}")
                    if exit_on_error:
                        sys.exit(1)
                    continue

    except Exception as e:
        log_message(f"ERROR in capture_views: {str(e)}\n{traceback.format_exc()}")
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
            if exit_on_error:
                sys.exit(1)

def run(context):
    """
    The main entry point for the script. Modify grid_positions or output_directory
    as needed. Then run the script in Fusion 360.
    """
    log_message("=== Script started ===")
    ui = adsk.core.Application.get().userInterface
    try:
        # Example usage - add grid positions here
        grid_positions = [
            (1, 1),
            (3, 2),
            (4, 2),
            (8, 2),
            (9, 2),
            (11, 1),
            (6, 3),
            (10, 3),
            (2, 5),
            (10, 5),
            (3, 6),
            (5, 6),
            (7, 6),
            (9, 6),
            (2, 7),
            (6, 7),
            (10, 7),
            (2, 9),
            (6, 9),
            (10, 9),
            (3, 10),
            (4, 10),
            (8, 10),
            (9, 10),
            (1, 11),
            (11, 11)
            # More positions as needed...
        ]
        
        # Modify path as needed for machine
        output_directory = r"/Users/gravelbridge/Desktop/blairlab_fusion/dynamic/images"
        log_message(f"Using output directory: {output_directory}")
        
        capture_views(grid_positions, output_directory)
        log_message("=== Script completed successfully ===")
        
    except Exception as e:
        log_message(f"ERROR in run: {str(e)}\n{traceback.format_exc()}")
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
            if exit_on_error:
                sys.exit(1)
