import adsk.core
import adsk.fusion
import traceback

# Version configuration - update these when versions change
VERSIONS = {
    'full_assembly': 'v19',
    'center_assembly': 'v21',
    'side_assembly': 'v23',
    'barrier_assembly': 'v40',
    'saddle_assembly': 'v12'
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

def move_object_vertical(full_assembly_name, mid_assembly_name, barrier_assembly_name, saddle_name, inches_to_move):
    """
    Move a specific Fusion 360 Saddle and Plexiglass Assembly up or down by a specified amount in inches.
    """
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = app.activeProduct
        root = design.rootComponent
        
        # Debug: Show what we're looking for
        ui.messageBox(f'Searching for:\nFull: {full_assembly_name}\nMid: {mid_assembly_name}\nBarrier: {barrier_assembly_name}\nSaddle: {saddle_name}')
        
        # Convert inches to centimeters
        cm_to_move = inches_to_move * 2.54
        
        # Navigate through the assembly hierarchy
        full_assembly = None
        mid_assembly = None
        barrier_assembly = None
        target_object = None
        
        # Debug: List all root occurrences
        root_occs = [occ.name for occ in root.occurrences]
        ui.messageBox(f'Root components found:\n{"\n".join(root_occs)}')
        
        # Find Full Assembly
        for occ in root.occurrences:
            if occ.name == full_assembly_name:
                full_assembly = occ
                break
        
        if not full_assembly:
            ui.messageBox(f'Could not find Full Assembly: {full_assembly_name}')
            return False
            
        # Debug: List all occurrences in full assembly
        full_occs = [occ.name for occ in full_assembly.childOccurrences]
        ui.messageBox(f'Components in Full Assembly:\n{"\n".join(full_occs)}')
        
        # Find Mid Assembly within Full Assembly
        for occ in full_assembly.childOccurrences:
            if occ.name == mid_assembly_name:
                mid_assembly = occ
                break
                
        if not mid_assembly:
            ui.messageBox(f'Could not find Mid Assembly: {mid_assembly_name}')
            return False
            
        # Debug: List all occurrences in mid assembly
        mid_occs = [occ.name for occ in mid_assembly.childOccurrences]
        ui.messageBox(f'Components in Mid Assembly:\n{"\n".join(mid_occs)}')
            
        # Find Barrier Assembly within Mid Assembly
        for occ in mid_assembly.childOccurrences:
            if occ.name == barrier_assembly_name:
                barrier_assembly = occ
                break
                
        if not barrier_assembly:
            ui.messageBox(f'Could not find Barrier Assembly: {barrier_assembly_name}')
            return False
            
        # Debug: List all occurrences in barrier assembly
        barrier_occs = [occ.name for occ in barrier_assembly.childOccurrences]
        ui.messageBox(f'Components in Barrier Assembly:\n{"\n".join(barrier_occs)}')
            
        # Find Saddle Assembly within Barrier Assembly
        for occ in barrier_assembly.childOccurrences:
            if occ.name == saddle_name:
                target_object = occ
                break
                
        if target_object:
            # Get current transform
            transform = target_object.transform
            current_z = transform.translation.z
            
            # Create new transform with updated position
            new_transform = adsk.core.Matrix3D.create()
            new_transform = transform
            
            # Update only the Z position
            new_transform.translation = adsk.core.Vector3D.create(
                transform.translation.x,
                transform.translation.y,
                transform.translation.z + cm_to_move
            )
            
            # Apply the new transform
            target_object.transform = new_transform
            
            ui.messageBox(f'Successfully moved assembly from Z={current_z:.2f} to Z={new_transform.translation.z:.2f}')
            return True
        else:
            ui.messageBox(f'Could not find Saddle Assembly: {saddle_name}')
            return False
            
    except:
        if ui:
            ui.messageBox(f'Failed:\n{traceback.format_exc()}')
        return False

def get_assembly_path(x, y):
    """Get the full assembly path for a barrier at given coordinates."""
    if (x, y) not in BARRIER_MAP:
        return None
        
    assembly_type, side_number, barrier_number = BARRIER_MAP[(x, y)]
    
    # Build the assembly path
    full_assembly = f"Full Assembly {VERSIONS['full_assembly']}:1"
    
    if assembly_type == 'center':
        mid_assembly = f"{ASSEMBLY_TYPES['center']} {VERSIONS['center_assembly']}:1"
    else:
        mid_assembly = f"{ASSEMBLY_TYPES['side']} {VERSIONS['side_assembly']}:{side_number}"
        
    barrier_assembly = f"New Barrier Assembly {VERSIONS['barrier_assembly']}:{barrier_number}"
    saddle_assembly = f"Barrier: Saddle and Plexiglass Assembly {VERSIONS['saddle_assembly']}:1"
    
    return (full_assembly, mid_assembly, barrier_assembly, saddle_assembly)

def move_barrier(x, y, inches_to_move):
    """Move a barrier at the specified coordinates up or down by the specified amount."""
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        # Get assembly path for the specified coordinates
        assembly_path = get_assembly_path(x, y)
        if not assembly_path:
            ui.messageBox(f'No barrier found at coordinates ({x}, {y})')
            return False
            
        # Move the barrier using the existing move_object_vertical function
        result = move_object_vertical(*assembly_path, inches_to_move)
        
        if result:
            ui.messageBox(f'Successfully moved barrier at ({x}, {y})')
        return result
        
    except:
        if ui:
            ui.messageBox(f'Failed:\n{traceback.format_exc()}')
        return False

def run(context):
    try:
        # Example: Move barrier at (5,6) up by 16 inches
        move_barrier(5, 2, 16.0)
        
        # Example: Move barrier at (7,6) down by 16 inches
        # move_barrier(7, 6, -16.0)
    except:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))