import adsk.core
import adsk.fusion
import traceback

# Version configuration - update these when versions change
VERSIONS = {
    'full_assembly': 'v20',
    'center_assembly': 'v22',
    'side_assembly': 'v24',
    'barrier_assembly': 'v41',
    'saddle_assembly': 'v13'
}

# Assembly type configuration
ASSEMBLY_TYPES = {
    'center': 'Center Assembly',
    'side': 'Side Assembly'
}

# Barrier mapping configuration
BARRIER_MAP = {
    # Format: (x, y): (assembly_type, side_number, barrier_number)
    # Center barriers
    (5, 6): ('center', None, 4),
    (7, 6): ('center', None, 3),
    (6, 5): ('center', None, 2),
    (6, 7): ('center', None, 1),
    
    # Side 4 barriers
    (2, 7): ('side', 4, 3),
    (2, 5): ('side', 4, 2),
    (3, 6): ('side', 4, 1),
    
    # Side 2 barriers
    (6, 3): ('side', 2, 1),
    (5, 2): ('side', 2, 3),
    (7, 2): ('side', 2, 2),
    
    # Side 1 barriers
    (10, 5): ('side', 1, 3),
    (9, 6): ('side', 1, 1),
    (10, 7): ('side', 1, 2),
    
    # Side 3 barriers
    (6, 9): ('side', 3, 1),
    (7, 10): ('side', 3, 3),
    (5, 10): ('side', 3, 2)
}

def move_object_vertical(full_assembly_component_name, mid_assembly_component_name, 
                         barrier_assembly_component_name, saddle_component_name, 
                         inches_to_move, barrier_number):
    """
    Move a specific Fusion 360 Saddle and Plexiglass Assembly up or down by modifying the occurrence's transform.

    Args:
        full_assembly_component_name (str): Name of the full assembly component
        mid_assembly_component_name (str): Name of the mid assembly component
        barrier_assembly_component_name (str): Name of the barrier assembly component
        saddle_component_name (str): Name of the saddle component
        inches_to_move (float): Distance to move in inches (positive = up, negative = down)
        barrier_number (int): Barrier identification number

    Returns:
        bool: True if successful, False otherwise
    """
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = app.activeProduct
        root = design.rootComponent

        # Find the component hierarchy
        full_assembly = None
        for occ in root.occurrences:
            if occ.component.name == full_assembly_component_name:
                full_assembly = occ
                break

        if not full_assembly:
            ui.messageBox(f'ERROR: Could not find Full Assembly: "{full_assembly_component_name}"')
            return False

        mid_assembly = None
        for occ in full_assembly.childOccurrences:
            if occ.component.name == mid_assembly_component_name:
                mid_assembly = occ
                break

        if not mid_assembly:
            ui.messageBox(f'ERROR: Could not find Mid Assembly: "{mid_assembly_component_name}"')
            return False

        barrier_assembly = None
        for occ in mid_assembly.childOccurrences:
            if (occ.component.name == barrier_assembly_component_name and 
                f":{barrier_number}" in occ.name):
                barrier_assembly = occ
                break

        if not barrier_assembly:
            ui.messageBox(f'ERROR: Could not find Barrier Assembly: "{barrier_assembly_component_name}"')
            return False

        target_occurrence = None
        for occ in barrier_assembly.childOccurrences:
            if occ.component.name == saddle_component_name:
                target_occurrence = occ
                break

        if not target_occurrence:
            ui.messageBox(f'ERROR: Could not find Saddle Assembly: "{saddle_component_name}"')
            return False

        # Check if the occurrence is grounded or constrained
        if target_occurrence.isGrounded:
            ui.messageBox('ERROR: The target occurrence is grounded and cannot be moved.')
            return False

        # Convert inches to centimeters
        cm_to_move = inches_to_move * 2.54

        # Modify the occurrence's transform
        current_transform = target_occurrence.transform

        # Create a translation vector for the vertical movement
        translation = adsk.core.Vector3D.create(0.0, 0.0, cm_to_move)

        # Create a translation matrix
        translation_matrix = adsk.core.Matrix3D.create()
        translation_matrix.translation = translation

        # Multiply the current transform by the translation matrix
        new_transform = current_transform.copy()
        new_transform.transformBy(translation_matrix)

        # Set the new transform to the occurrence
        target_occurrence.transform = new_transform

        return True

    except:
        if ui:
            ui.messageBox(f'Failed:\n{traceback.format_exc()}')
        return False


def get_assembly_path(x, y):
    """Get the full assembly path and barrier number for a barrier at given coordinates."""
    if (x, y) not in BARRIER_MAP:
        return None, None
        
    assembly_type, side_number, barrier_number = BARRIER_MAP[(x, y)]
    
    # Build the assembly component names
    full_assembly_component_name = f"Full Assembly {VERSIONS['full_assembly']}"
    
    if assembly_type == 'center':
        mid_assembly_component_name = f"{ASSEMBLY_TYPES['center']} {VERSIONS['center_assembly']}"
    else:
        mid_assembly_component_name = f"{ASSEMBLY_TYPES['side']} {VERSIONS['side_assembly']}"
    
    barrier_assembly_component_name = f"New Barrier Assembly {VERSIONS['barrier_assembly']}"
    saddle_component_name = f"Barrier: Saddle and Plexiglass Assembly {VERSIONS['saddle_assembly']}"
    
    return (full_assembly_component_name, mid_assembly_component_name, barrier_assembly_component_name, saddle_component_name), barrier_number

def move_barrier(x, y, inches_to_move):
    """Move a barrier at the specified coordinates up or down by the specified amount."""
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        # Get assembly path and barrier number for the specified coordinates
        assembly_path, barrier_number = get_assembly_path(x, y)
        if not assembly_path:
            ui.messageBox(f'ERROR: No barrier found at coordinates ({x}, {y})')
            return False
            
        # Move the barrier using the existing move_object_vertical function
        result = move_object_vertical(*assembly_path, inches_to_move, barrier_number)

        # Force multiple types of updates
        adsk.doEvents()
        
        return result
        
    except:
        if ui:
            ui.messageBox(f'Failed:\n{traceback.format_exc()}')
        return False

def run(context):
    try:
        # Example: Move barrier at (5,2) down by 16 inches
        move_barrier(6, 7, 16.0)
        
    except:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))