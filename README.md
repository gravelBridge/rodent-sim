# Rodent Maze View Simulation with Fusion 360 and Python

This repository contains Python scripts and related assets that integrate with Autodesk Fusion 360 to simulate a rodent’s perspective within a 3D maze. The generated images can serve as input data for machine learning and computational neuroscience research, such as training reinforcement learning agents or advanced vision models to understand spatial cognition and navigation strategies.

A full technical report accompanying this code is available [here](https://drive.google.com/file/d/1VuCJLwodUhfI0ejYaSaXPOKKqvQ8wo0C/view?usp=sharing).

## Overview

Rodents rely on their vision, among other senses, to navigate complex environments. By using Autodesk Fusion 360’s scripting capabilities, we can automate the camera placement, rendering, and exporting of images from different coordinates, headings, and with varying illumination. These images approximate what a rodent might "see" at ground level, capturing subtle geometric and lighting cues.

The main goals of this setup are:
- Automating the capture of images from multiple positions and headings within the maze.
- Providing both non-global-illumination (in-canvas) and global-illumination (cloud-rendered) images.
- Facilitating the generation of large-scale datasets for machine learning, reinforcement learning, or vision models that attempt to replicate or study rodent navigation behaviors.

## Directory Structure

The repository is organized to separate code, rendered images, and configuration files:

**`/blairlab_fusion`**  
**├── test/**  
**│   └── generate_stacks.py**  
**├── dynamic_moving/**  
**│   └── set_capture.py**  
**├── generate.py**  
**├── center_four_gi/**  
**│   └── gi_four.py**  
**├── saving.py**  
**├── track_images/**  
**│   ├── right_x55.52_y53.50_h0.png**  
**│   ├── right_x55.52_y53.50_h90.png**  
**│   ├── right_x55.52_y53.50_h180.png**  
**│   ├── left_x55.52_y53.50_h180.png**  
**│   ├── left_x55.52_y53.50_h0.png**  
**│   ├── left_x55.52_y53.50_h270.png**  
**│   ├── right_x55.52_y53.50_h270.png**  
**│   └── left_x55.52_y53.50_h90.png**  
**├── images-gi/**  
**│   ├── 6_6_2_3_L.png**  
**│   ├── 6_6_3_3_L.png**  
**│   ├── 6_6_1_3_L.png**  
**│   ├── 6_6_0_3_L.png**  
**│   ├── 6_6_1_3_R.png**  
**│   ├── 6_6_0_3_R.png**  
**│   ├── 6_6_2_3_R.png**  
**│   └── 6_6_3_3_R.png**  
**├── images-non-gi/**  
**│   ├── 6_6_2_3_L.png**  
**│   ├── 6_6_3_3_L.png**  
**│   ├── 6_6_1_3_L.png**  
**│   ├── 6_6_0_3_L.png**  
**│   ├── 6_6_1_3_R.png**  
**│   ├── 6_6_0_3_R.png**  
**│   ├── 6_6_2_3_R.png**  
**│   └── 6_6_3_3_R.png**  
**└── center_four/**  
    **└── center_four.py**

## Directory and File Explanations

### `test/`
- **generate_stacks.py**:  
  This script calculates camera positions and headings, placing the virtual rodent's eyes at specified coordinates within the maze. It then captures stacks of images from a set of predefined grid locations. It uses techniques like converting inches to centimeters, computing eye positions, and setting up camera FOV. The images generated are often saved into a specified output directory.

### `dynamic_moving/`
- **set_capture.py**:  
  Contains functions and logic to dynamically manipulate certain components (e.g., barriers) within the Fusion 360 model. By altering the vertical position of these barrier assemblies, we can simulate different maze configurations. This can be used before capturing images to show the maze in different states (e.g., barriers raised or lowered).

### Root Files
- **generate.py**:  
  A general-purpose script that defines a grid of positions and headings within the maze. It automates switching Fusion 360 to the Render workspace, positions the camera for each eye (left and right), and saves out images. This script can generate a large dataset of images by iterating over multiple coordinates and headings.

- **saving.py**:  
  Contains functions and classes to navigate the Fusion 360 assembly hierarchy and move specific occurrences (e.g., saddle assemblies, barriers) up or down by a specified amount. This script complements `set_capture.py` by providing a reference approach to adjust physical elements in the CAD environment.

- **create_stacks.txt**:  
  While named `.txt`, it appears to contain code that similarly sets up camera positions and captures images. It may integrate with external tools (like PIL) to post-process images (e.g., converting them to grayscale). It's a scratch file or a recipe for generating image stacks with certain parameters.

### `center_four_gi/`
- **gi_four.py**:  
  This script is tailored to produce views from four cardinal directions (North, East, South, West) at a central position. It supports setting up camera parameters for both left and right eyes of the rodent, but relies on manually triggered cloud rendering in Fusion 360 for global illumination. Users must open Fusion 360’s Render workspace and initiate the cloud rendering themselves, then use this script to capture the GI images.

### `track_images/`
- Contains images captured from a specific position (`x=55.52, y=53.50`) at various headings (0°, 90°, 180°, 270°) and for both left and right eyes. These images represent a static example dataset. The naming scheme (`left_x55.52_y53.50_h0.png`) encodes the eye (left/right), position coordinates, and heading.

### `images-gi/`
- Holds images rendered with global illumination. The naming convention `6_6_0_3_L.png` or `6_6_0_3_R.png` encodes position and configuration. For example, `6_6_0_3_L` means:
  - Position: (6,6) in the grid space mapping.
  - Heading or configuration: `_0_3_` indicates East heading and cue configuration 3 (cue light 3 is on).
  - Eye: `L` for left eye, `R` for right eye.

These GI images have more realistic lighting, shadows, and reflections, making them valuable for evaluating how lighting realism affects model training and performance.

### `images-non-gi/`
- Contains images captured without global illumination, relying on the in-canvas rendering mode. Although less photorealistic, these images are produced more quickly and can serve as baseline data or for large-scale training where speed is important.

### `center_four/`
- **center_four.py**:  
  Similar to `gi_four.py`, but may focus on producing in-canvas rendered views from the maze's center in four directions. It can be a starting point or a simplified version of producing images from a single reference point without GI.

## Core Concepts in the Code

1. **Camera Placement**:  
   Each script computes the rodent’s eye positions based on a given height, heading, and interocular distance. By using simple trigonometric functions, the code calculates left and right eye coordinates, as well as a forward-facing target point for the camera.

2. **Field of View (FOV)**:  
   The vertical FOV is set to values like 140° or 150°, approximating a wide-angle view that a rodent might have. Adjusting FOV can test how vision model performance varies with narrower or wider fields of view.

3. **Pitch and Heading Adjustments**:  
   Scripts allow specifying pitch angles (e.g., 15° upward) and heading angles in increments of 90° (North, East, South, West), but this can be generalized to any angle. Such variation is crucial for building robust datasets that emulate a rodent looking around a maze.

4. **Global Illumination vs. Non-GI**:  
   - Non-GI images are rendered quickly in-canvas.  
   - GI images require manual cloud rendering but produce more realistic visuals.

5. **Maze Configuration Manipulation**:  
   Through scripts like `saving.py` and `set_capture.py`, the user can alter the maze’s physical elements, such as raising or lowering barriers. This allows creating diverse visual conditions that test a model’s ability to adapt to changing environments.

## Potential Use Cases

- **Machine Learning Training Data**:  
  The generated images can train reinforcement learning agents in simulation, helping them learn navigation strategies within a visually complex environment before testing on real-world or more detailed simulated environments.

- **Neuroscientific Modeling**:  
  By approximating what a rodent visually perceives, these images can help model or interpret neuronal activity observed in experimental settings. Researchers can input these images into computational models to predict place cell firing patterns or memory recall strategies.

- **Comparative Studies (GI vs. Non-GI)**:  
  Comparing model performance on GI and non-GI image sets can reveal how sensitive a system is to lighting realism. This can inform the choice of rendering mode and scene complexity when generating training data.

## Getting Started

1. Ensure you have Autodesk Fusion 360 and its Python API available.
2. Place these scripts in a known location accessible by Fusion 360’s script environment.
3. Modify paths and parameters in the scripts (`OUTPUT_DIR`, maze dimensions, step sizes, EYE_HEIGHT, EYE_SEPARATION, etc.) to match your scenario.
4. Run scripts like `generate.py` to produce images. For GI images, run scripts like `gi_four.py` and then manually trigger cloud rendering.

## Future Improvements

- Automating the GI render process to avoid manual steps.
- Integrating more biologically accurate visual models (e.g., considering a rodent’s visual acuity).
- Expanding to arbitrary maze layouts and dynamic elements.
