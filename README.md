# Minecraft VoxelMap to Xaero's World Map Converter

This Python script converts waypoints from VoxelMap format to Xaero's World Map format for Minecraft. It enables Minecraft players who have switched from using VoxelMap to Xaero's World Map to retain their saved waypoints, ensuring a seamless transition between these mapping mods.

## Features

- Converts waypoint data from VoxelMap format to Xaero's World Map format.
- Supports both singleplayer and multiplayer server waypoint files.
- Detects and categorizes waypoints according to the Minecraft dimension (Overworld, Nether, The End).
- Automatically creates necessary directories and files following Xaero's World Map file structure.
- Adds header information to newly created waypoint files for Xaero's compatibility.

## Requirements

- Python 3.x
- Minecraft with VoxelMap and Xaero's World Map mods installed
- Waypoint files from VoxelMap

## Installation

1. **Locate Minecraft Instance Folder:**
   - Start the search window from your desktop start menu.
   - On almost every version of Windows, this can be found by clicking on the Start Menu.
   - Type %appdata% into the search and hit enter.
   - Click on the .minecraft folder.
   - Default: `C:\Users\[YourUsername]\AppData\Roaming\.minecraft`
   - Others: Varies by launcher, check settings or docs.

3. **Setup:**
   - Download `VoxelMap2XaeroWaypoints.py`.
   - Place it in your .Minecraft instance directory (where `saves`, `mods`, `resourcepacks`, `voxelmap` are).

4. **Open Command Prompt:**
   - Navigate to Minecraft instance folder, `Shift` + Right-click > "Open in Terminal".
   - Alternatively, type `cmd` in the address bar and press `Enter`.

5. **Run:**
   - Run the command `python VoxelMap2XaeroWaypoints.py` in the new CMD prompt window.
   - The script will process each `.points` file from the VoxelMap directory and create or update corresponding files in the Xaero's World Map directory.

6. **Play:**
   - Open up your world/server and you should see the new Xaero Map waypoints in-game.
  
## Notes

- **Backup your original waypoint files before running the script.**
- **You will get duplicates added to your exisiting waypoints if this is run multiple times**
- The script does not delete any files. It only reads VoxelMap waypoint files and writes new or updated files for Xaero's World Map.
- Waypoints are grouped by dimension. If waypoints from different dimensions are contained within a single VoxelMap file, they will be split accordingly for Xaero's format.
- The script will automatically detect whether a waypoint file corresponds to a singleplayer world or a multiplayer server and adjust the directory structure accordingly.

## Troubleshooting

- Ensure that Python 3.x is correctly installed and accessible from your terminal or command prompt.
- Check the paths provided to the script are correct and the directories exist.
- If you encounter permission errors, try running the command prompt or terminal as an administrator or ensure you have read/write permissions for the directories.

## License

This script is provided 'as-is', without any warranty or support. Users are responsible for the backups of their data.
