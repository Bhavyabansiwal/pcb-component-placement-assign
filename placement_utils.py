# placement_utils.py
"""
A utility module for the PCB Component Placement coding assignment.
"""
import time
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- Assignment Constants ---
BOARD_DIMS = (50, 50)
PROXIMITY_RADIUS = 10.0
CENTER_OF_MASS_RADIUS = 2.0
KEEPOUT_ZONE_DIMS = (10, 20)
VALIDATION_TIME_LIMIT = 2

# --- Geometric Helper Functions ---
def _get_center(comp):
    return (comp['x'] + comp['w'] / 2, comp['y'] + comp['h'] / 2)

def _distance(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

# --- Public Utility Functions ---

def validate_placement(placement):
    """Validates a component placement against all hard constraints."""
    print("--- Running Detailed Hard Constraint Validation ---")
    results = {}
    
    required_keys = ['USB_CONNECTOR', 'MICROCONTROLLER', 'CRYSTAL', 
                     'MIKROBUS_CONNECTOR_1', 'MIKROBUS_CONNECTOR_2']
    if not all(key in placement for key in required_keys):
        print("FAILED: The placement dictionary is missing one or more required components.")
        return False

    all_in_bounds = all(
        comp['x'] >= 0 and comp['y'] >= 0 and
        comp['x'] + comp['w'] <= BOARD_DIMS[0] and
        comp['y'] + comp['h'] <= BOARD_DIMS[1]
        for comp in placement.values()
    )
    results["Boundary Constraint"] = (all_in_bounds, "")

    items = list(placement.items())
    overlap_found = any(
        not (items[i][1]['x'] + items[i][1]['w'] <= items[j][1]['x'] or 
             items[i][1]['x'] >= items[j][1]['x'] + items[j][1]['w'] or
             items[i][1]['y'] + items[i][1]['h'] <= items[j][1]['y'] or 
             items[i][1]['y'] >= items[j][1]['y'] + items[j][1]['h'])
        for i in range(len(items)) for j in range(i + 1, len(items))
    )
    results["No Overlapping"] = (not overlap_found, "")
    
    all_on_edge = all(
        placement[name]['x'] == 0 or placement[name]['y'] == 0 or
        placement[name]['x'] + placement[name]['w'] == BOARD_DIMS[0] or
        placement[name]['y'] + placement[name]['h'] == BOARD_DIMS[1]
        for name in ['USB_CONNECTOR', 'MIKROBUS_CONNECTOR_1', 'MIKROBUS_CONNECTOR_2']
    )
    results["Edge Placement"] = (all_on_edge, "")

    mb1, mb2 = placement['MIKROBUS_CONNECTOR_1'], placement['MIKROBUS_CONNECTOR_2']
    is_parallel = False
    if mb1['w'] == mb2['w']:
        is_parallel = ((mb1['x'] == 0 and mb2['x'] + mb2['w'] == 50) or
                       (mb1['x'] + mb1['w'] == 50 and mb2['x'] == 0) or
                       (mb1['y'] == 0 and mb2['y'] + mb2['h'] == 50) or
                       (mb1['y'] + mb1['h'] == 50 and mb2['y'] == 0))
    results["Parallel Placement"] = (is_parallel, "")

    dist = _distance(_get_center(placement['CRYSTAL']), _get_center(placement['MICROCONTROLLER']))
    results["Proximity Constraint"] = (dist <= PROXIMITY_RADIUS, f"Actual distance: {dist:.2f}")

    com_x = sum(_get_center(c)[0] for c in placement.values()) / len(placement)
    com_y = sum(_get_center(c)[1] for c in placement.values()) / len(placement)
    com_dist = _distance((com_x, com_y), (25, 25))
    results["Global Balance"] = (com_dist <= CENTER_OF_MASS_RADIUS, f"CoM dist: {com_dist:.2f}")

    usb, crystal, micro = placement['USB_CONNECTOR'], placement['CRYSTAL'], placement['MICROCONTROLLER']
    zone_w, zone_h_inward = KEEPOUT_ZONE_DIMS
    usb_cx, usb_cy = _get_center(usb)
    zone = {}
    if usb['y'] == 0: zone = {'x': usb_cx - zone_w / 2, 'y': 0, 'w': zone_w, 'h': zone_h_inward}
    elif usb['y'] + usb['h'] == 50: zone = {'x': usb_cx - zone_w / 2, 'y': 50 - zone_h_inward, 'w': zone_w, 'h': zone_h_inward}
    elif usb['x'] == 0: zone = {'x': 0, 'y': usb_cy - zone_w / 2, 'w': zone_h_inward, 'h': zone_w}
    else: zone = {'x': 50 - zone_h_inward, 'y': usb_cy - zone_w / 2, 'w': zone_h_inward, 'h': zone_w}
    p1, p2 = _get_center(crystal), _get_center(micro)
    def ccw(A,B,C): return (C[1]-A[1])*(B[0]-A[0]) > (B[1]-A[1])*(C[0]-A[0])
    def intersect(A,B,C,D): return ccw(A,C,D)!=ccw(B,C,D) and ccw(A,B,C)!=ccw(A,B,D)
    tl, tr, bl, br = (zone['x'], zone['y']), (zone['x']+zone['w'], zone['y']), (zone['x'], zone['y']+zone['h']), (zone['x']+zone['w'], zone['y']+zone['h'])
    intersects = (intersect(p1,p2,tl,tr) or intersect(p1,p2,tr,br) or intersect(p1,p2,br,bl) or intersect(p1,p2,bl,tl))
    results["Keep-Out Zone"] = (not intersects, "")

    all_valid = all(res[0] for res in results.values())
    for rule, (is_valid, msg) in results.items():
        # **FIX IS HERE:** Replaced emojis with simple text
        status = "PASSED" if is_valid else "FAILED"
        print(f"{rule:<22}: {status} {msg}")
    
    return all_valid

# --- The rest of the file remains the same ---

def score_placement(placement):
    """Calculates a score for a placement."""
    print("\n--- Calculating Placement Score (Lower is Better) ---")
    min_x = min(c['x'] for c in placement.values())
    max_x = max(c['x'] + c['w'] for c in placement.values())
    min_y = min(c['y'] for c in placement.values())
    max_y = max(c['y'] + c['h'] for c in placement.values())
    bounding_box_area = (max_x - min_x) * (max_y - min_y)
    
    board_center = (BOARD_DIMS[0] / 2, BOARD_DIMS[1] / 2)
    micro_center = _get_center(placement['MICROCONTROLLER'])
    centrality_score = _distance(micro_center, board_center)
    
    total_score = bounding_box_area + (centrality_score * 10)
    print(f"Compactness Score (Area): {bounding_box_area:.2f}")
    print(f"Centrality Score (uC dist): {centrality_score:.2f}")
    print(f"---------------------------------\nTotal Score: {total_score:.2f}\n---------------------------------")
    return total_score

def plot_placement(placement):
    """Generates a matplotlib plot to visualize the placement."""
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(0, BOARD_DIMS[0]); ax.set_ylim(0, BOARD_DIMS[1])
    ax.set_xticks(range(0, BOARD_DIMS[0] + 1, 5)); ax.set_yticks(range(0, BOARD_DIMS[1] + 1, 5))
    ax.grid(True, linestyle='--', color='gray', alpha=0.5)
    ax.set_aspect('equal', adjustable='box'); ax.invert_yaxis()
    ax.set_title("PCB Component Placement Solution")
    
    colors = {'USB_CONNECTOR': '#e74c3c', 'MICROCONTROLLER': '#3498db', 'CRYSTAL': '#f39c12',
              'MIKROBUS_CONNECTOR_1': '#9b59b6', 'MIKROBUS_CONNECTOR_2': '#8e44ad'}
    labels = {'USB_CONNECTOR': 'USB', 'MICROCONTROLLER': 'μC', 'CRYSTAL': 'XTAL',
              'MIKROBUS_CONNECTOR_1': 'MB1', 'MIKROBUS_CONNECTOR_2': 'MB2'}

    for name, comp in placement.items():
        rect = patches.Rectangle((comp['x'], comp['y']), comp['w'], comp['h'],
                                 linewidth=1, edgecolor='black', facecolor=colors[name])
        ax.add_patch(rect)
        ax.text(comp['x'] + comp['w'] / 2, comp['y'] + comp['h'] / 2, labels[name],
                color='white', ha='center', va='center', fontweight='bold')
    
    uc_center = _get_center(placement['MICROCONTROLLER'])
    circle = patches.Circle(uc_center, PROXIMITY_RADIUS, fill=True, color='#f39c12', alpha=0.1,
                            linestyle='--', lw=2, label='Proximity Radius')
    ax.add_patch(circle)
    
    usb = placement['USB_CONNECTOR']
    zone_w, zone_h_inward = KEEPOUT_ZONE_DIMS
    usb_cx, usb_cy = _get_center(usb)
    zone_props = {}
    if usb['y'] == 0: zone_props = {'xy': (usb_cx-zone_w/2, 0), 'w': zone_w, 'h': zone_h_inward}
    elif usb['y']+usb['h']==BOARD_DIMS[1]: zone_props = {'xy': (usb_cx-zone_w/2, BOARD_DIMS[1]-zone_h_inward), 'w': zone_w, 'h': zone_h_inward}
    elif usb['x'] == 0: zone_props = {'xy': (0, usb_cy-zone_w/2), 'w': zone_h_inward, 'h': zone_w}
    else: zone_props = {'xy': (BOARD_DIMS[0]-zone_h_inward, usb_cy-zone_w/2), 'w': zone_h_inward, 'h': zone_w}
    keepout = patches.Rectangle(zone_props['xy'], zone_props['w'], zone_props['h'], fill=True, color='#e74c3c', alpha=0.15, linestyle='--', lw=2, label='Keep-out Zone')
    ax.add_patch(keepout)
    
    xtal_center = _get_center(placement['CRYSTAL'])
    ax.plot([xtal_center[0], uc_center[0]], [xtal_center[1], uc_center[1]], 'k--')
    
    plt.show()

