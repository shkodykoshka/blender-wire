import bpy
import json
import os

# makes input for pole (wires ENTERING pole)
class CreatePoleInput(bpy.types.Operator):
    bl_idname = "wire_pole.create_pole_input"
    bl_label = "Create Pole"
    bl_description = "Create a pole input from selected vertices"
    bl_options = {"REGISTER"}

    def execute(self, context):
        # adding input, checking output
        PolesDict().create_pole("input", "output")
        return {"FINISHED"}

# makes output for pole (wires EXITING pole)
class CreatePoleOutput(bpy.types.Operator):
    bl_idname = "wire_pole.create_pole_output"
    bl_label = "Create Pole"
    bl_description = "Create a pole output from selected vertices"
    bl_options = {"REGISTER"}

    def execute(self, context):
        # adding output, checking input
        PolesDict().create_pole("output", "input")
        return {"FINISHED"}

# prints input/output for current selected pole
class PrintPoles(bpy.types.Operator):
    bl_idname = "wire_pole.print_poles"
    bl_label = "Print Pole"
    bl_description = "Prints pole to console"
    bl_options = {"REGISTER"}

    def execute(self, context):
        print(PolesDict().poles)
        return {"FINISHED"}

class DeletePole(bpy.types.Operator):
    bl_idname = "wire_pole.delete_pole"
    bl_label = "Delete Pole"
    bl_description = "Deletes currently selected pole"
    bl_options = {"REGISTER"}

    def execute(self, context):
        # get current selected object name (pole entry name)
        obj = bpy.context.active_object
        obj_name = obj.name.split('.')[0]
        # delete pole if it exists
        PolesDict().delete_pole(obj_name)
        return {"FINISHED"}


class PolesDict():
    # get poles.json path
    def __init__(self):
        self.poles = {}
        #print("read file") #<-- debug
        # get path of current file to find json in same directory
        self.json_path = os.path.join(os.path.dirname(__file__), "poles.json")
        # read json if it exists
        if os.path.exists(self.json_path):
            self.poles = self.read_poles(self.json_path)
    
    # writes poles to poles.json
    def dump_poles(self, poles, filepath):
        with open(filepath, "w") as f:
            json.dump(poles, f, indent=4)
    
    # reads poles.json
    def read_poles(self, filepath):
        with open(filepath, "r") as f:
            poles = json.load(f)
        return poles
    
    def delete_pole(self, name):
        if name in self.poles:
            self.poles.pop(name)
            # dump
            self.dump_poles(self.poles, self.json_path)

    # gets currently s4elected vertices
    def get_vertices(self):
        # set to object mode and then to edit mode to update
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.mode_set(mode="EDIT")
        # get selected vertices in order
        selected_verts = [tuple(v.co) for v in bpy.context.active_object.data.vertices if v.select]
        return selected_verts

    # creates pole intput/output depending on add_key
    # check_key is used to preserve other key in pole
    def create_pole(self, add_key, check_key):
        # create a pole output from selected vertices
        selected_verts = PolesDict().get_vertices()
        # get selected object
        obj = bpy.context.active_object
        obj_name = obj.name.split('.')[0]
        # check if pole with current name already exists
        if obj_name in self.poles:
            # if check_key exists, save it
            if check_key in self.poles[obj_name]:
                poles_check_key = self.poles[obj_name][check_key]
            else:
                poles_check_key = None
            # delete entry for pole
            self.poles.pop(obj_name)
            # create new entry for pole with add_key
            self.poles[obj_name] = {add_key: selected_verts}
            # add check_key if previously existed
            if poles_check_key:
                self.poles[obj_name][check_key] = poles_check_key
        # if pole does not exist create it with add_key
        else:
            self.poles[obj_name] = {add_key: selected_verts}
        # dump poles
        self.dump_poles(self.poles, self.json_path)