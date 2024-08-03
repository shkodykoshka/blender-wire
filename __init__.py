bl_info = {
    "name": "blender-wire",
    "author": "shkodykoshka",
    "version": (0, 0, 3),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Create > Wire",
    "description": "makes wire",
    "warning": "",
    "wiki_url":    "https://github.com/shkodykoshka/blender-wire",
    "tracker_url": "https://github.com/shkodykoshka/blender-wire",
    "category": "Add Mesh",
}

import bpy
from bpy.app.handlers import persistent
from . import wire_pole, wire_ops

# wire config
class WireConfig(bpy.types.PropertyGroup):
    # increase/decrease droop of wire
    droop : bpy.props.FloatProperty(name="Droop",
                                    description = "Maximum droop at midpoint of wire in meters. Set to 0 to disable",
                                    default = 1.0,
                                    min = 0,
                                    max = 3.402823e+38
                                    )
    # increase/decrease segments for parabolic wire. setting to 1 or 0 disables
    segments : bpy.props.IntProperty(name="w_segment",
                                     description="Amount of segments that make up parabolic wire. Set to 0 to disable",
                                     default = 16,
                                     min = 1,
                                     max = 8192
                                     )
    # enable/disable catenary wire
    catenary_wire : bpy.props.BoolProperty(name="Catenary", description="Enable catenary", default=False)
    # shade smooth
    shade_wire_smooth : bpy.props.BoolProperty(name="Shade Smooth", description="Shade Wire Smooth", default=True)
    # enable/disable wire with thickness
    thick_wire : bpy.props.BoolProperty(name="Thick Wire", description="Enable/disable wire with thickness", default = False)
    # change thickness of wire
    wire_thickness : bpy.props.FloatProperty(name="Wire Thickness",
                                             description="Thickness of wire in meters",
                                             default = 0.01,
                                             min = 0.001,
                                             max = 3.402823e+38,
                                             precision = 4,
                                             )
    # change amount of sides wire has
    wire_sides : bpy.props.IntProperty(name="Wire Sides",
                                       description="Sides wire has",
                                       default=4,
                                       min=3,
                                       max=8192)
    # update mode
    update_mode : bpy.props.EnumProperty(items=[("MANUAL", "Manual", "Update wire when button pressed", 0),
                                                ("AUTO", "Auto", "Update wire when config changes or pole is moved", 1)],
                                                name="Update Mode",
                                                description="When to update wire",
                                                default="MANUAL"
                                                )
    # enable/disable wire balls
    wire_balls_enabled : bpy.props.BoolProperty(name="Wire Balls", description="Enable/disable wire balls", default = False)
    # change wire ball radius
    wire_ball_radius : bpy.props.FloatProperty(name="Wire Ball Radius",
                                               description="Radius of wire ball in meters",
                                               default = 0.10,
                                               min = 0.001,
                                               max = 3.402823e+38,
                                               precision = 4,
                                               )
    # change wire ball sides
    wire_ball_sides : bpy.props.IntProperty(name="Wire Ball Sides",
                                            description="Amount of segments/sides that make up wire ball",
                                            default = 16,
                                            min = 1,
                                            max = 8192,
                                            )
    # change wire ball quantity
    wire_ball_amount : bpy.props.IntProperty(name="Wire Ball Amount",
                                             description="Amount of wire balls",
                                             default = 3,
                                             min = 1,
                                             max = 8192,
                                             )

@persistent
# update handler for selection change
def selection_change_handler(scene):
    # make sure user in object mode
    if bpy.context.mode != "OBJECT":
        return
    # get wanted updates
    for update in bpy.context.view_layer.depsgraph.updates:
        if (not update.is_updated_geometry and not update.is_updated_transform and not update.is_updated_shading):
            wire_ops.update_selection_order()
        break

@persistent
# update handler for pole position or config change
def pole_change_handler(scene):
    if bpy.context.mode != "OBJECT":
        return
    for update in bpy.context.view_layer.depsgraph.updates:
        if update.is_updated_transform:
            if bpy.context.scene.wire_config.update_mode == "AUTO":
                wire_ops.update_wire()
                wire_ops.update_wire_between_verts()
            break

# main menu
class WireUI(bpy.types.Panel):
    bl_idname = "WIRE_PT_ops_ui"
    bl_label = "Wire Configuration"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Wire"
    
    def draw(self, context):
        config = context.scene.wire_config
        # first section
        layout = self.layout
        col = layout.column()
        r1 = col.row(align=True)
        r1c1 = r1.column(align=True)
        # button to draw wire
        r1c1.operator("wire_ops.draw_parabolic", text="Draw Wire")
        # button to delete wire properties
        r2 = col.row(align=True)
        r2c1 = r2.column(align=True)
        r2c1.prop(config, "update_mode", text="Update Mode")

        # second section
        col = layout.column()
        col.label(text="Configuration")
        # rows for second section
        col.prop(config, "droop", text="Droop")
        col.prop(config, "segments", text="Wire Segments")
        col.label(text=" ")
        # button to update wire
        col.operator("wire_ops.manual_update_wire", text="Update Wire")
        col.operator("wire_ops.wire_between_vertices", text="Wire Between Vertices")

# dropdown menu under main manu
class WireSubUI(bpy.types.Panel):
    bl_idname = "WIRE_PT_sub_ui"
    bl_parent_id = "WIRE_PT_ops_ui"
    bl_label = "Other Wire Options"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Wire"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        col = self.layout.column()
        config = context.scene.wire_config
        # buttons to change more wire options
        col.prop(config, "catenary_wire", text="Catenary")
        col.prop(config, "shade_wire_smooth", text="Shade Smooth")
        col.prop(config, "thick_wire", text="Mesh Wire")
        col.prop(config, "wire_thickness", text="Wire Thickness")
        col.prop(config, "wire_sides", text="Wire Sides")
        col.operator("wire_ops.remove_wire_props", text="Delete Wire Props")

# dropdown menu with wire ball configuration
class WireBallsUI(bpy.types.Panel):
    bl_idname = "WIRE_PT_balls_ui"
    bl_parent_id = "WIRE_PT_ops_ui"
    bl_label = "Wire Balls"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Wire"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        col = self.layout.column()
        config = context.scene.wire_config
        # buttons to change settings regarding balls
        col.prop(config, "wire_balls_enabled", text="Enable Wire Balls")
        col.prop(config, "wire_ball_radius", text="Wire Ball Radius")
        col.prop(config, "wire_ball_sides", text="Wire Ball Sides")
        col.prop(config, "wire_ball_amount", text="Wire Ball Amount")

# dropdown menu with pole operators 
class WirePoleUI(bpy.types.Panel):
    bl_idname = "WIRE_PT_pole_ui"
    bl_parent_id = "WIRE_PT_ops_ui"
    bl_label = "Pole Options"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Wire"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        col = self.layout.column()
        # buttons to create poles
        col.operator("wire_pole.create_pole_input", text="Create Pole Input")
        col.operator("wire_pole.create_pole_output", text="Create Pole Output")
        col.operator("wire_pole.delete_pole", text="Delete Pole")
        col.operator("wire_pole.print_poles", text="Print Pole") #<-- debug

# classes that will be registered
classesToRegister = [
    wire_ops.WireMain,
    wire_ops.RemoveWireProps,
    wire_ops.ManualUpdateWire,
    wire_ops.WireBetweenVertices,
    wire_pole.CreatePoleInput,
    wire_pole.CreatePoleOutput,
    wire_pole.PrintPoles,
    wire_pole.DeletePole,
    WireConfig,
    WireUI,
    WireSubUI,
    WireBallsUI,
    WirePoleUI,
]

def register():
    for cls in classesToRegister:
        bpy.utils.register_class(cls)
    # register handlers and config
    bpy.app.handlers.depsgraph_update_post.append(selection_change_handler)
    bpy.app.handlers.depsgraph_update_post.append(pole_change_handler)
    bpy.types.Scene.wire_config = bpy.props.PointerProperty(type=WireConfig)
    
def unregister():
    # unregister (delete) handlers and config
    del bpy.types.Scene.wire_config
    bpy.app.handlers.depsgraph_update_post.remove(selection_change_handler)
    bpy.app.handlers.depsgraph_update_post.remove(pole_change_handler)
    # unregister classes
    for cls in classesToRegister:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    # selection change handler (remove if already there)
    for deps_handle in bpy.app.handlers.depsgraph_update_post:
        if deps_handle.__name__ == "selection_change_handler":
            bpy.app.handlers.depsgraph_update_post.remove(deps_handle)
    # pole change handler
    for deps_handle in bpy.app.handlers.depsgraph_update_post:
        if deps_handle.__name__ == "pole_change_handler":
            bpy.app.handlers.depsgraph_update_post.remove(deps_handle)
    register()