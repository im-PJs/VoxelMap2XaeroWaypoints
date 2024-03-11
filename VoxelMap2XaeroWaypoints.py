#!/usr/bin/python3

import os
import functools
import argparse
import glob
import random
import sys
import logging
from collections import defaultdict
import re

# Minecraft VoxelMap to Xaero's World Map Converter
# Created by: PJs 
# Last updated: 3/10/2024

logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

class VoxelMapWaypoint(object):
    def __init__(self, name=None, dim=None, x=None, y=None, z=None, r=None, g=None, b=None, suffix=None, world=None, enabled=False):
        self.name = name
        self.dim = dim
        self.x = x
        self.y = y
        self.z = z
        self.r = r
        self.g = g
        self.b = b
        self.suffix = suffix
        self.world = world
        self.enabled = enabled

class DimensionData(object):
    def __init__(self, dimension):
        self.dimension = dimension
        self.waypoints = []

def acc_waypoints_by_dim(dataset, waypoint):
    dimension_data = dataset.get(waypoint.dim, DimensionData(waypoint.dim))
    dimension_data.waypoints.append(waypoint)
    dataset[waypoint.dim] = dimension_data
    return dataset

def group_waypoints_by_dim(waypoints):
    return functools.reduce(acc_waypoints_by_dim, waypoints, {})

class MissingBaseDirectoryError(Exception):
    pass

class MissingSourceFileError(Exception):
    pass

def check_dir_args(voxelmap_dir, xaeromap_dir):
    logging.debug(f"Checking directories: VoxelMap: '{voxelmap_dir}', XaeroMap: '{xaeromap_dir}'")
    logging.info("Verifying VoxelMap and XaeroMap directories...")
    if not os.path.exists(voxelmap_dir):
        logging.error("VoxelMap directory not found. Please check the path.")
        raise MissingBaseDirectoryError('Voxelmap directory does not exist')
    if not os.path.exists(xaeromap_dir):
        logging.error("XaeroMap directory not found. Please check the path.")
        raise MissingBaseDirectoryError('XaeroMap directory does not exist')

def boolean_to_string(val):
    return 'true' if val else 'false'

def extract_xz_coords(waypoint):
    if waypoint.dim == 'the_nether':
        return (waypoint.x * 8, waypoint.z * 8)  # Convert Nether to Overworld coords
    return (waypoint.x, waypoint.z)

def extract_initial(idx, index_initial, waypoint):
    if index_initial:
        return chr(min(ord('A') + idx, ord('Z')))
    return waypoint.name[0].upper()

def extract_color(random_color, waypoint):
    return random.randrange(16) if random_color else 0

def is_server_filename(filename):
    # Improved IP detection with common TLDs
    if re.search(r'(\.com|\.net|\.org|\.io|\.co|\.us|\.biz|~colon~\d+)', filename, re.IGNORECASE):
        return True
    return False

def determine_filename(server):
    # Use different filename formats based on whether it's server or singleplayer
    return 'mw$default_1.txt' if server else 'waypoints.txt'

def voxelmap_assign_kv(waypoint, k, v):
    if k == "name":
        waypoint.name = v
    elif k == "dimensions":
        parsed_dim = v.split('#')[0] if '#' in v and v.split('#')[0] else 'overworld'  # Default to 'overworld' if no valid dimension is found
        waypoint.dim = parsed_dim
        # Log the assigned dimension
        logging.info(f"Waypoint '{waypoint.name}' assigned to dimension '{parsed_dim}'.")
    elif k == "x":
        waypoint.x = int(v)
    elif k == "y":
        waypoint.y = int(v)
    elif k == "z":
        waypoint.z = int(v)
    elif k == "red":
        waypoint.r = float(v)
    elif k == "green":
        waypoint.g = float(v)
    elif k == "blue":
        waypoint.b = float(v)
    elif k == "suffix":
        waypoint.suffix = v
    elif k == "world":
        waypoint.world = v
    elif k == "enabled":
        waypoint.enabled = v == "true"

def parse_voxelmap_file(filepath):
    logging.debug(f"Trying to open VoxelMap file: '{filepath}'")
    waypoints = []
    try:
        with open(filepath, 'r') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith('#') or not line.startswith('name:'): continue  # Skip empty lines and comments
                parts = line.split(',')
                waypoint = VoxelMapWaypoint()
                for part in parts:
                    k, v = part.split(':', 1)  # Split on the first colon only
                    voxelmap_assign_kv(waypoint, k, v)
                waypoints.append(waypoint)
    except IOError as e:
        logging.error(f"IOError encountered while opening file: {e}")
        raise MissingSourceFileError(f'Could not open voxelmap points file: {filepath}')
    logging.debug(f"Total waypoints parsed: {len(waypoints)}")
    return waypoints

def format_waypoint_for_xaero(waypoint):
    color = extract_color(True, waypoint)  # Assume random color for now
    initial = waypoint.name[0].upper()  # Just use the first letter of the name as the initial
    return f"waypoint:{waypoint.name}:{initial}:{waypoint.x}:{waypoint.y}:{waypoint.z}:{color}:{boolean_to_string(not waypoint.enabled)}:0:gui.xaero_default:false:0:0"

def sanitize_server_name(name):
    # Remove the port and illegal characters from server names
    # For example, "132.324.55.624~colon~25594" becomes "132.324.55.624"
    name = re.sub(r'~[^~]+~\d+', '', name)  # Regex to remove ~colon~25594-like patterns
    return name

def voxel2xaero(xaeromap_dir, world_name, waypoints):
    server = is_server_filename(world_name)
    if server:
        sanitized_name = sanitize_server_name(world_name)
        xaero_world_dir = f"Multiplayer_{sanitized_name}"
    else:
        xaero_world_dir = world_name
    xaero_world_path = os.path.join(xaeromap_dir, xaero_world_dir)

    if not os.path.exists(xaero_world_path):
        os.makedirs(xaero_world_path, exist_ok=True)
        logging.debug(f"Created directory for {'server' if server else 'world'}: {xaero_world_dir}")

    grouped_waypoints = group_waypoints_by_dim(waypoints)
    conversion_summary = {}  # Initialize the conversion summary dictionary

    for dim, data in grouped_waypoints.items():
        if dim is None or data is None or data.waypoints is None:
            logging.error(f"Skipping invalid dimension or missing data for dimension: {dim}")
            continue  # Skip this iteration if dimension is None or data is missing

        # Convert VoxelMap dimension format to Xaero's.
        xaero_dim_folder = 'dim%-1' if dim == 'the_nether' else 'dim%1' if dim == 'the_end' else 'dim%0'
        xaero_file_name = determine_filename(server)
        xaero_folder_path = os.path.join(xaero_world_path, xaero_dim_folder)
        os.makedirs(xaero_folder_path, exist_ok=True)
        xaero_file_path = os.path.join(xaero_folder_path, xaero_file_name)

        # Check if the file already exists to determine if we need to add the header
        file_exists = os.path.isfile(xaero_file_path)

        logging.debug(f"Appending waypoints to {xaero_file_path} for dimension {dim}")
        logging.info(f"Adding waypoints to {dim} in Xaero's format...")
        with open(xaero_file_path, 'a') as file:  # Open for appending
            # If the file didn't exist, write the header first
            if not file_exists:
                file.write("#\n")
                file.write("#waypoint:name:initials:x:y:z:color:disabled:type:set:rotate_on_tp:tp_yaw:visibility_type:destination\n")
                file.write("#\n")

            for waypoint in data.waypoints:
                xaero_waypoint = format_waypoint_for_xaero(waypoint)
                file.write(f"{xaero_waypoint}\n")
            logging.info(f"Appended {len(data.waypoints)} waypoints to {xaero_file_path}")

        # Update the conversion summary with the count of waypoints added for this dimension
        conversion_summary[dim] = len(data.waypoints)

    return conversion_summary  # Return the conversion summary at the end of the function

def main():
    print("--------------------------------------------------")
    print("VoxelMap to Xaero Conversion Process Initiated")
    print("--------------------------------------------------")
    print("Checking directories... OK")

    parser = argparse.ArgumentParser(description='Convert VoxelMap data to Xaero\'s World Map format.')
    parser.add_argument('--voxelmap-dir', default='./voxelmap', help='Directory where VoxelMap waypoints are stored.')
    parser.add_argument('--xaeromap-dir', default='./XaeroWaypoints', help='Directory where Xaero\'s waypoints should be saved.')
    args = parser.parse_args()

    total_summary = defaultdict(lambda: defaultdict(int))  # Initialize total counters for dimensions

    try:
        check_dir_args(args.voxelmap_dir, args.xaeromap_dir)
        voxelmap_files = glob.glob(os.path.join(args.voxelmap_dir, '*.points'))
        for vm_file in voxelmap_files:
            world_name = os.path.splitext(os.path.basename(vm_file))[0]  # Get the base name of the file for reporting
            session_type = "Multiplayer" if is_server_filename(world_name) else "Singleplayer"
            print(f"\nProcessing {session_type} file: {world_name}.points")
            print("- Assigning waypoints... ", end="")

            waypoints = parse_voxelmap_file(vm_file)
            conversion_summary = voxel2xaero(args.xaeromap_dir, world_name, waypoints)

            print("Done")  # Finish the 'assigning waypoints' line

            for dim, count in conversion_summary.items():
                total_summary[dim][world_name] += count
                print(f"- Adding waypoints to {dim.capitalize()}... {count} new waypoints added.")

            print(f"- Conversion for {world_name}.points completed.")
    except Exception as e:
        logging.warning(f"An error occurred: {e}")
        sys.exit(1)

    # Print final summary
    print("--------------------------------------------------\n")
    print("Conversion Summary:")
    print(f"- Total files processed: {len(voxelmap_files)}")
    for dim, worlds in total_summary.items():
        total_by_dim = sum(worlds.values())
        print(f"- Total waypoints added: {dim.capitalize()} ({total_by_dim})")
        for world, count in worlds.items():
            print(f"  - {world}: {count}")
    print("- Conversion process completed successfully.")
    print("--------------------------------------------------")


if __name__ == '__main__':
    main()

    #attribution
    print("""This script was created by PJ's.
For updates or issues, visit: https://github.com/im-PJs/VoxelMap2XaeroWaypoints
----------------------------------------------------------------------""")

# Copyright © 2024 PJ's. All rights reserved.
# This script is protected by copyright law. It may not be reproduced or distributed without permission.
# You are welcome to use this script with proper attribution. If you intend to distribute or modify it, please create an issue on the github page permission and credit details.

