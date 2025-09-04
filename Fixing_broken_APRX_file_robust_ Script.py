#-------------------------------------------------------------------------------
# Name:         Fixing broken APRX file
# Purpose:      Fixing broken files in ArcGIS PRO
# Author:       Charles Owuama
#
# Created:     22/08/2025
# Copyright:   (c) Department of Planning, Lands and Heritage
#-------------------------------------------------------------------------------

import arcpy
import logging
import os
import re

def get_sde_path(dataset_name, sde_paths):
    """Returns the appropriate SDE path based on dataset name pattern."""
    dataset_name = dataset_name.strip()  # Remove leading/trailing spaces
    for sde_path in sde_paths:
        
        if re.search(r"A[0-9]{3}_", dataset_name): # Checks if a dataset has a particular naming convention
            if "giscapdb_ReadOnly_PRD.sde" in sde_path: # Search the data in this path and return if found
                return sde_path
        else:
            if "gispubdb_extdata_PROD.sde" in sde_path: # if not, it searches for it here
                return sde_path
    return None  # Return none if it can't find a match


def process_layer(layer, sde_paths):
    """Recursively process layers including group layers."""
    if layer.isGroupLayer:
        for sublayer in layer.listLayers():
            process_layer(sublayer, sde_paths)
    elif layer.supports("DATASOURCE") and layer.isBroken:
        try:
            dataset_name = layer.name.strip() # Since connection properties shows None for broken files

            matched_sde = get_sde_path(dataset_name, sde_paths)
            if matched_sde:
                logging.info(f"Fixing layer '{layer.name}' (dataset:{dataset_name}) using {matched_sde}")
                
                # Robust: replace any workspace with the matched SDE
                layer.updateConnectionProperties("", matched_sde)
            else:
                logging.warning(f"No matching SDE found for dataset: {dataset_name}")
        except Exception as e:
            logging.error(f"Failed fixing {layer.name}: {e}")


def fix_aprx_connections(aprx_path, sde_paths):
    """Fix broken connections using matched SDE path."""
    try:
        aprx = arcpy.mp.ArcGISProject(aprx_path)
        logging.info(f"Processing APRX: {aprx_path}")

        for m in aprx.listMaps():
            for lyr in m.listLayers():
                process_layer(lyr, sde_paths)

        aprx.save()
        logging.info(f"Saved APRX: {aprx_path}")
        del aprx
        return True
    except Exception as e:
        logging.error(f"Error processing APRX {aprx_path}: {e}")
        return False


def main(aprx_folders, sde_folders):
    """Main function to process APRX files using SDE files from multiple folders."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # If a single string is given, wrap it into a list
    if isinstance(aprx_folders, str):
        aprx_folders = [aprx_folders]

    # Collect all .sde files from all sde folders
    sde_paths = []
    for folder in sde_folders:
        if os.path.isdir(folder):
            for f in os.listdir(folder):
                if f.lower().endswith(".sde"):
                    sde_paths.append(os.path.join(folder, f))
        else:
            logging.warning(f"Invalid SDE folder path: {folder}")

    if not sde_paths:
        logging.error("No SDE files found in the provided folders.")
        return

    # Collect all .aprx files from all aprx folders
    aprx_files = []
    for folder in aprx_folders:
        if os.path.isdir(folder):
            for root, dirs, files in os.walk(folder):
                for filename in files:
                    if filename.lower().endswith(".aprx"):
                        aprx_files.append(os.path.join(root, filename))
        else:
            logging.warning(f"Invalid APRX folder path: {folder}")

    if not aprx_files:
        logging.info("No APRX files found in the provided folders.")
        return

    # Process each APRX file
    for aprx_path in aprx_files:
        fix_aprx_connections(aprx_path, sde_paths)


# ------------------------------
# Usage
# ------------------------------
if __name__ == "__main__":
    user_input = input("Enter one or more APRX folders (separated by semicolons): ").strip() # Nb enter folder path containing aprx map, exclude this: ""
    aprx_folders = [f.strip() for f in user_input.split(";") if f.strip()]

    sde_folders = [
        r"\\gisfileintprd\DatabaseConnections\PublicationDB",
        r"\\gisfileintprd\DatabaseConnections\CaptureDB\ReadOnly",
        r"\\gisfileintprd\DatabaseConnections\CaptureDB"
    ]

    main(aprx_folders, sde_folders)