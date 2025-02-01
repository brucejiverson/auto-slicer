import adsk.core
import adsk.fusion
import adsk.cam
import os

# Bulk export Fusion 360 Body objects as .STL files, optionally changing
# orientation.

# TASKS/QUESTIONS:
#   TODO: Is Export Components needed?  Currently just searches top level Bodies.  Is nested
#       search needed?  Could use allOccurrences, but would then need smarter logic to exclude tiny
#       parts not intended to be printed e.g. Hemera gears and nuts.  Would probably end up needing
#       more complex graph exclusion/filter syntax support...

# RESOURCES:
# - STLExport API Sample https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-ECA8A484-7EDD-427D-B1E3-BD59A646F4FA
# - UI Logger https://modthemachine.typepad.com/my_weblog/2021/03/log-debug-messages-in-fusion-360.html
# - Also, have sprinkled code with links to Fusion 360 API reference docs.

# FUTURES:
#   TODO: Auto generate .STL filename that includes part count != 1, e.g. "Z Belt Holder (x3).stl"
#   TODO: Emit Design version number or date as file prefix? e.g. fileVersion  = app.activeDocument.
#       dataFile.latestVersionNumber
#   TODO: Write files to versioned subdir? Diff? "c:\\git\\v1engineering-mods\\mp3dp-v4\\models\\v51\\..."
#   TODO:P2 Drag-n-drop MP3DP files into Cura 5.0 were automatically OK.  So, may not need to use
#       body.boundingBox to autocenter XY, and ensure Z > 0.

# Target folder.  WARNING: Existing files are overwritten.
target_folder = "./"

# Filter used to only export parts containing this expression in the Body name.   Usually used when
# wanting to quickly figure out rotation expression for a specific part, without having to export
# everything.
filter_expression = ""

# Body names containing these substrings will NOT be exported.
excludes = ["(1)", "(2)", "Frame", "MGN12H", "12H Block", "HEMERA"]

# Maximum files to export.  Implemented as safe guard, since haven't figured out how to cancel
# running script without killing the app.
max_export_count = 100

pi = 3.1415926535897931


class UiLogger:
    """Logger class to print messages to the Fusion 360 UI."""

    def __init__(self, force_update):
        """
        Initializes the UiLogger.

        Args:
            force_update (bool): If True, forces the UI to update after printing a message.
        """
        app = adsk.core.Application.get()
        ui = app.userInterface
        palettes = ui.palettes
        self.text_palette = palettes.itemById("TextCommands")
        self.force_update = force_update
        self.text_palette.isVisible = True

    def print(self, text):
        """
        Prints a message to the Fusion 360 UI text palette.

        Args:
            text (str): The message to print.
        """
        self.text_palette.writeText(text)
        if self.force_update:
            adsk.doEvents()


def apply_transformations(body, body_name, root_comp, comp, logger):
    """
    Applies transformations to the body based on its name.

    Args:
        body (adsk.fusion.BRepBody): The body to transform.
        body_name (str): The name of the body.
        root_comp (adsk.fusion.Component): The root component of the design.
        comp (adsk.fusion.Component): The component containing the body.
        logger (UiLogger): The logger to print messages.

    Returns:
        tuple: The transformed body name and a list of temporary transforms applied.
    """

    temp_transforms = []
    body_parts = body_name.split("(")
    export_body_name = body_parts[0].strip()
    rotate_exprs = body_parts[1].replace(
        ")", "").strip().split(",")
    logger.print(
        f"Rotating {body_name}, transform... x: {
            rotate_exprs[0]}, y: {
            rotate_exprs[1]}, z: {
            rotate_exprs[2]}")

    for iter_axis in range(3):
        rotation_deg = int(rotate_exprs[iter_axis])

        if rotation_deg == 0:
            continue

        rotation_rad = rotation_deg * pi / 180.0
        items_to_move = adsk.core.ObjectCollection.create()
        items_to_move.add(body)

        if iter_axis == 0:
            axis_vector = root_comp.xConstructionAxis.geometry.getData()[
                2]
        elif iter_axis == 1:
            axis_vector = root_comp.yConstructionAxis.geometry.getData()[
                2]
        else:
            axis_vector = root_comp.zConstructionAxis.geometry.getData()[
                2]

        transform = adsk.core.Matrix3D.create()
        transform.setToRotation(
            rotation_rad,
            axis_vector,
            root_comp.originConstructionPoint.geometry)

        move_feats = comp.features.moveFeatures
        move_feature_input = move_feats.createInput(
            items_to_move, transform)
        new_move_feature = move_feats.add(move_feature_input)
        temp_transforms.append(new_move_feature)
        return export_body_name, temp_transforms


def run(context):
    """
    Main function to export Fusion 360 components as .STL files.

    Args:
        context: The context in which the script is run.

    Raises:
        Exception: If there is an error during the export process.

    This function performs the following steps:
        1. Initializes the logger.
        2. Retrieves the application, user interface, active design, root component, and occurrences.
        3. Iterates through the occurrences and exports each visible component as an .STL file.
        4. Applies transformations to the components based on their names if specified.
        5. Exports the components to the specified target folder.
        6. Logs the export process and displays a message box upon completion.
    """
    logger = UiLogger(True)

    # Get the application and the active design.
    app = adsk.core.Application.get()
    ui = app.userInterface
    design = app.activeProduct
    root_comp = design.rootComponent
    occurrences = root_comp.occurrences

    curr_export_count = 0
    for occ in occurrences:
        if not occ.isLightBulbOn:
            continue

        if curr_export_count >= max_export_count:
            break

        comp = occ.component

        if any(comp.name.find(exclude) != -1 for exclude in excludes):
            continue

        export_mgr = design.exportManager

        for body in comp.bRepBodies:
            body_name = body.name
            body_name = body_name.replace("(1)", "").strip()

            if len(filter_expression) > 0 and body_name.find(
                    filter_expression) == -1:
                continue

            export_body_name = body_name

            if "(" in body_name and ")" in body_name and body_name.index("(") < body_name.index(
                    ")") and len(body_name.split("(")[1].replace(")", "").strip().split(",")) == 3:
                export_body_name, temp_transforms = apply_transformations(
                    body, body_name, root_comp, comp, logger)
            else:
                temp_transforms = []

            file_name = target_folder + export_body_name + ".stl"
            options = export_mgr.createSTLExportOptions(body, file_name)
            export_mgr.execute(options)

            for transform in reversed(temp_transforms):
                transform.deleteMe()

            temp_transforms.clear()
            logger.print("Exported " + file_name)

        curr_export_count += 1

    logger.print("Done!")
    ui.messageBox('Export Done!')
