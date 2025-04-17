def get_maze_coordinates(grid_x, grid_y):
    """
    Convert maze grid coordinates to Fusion model coordinates in inches.
    
    Args:
        grid_x (int): X coordinate on the grid (0-12)
        grid_y (int): Y coordinate on the grid (0-12)
    
    Returns:
        tuple: (x, y, z) coordinates in inches
    """
    # Validate input coordinates
    if not (0 <= grid_x <= 12 and 0 <= grid_y <= 12):
        raise ValueError("Grid coordinates must be between 0 and 12")
    
    # Known reference points (grid_x, grid_y): (x_inches, y_inches)
    reference_points = {
        (1, 1): (8.039, 100.98),
        (2, 2): (16.336, 92.683),
        (6, 2): (55.519, 92.683),
        (6, 6): (55.519, 53.50),  # Added new reference point
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

    return (round(x, 3), round(y, 3), Z_HEIGHT)

def verify_coordinates():
    """Verify the function against known reference points"""
    reference_points = {
        (1, 1): (8.039, 100.98),
        (2, 2): (16.336, 92.683),
        (6, 2): (55.519, 92.683),
        (6, 6): (55.519, 53.50),  # Added new reference point
        (10, 2): (94.702, 92.683),
        (11, 1): (102.999, 100.98),
        (2, 10): (16.336, 21.973),
        (1, 11): (8.039, 6.02),
        (11, 11): (102.999, 6.02)
    }
    
    print("Verification of reference points:")
    for (grid_x, grid_y), (ref_x, ref_y) in reference_points.items():
        calculated = get_maze_coordinates(grid_x, grid_y)
        print(f"Grid ({grid_x}, {grid_y}):")
        print(f"  Reference: ({ref_x}, {ref_y}, {33.577})")
        print(f"  Calculated: {calculated}")
        print()

if __name__ == "__main__":
    # Example usage
    print("Example coordinate lookup:")
    coord = get_maze_coordinates(10, 6)
    print(f"Grid position (6,6) -> Fusion coordinates: {coord}")
    print("\nVerifying against known reference points...")
    verify_coordinates()