# solver.py (Final, Improved Version)
import time
import math
import random
import itertools

# Import the provided utility functions
import placement_utils as utils

# --- Internal Solver Constants ---
COMPONENTS_SPECS = {
    'USB_CONNECTOR': {'size': (5, 5)},
    'MICROCONTROLLER': {'size': (5, 5)},
    'CRYSTAL': {'size': (5, 5)},
    'MIKROBUS_CONNECTOR_1': {'size': (5, 15)},
    'MIKROBUS_CONNECTOR_2': {'size': (5, 15)},
}

# --- Helper Functions for Solver ---
def get_center_from_pos(name, pos):
    """Calculates center from (x, y, rot) format."""
    w, h = COMPONENTS_SPECS[name]['size']
    if pos[2] == 90: w, h = h, w
    return (pos[0] + w / 2, pos[1] + h / 2)

def _convert_to_util_format(internal_placement):
    """Converts the solver's internal format to the one used by the utility module."""
    util_placement = {}
    for name, (x, y, rot) in internal_placement.items():
        w, h = COMPONENTS_SPECS[name]['size']
        if rot == 90: w, h = h, w
        util_placement[name] = {'x': x, 'y': y, 'w': w, 'h': h}
    return util_placement

# --- New Intelligent Solver ---
def find_placement():
    """
    An intelligent, constraint-driven algorithm to find a valid placement.
    """
    start_time = time.time()
    
    # Try different edge configurations
    edge_configs = [
        ('v', 'top'), ('v', 'bottom'),
        ('h', 'left'), ('h', 'right')
    ]
    random.shuffle(edge_configs)

    for mb_orientation, usb_edge in edge_configs:
        
        # Try to find a solution within a time limit for each configuration
        while time.time() - start_time < (utils.VALIDATION_TIME_LIMIT - 0.2):
            positions = {}
            
            # 1. Place MIKROBUS connectors
            w, h = COMPONENTS_SPECS['MIKROBUS_CONNECTOR_1']['size']
            if mb_orientation == 'v':
                rot, rw, rh = 90, h, w
                y1, y2 = random.randint(0, 50 - rh), random.randint(0, 50 - rh)
                positions['MIKROBUS_CONNECTOR_1'] = (0, y1, rot)
                positions['MIKROBUS_CONNECTOR_2'] = (50 - rw, y2, rot)
            else: # 'h'
                rot, rw, rh = 0, w, h
                x1, x2 = random.randint(0, 50 - rw), random.randint(0, 50 - rw)
                positions['MIKROBUS_CONNECTOR_1'] = (x1, 0, rot)
                positions['MIKROBUS_CONNECTOR_2'] = (x2, 50 - rh, rot)

            # 2. Place USB connector
            usb_w, usb_h = COMPONENTS_SPECS['USB_CONNECTOR']['size']
            if usb_edge == 'top': positions['USB_CONNECTOR'] = (random.randint(0, 50 - usb_w), 0, 0)
            elif usb_edge == 'bottom': positions['USB_CONNECTOR'] = (random.randint(0, 50 - usb_w), 50 - usb_h, 0)
            elif usb_edge == 'left': positions['USB_CONNECTOR'] = (0, random.randint(0, 50 - usb_h), 0)
            else: positions['USB_CONNECTOR'] = (50-usb_w, random.randint(0, 50 - usb_h), 0)

            # 3. Intelligent Placement for internal components
            # Calculate the target center for the remaining 2 components
            edge_com_x = sum(get_center_from_pos(name, pos)[0] for name, pos in positions.items())
            edge_com_y = sum(get_center_from_pos(name, pos)[1] for name, pos in positions.items())
            
            # Target for all 5 components is (25, 25) * 5 = (125, 125)
            target_sum_x, target_sum_y = 125, 125
            
            # Required sum for the two internal components
            internal_sum_x = target_sum_x - edge_com_x
            internal_sum_y = target_sum_y - edge_com_y
            
            # Target center for the pair of internal components
            target_center_x = internal_sum_x / 2
            target_center_y = internal_sum_y / 2
            
            # 4. Search around the target center
            mc_w, mc_h = COMPONENTS_SPECS['MICROCONTROLLER']['size']
            cr_w, cr_h = COMPONENTS_SPECS['CRYSTAL']['size']

            for i in range(100): # 100 attempts to place around the target
                # Place MICROCONTROLLER near the target
                dx, dy = random.uniform(-5, 5), random.uniform(-5, 5)
                mc_x = int(target_center_x - mc_w/2 + dx)
                mc_y = int(target_center_y - mc_h/2 + dy)
                mc_pos = (mc_x, mc_y, 0)
                positions['MICROCONTROLLER'] = mc_pos

                # Place CRYSTAL near the MICROCONTROLLER
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(0, utils.PROXIMITY_RADIUS)
                mc_center = get_center_from_pos('MICROCONTROLLER', mc_pos)
                cr_x = int(mc_center[0] + dist * math.cos(angle) - cr_w/2)
                cr_y = int(mc_center[1] + dist * math.sin(angle) - cr_h/2)
                positions['CRYSTAL'] = (cr_x, cr_y, 0)
                
                # Full validation
                final_placement = _convert_to_util_format(positions)
                
                # The validator function prints its own report
                if utils.validate_placement(final_placement):
                    return positions # Return the first valid solution found
    
    return None # Return None if no solution is found across all configs

# --- Main Execution Block ---
if __name__ == "__main__":
    print("Starting the intelligent component placement solver...")
    solver_start_time = time.time()
    
    solution_internal = find_placement()
    
    solver_end_time = time.time()
    
    print(f"\n--- Solver Performance ---")
    print(f"Algorithm finished in: {solver_end_time - solver_start_time:.6f} seconds")
    if (solver_end_time - solver_start_time) <= utils.VALIDATION_TIME_LIMIT:
        print("PERFORMANCE: PASSED (Algorithm is fast enough)")
    else:
        print("PERFORMANCE: FAILED (Algorithm is too slow)")
    print("--------------------------")

    if solution_internal:
        print("\nSUCCESS: A valid placement was found!")
        final_placement = _convert_to_util_format(solution_internal)
        
        # Score and plot the final valid solution
        utils.score_placement(final_placement)
        print("\nDisplaying final plot...")
        utils.plot_placement(final_placement)
    else:
        print("\nFAILURE: Solver could not find a valid solution within the time limit.")
