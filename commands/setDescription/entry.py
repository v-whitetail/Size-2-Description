import adsk.core, adsk.fusion
import os
from ...lib import fusionAddInUtils as futil
from ...lib.Classes import ImperialFraction
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface

CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_palette_send'
CMD_NAME = 'Set to Description'
CMD_Description = 'Set Component Descriptions as Sizes'
IS_PROMOTED = True

PALETTE_ID = config.sample_palette_id

WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidModifyPanel'
COMMAND_BESIDE_ID = ''

ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

local_handlers = []

def start():
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)
    futil.add_handler(cmd_def.commandCreated, command_created)
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)
    control.isPromoted = IS_PROMOTED

def stop():
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)
    if command_control:
        command_control.deleteMe()
    if command_definition:
        command_definition.deleteMe()

def command_created(args: adsk.core.CommandCreatedEventArgs):
    futil.log(f'{CMD_NAME} Command Created Event')
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)

    args.command.setDialogSize(360,180)
    inputs = args.command.commandInputs

    unit_style_input = inputs.addDropDownCommandInput(
        'unit_style_input',
        'Unit Style',
        adsk.core.DropDownStyles.TextListDropDownStyle,
    )
    _imperial_inches_input = unit_style_input.listItems.add('Imperial Inches', True)
    _decimal_inches_input = unit_style_input.listItems.add('Decimal Inches', False)
    _millimeters_input = unit_style_input.listItems.add('Millimeters', False)
    _centimeters_input = unit_style_input.listItems.add('Centimeters', False)
    _meters_input = unit_style_input.listItems.add('Meters', False)

    decimal_precision_input = inputs.addIntegerSpinnerCommandInput(
        'decimal_precision_input',
        'Decimal Precision',
        0,
        8,
        1,
        3
    )
    decimal_precision_input.isVisible = False

    bounding_method_input = inputs.addDropDownCommandInput(
        'bounding_method_input',
        'Bounding Method',
        adsk.core.DropDownStyles.TextListDropDownStyle
    )
    _minimum_relative_bounds = bounding_method_input.listItems.add('Minimum Bounding Box', True)
    _minimum_absolute_bounds = bounding_method_input.listItems.add('Coordinate Bounding Box', False)

def command_execute(args: adsk.core.CommandEventArgs):
    design = adsk.fusion.Design.cast(app.activeProduct)

    futil.log(f'{CMD_NAME} Command Execute Event')
    inputs = args.command.commandInputs

    unit_style_input = adsk.core.DropDownCommandInput.cast(inputs.itemById('unit_style_input'))
    decimal_precision_input = adsk.core.IntegerSpinnerCommandInput.cast(inputs.itemById('decimal_precision_input'))
    bounding_method_input = adsk.core.DropDownCommandInput.cast(inputs.itemById('bounding_method_input'))

    bounding = minimum_bounding_box
    if bounding_method_input.selectedItem.name == 'Coordinate Bounding Box':
        bounding = coordinate_bounding_box

    precision = decimal_precision_input.value
    formatter = lambda value: float, 'SCRIPT ERROR'
    if unit_style_input.selectedItem == 'Decimal Inches':
        formatter = lambda value: design.fusionUnitsManager.formatValue(value, 'in', precision, showUnits=True)
    elif unit_style_input.selectedItem == 'Millimeters':
        formatter = lambda value: design.fusionUnitsManager.formatValue(value, 'mm', precision, showUnits=True)
    elif unit_style_input.selectedItem == 'Centimeters':
        formatter = lambda value: design.fusionUnitsManager.formatValue(value, 'cm', precision, showUnits=True)
    elif unit_style_input.selectedItem == 'Meters':
        formatter = lambda value: design.fusionUnitsManager.formatValue(value, 'm', precision, showUnits=True)
    else:
        formatter = lambda value: f'{ImperialFraction.from_measurement(value, design.fusionUnitsManager)}'

    for component in design.allComponents:
        thickness, width, length = map(formatter, bounding(component))
        component.description = f'{thickness} x {width} x {length}'

def command_preview(args: adsk.core.CommandEventArgs):
    inputs = args.command.commandInputs
    futil.log(f'{CMD_NAME} Command Preview Event')

def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')
    inputs = args.inputs

    if changed_input.id == 'unit_style_input':
        unit_style_input = adsk.core.DropDownCommandInput.cast(changed_input)
        decimal_precision_input = adsk.core.IntegerSpinnerCommandInput.cast(inputs.itemById('decimal_precision_input'))
        if unit_style_input.selectedItem.name == 'Imperial Inches':
            decimal_precision_input.isVisible = False
        else:
            decimal_precision_input.isVisible = True

def command_destroy(args: adsk.core.CommandEventArgs):
    global local_handlers
    local_handlers = []
    futil.log(f'{CMD_NAME} Command Destroy Event')

def minimum_bounding_box(component: adsk.fusion.Component):
    bounding_box = component.orientedMinimumBoundingBox
    return sorted([bounding_box.length, bounding_box.width, bounding_box.height])

def coordinate_bounding_box(component: adsk.fusion.Component):
    bounding_box = component.boundingBox2(adsk.fusion.BoundingBoxEntityTypes.SolidBRepBodyBoundingBoxEntityType)
    return sorted(bounding_box.minPoint.vectorTo(bounding_box.maxPoint).asArray())