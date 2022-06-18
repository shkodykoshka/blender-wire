bl_info = {
    "name": "blender-wire",
    "author": "shkodykoshka",
    "version": (0, 0, 1),
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
import bmesh
import mathutils
from mathutils import Vector
import math

# buttons and sliders
class WireConfig(bpy.types.PropertyGroup):
    # turn on/off eight-segmented parabola for wire
    eight_part_wire : bpy.props.BoolProperty(name="Eight Part Parabola", description="Enable eight-segmented parabola", default=False)
    # increase/decrease droop of wire
    droop : bpy.props.FloatProperty(name="Droop",
                                    description = "Maximum droop at midpoint of wire in meters. Set to 0 to disable",
                                    default = 1.0,
                                    min = 0,
                                    max = 3.402823e+38
                                    )
    # increase/decrease tolerence for kd tree which finds coordinates
    kd_tol : bpy.props.FloatProperty(name="dist_tol",
                                     description="Tolerance of Mathutils KD Tree. KD Tree will find any matching coordinates within this radius, selecting first found",
                                     default = 0.0075,
                                     min = 0.0001,
                                     max = 0.5,
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
        box.prop(config, "eight_part_wire", text="Eight Segmented Parabola")
        
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