bl_info = {
    "name": "blender-wire",
    "author": "shkodykoshka",
    "version": (0, 0, 2),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Create > Wire",
    "description": "makes wire",
    "warning": "",
    "wiki_url":    "https://github.com/shkodykoshka/blender-wire",
    "tracker_url": "https://github.com/shkodykoshka/blender-wire",
    "support": 'OFFICIAL',
    "category": "Add Mesh",
}

_modules = [
    'wire_ops',
]


__import__(name=__name__, fromlist=_modules)
_namespace = globals()
_modules_loaded = [_namespace[name] for name in _modules]
del _namespace

import bpy

# buttons and sliders
class WireConfig(bpy.types.PropertyGroup):
    # turn on/off eight-segmented parabola for wire
    eight_part_wire : bpy.props.BoolProperty(name="Eight Part Parabola", description="Enable eight-segmented parabola", default=False)
    # turn on/off catenary for wire
    catenary_wire : bpy.props.BoolProperty(name="Catenary", description="Enable catenary", default=False)
    # turn on/off checking if coordinates exist in model
    check_wire : bpy.props.BoolProperty(name="Check Coordinates",
                                        description="Enable checking coordinates. Checks if coordinates exist in model. Disable if recieving 'IndexError: list index out of range' error",
                                        default=True
                                        )
    # turn on/off auto-droop
    auto_droop : bpy.props.BoolProperty(name="Auto Droop", description="Changes droop values based on distance wire travels. When enabled user droop value has no effect", default=False)
    # turn on/off auto-segments
    auto_segments : bpy.props.BoolProperty(name="Auto Segments", description="Changes amount of segments in wire based on distance wire travels. When enabled user segments value has no effect", default=False)
    # increase/decrease droop of wire
    droop : bpy.props.FloatProperty(name="Droop",
                                    description = "Maximum droop at midpoint of wire in meters. Set to 0 to disable",
                                    default = 1.0,
                                    min = 0,
                                    max = 3.402823e+38
                                    )
    # increase/decrease tolerence for kd tree which finds coordinates
    kd_tol : bpy.props.FloatProperty(name="dist_tol",
                                     description="Tolerance of Mathutils KD Tree. KD Tree will find any matching coordinates within this radius, using first found",
                                     default = 0.0075,
                                     min = 0.0001,
                                     max = 10,
                                     precision = 4,
                                     step = 1,
                                     )
    # increase/decrease segments for parabolic wire. setting to 1 or 0 disables
    segments : bpy.props.IntProperty(name="w_segment",
                                     description="Amount of segments that make up parabolic wire. Set to 0 to disable. Does not work with eight-segmented wire",
                                     default = 16,
                                     min = 0,
                                     max = 8192
                                     )
    # balls enabled/disabled
    wire_balls : bpy.props.BoolProperty(name="Balls", description="Enable/disable balls", default=False)
    # balls amount
    wire_balls_amount: bpy.props.IntProperty(name="Ball Amount",
                                            description="Amount of balls",
                                            default=3,
                                            min=0,
                                            max=8192
                                            )
    # balls radius
    wire_balls_radius : bpy.props.FloatProperty(name="Ball Radius",
                                               description="Radius of ball in meters",
                                               default = 0.25,
                                               min = 0.01,
                                               max = 3.402823e+38,
                                               )
    # balls size
    wire_balls_sides : bpy.props.IntProperty(name="Ball Sides",
                                            description="Amount of sides of ball",
                                            default = 8,
                                            min = 3,
                                            max = 8192
                                            )


# panel ui
class WireUI(bpy.types.Panel):
    bl_idname = 'wire_ops_ui'
    bl_label = 'Wire Configuration'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Wire'
    bl_context = 'objectmode'
    
    def draw(self, context):
        # first section
        layout = self.layout
        col = layout.column()
        r = col.row(align=True)
        r1c1 = r.column(align=True)
        # button to draw wire
        r1c1.operator("wire_ops.draw_parabolic", text='Draw Wire')
        
        # second section
        col = layout.column()
        col.label(text="Configuration")
        
        config = context.scene.config
        box = self.layout.box()
        # buttons to change stuff
        box.prop(config, "droop", text="Droop")
        box.prop(config, "segments", text="Wire Segments")
        box.prop(config, "kd_tol", text="KD Tree Tolerance")
        box.prop(config, "check_wire", text="Check Coordinates")
        box.prop(config, "auto_droop", text="Auto Droop")
        box.prop(config, "auto_segments", text="Auto Segments")
        box.prop(config, "eight_part_wire", text="Eight Segmented Parabola")
        box.prop(config, "catenary_wire", text="Catenary")
        # balls
        box.prop(config, "wire_balls", text="Wire balls")
        if config.wire_balls:
            box.prop(config, "wire_balls_amount", text="Amount")
            box.prop(config, "wire_balls_radius", text="Radius")
            box.prop(config, "wire_balls_sides", text="Sides")
        
# registration
classesToRegister = [
    wire_ops.WireMain,
    WireConfig,
    WireUI
]

registerClasses, unregisterClasses = bpy.utils.register_classes_factory(classesToRegister)

def register():
    registerClasses()
    bpy.types.Scene.config = bpy.props.PointerProperty(type=WireConfig)
    
def unregister():
    del bpy.types.Scene.config
    unregisterClasses()

if __name__ == "__main__":
    register()