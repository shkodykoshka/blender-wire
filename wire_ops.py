import bpy
import math
import mathutils
from . import wire_pole

# https://blender.stackexchange.com/questions/253427/python-blender-get-selected-object-in-order-of-selection
# gets list of selected objects in order of selection
def get_ordered_selection_objects():
    # list of selected objects
    tagged_objects = []
    for obj in bpy.data.objects:
        # if no "selection_order" exists for current object -1 is returned
        order_index = obj.get("selection_order", -1)
        if order_index >= 0:
            tagged_objects.append((order_index, obj))
    tagged_objects = sorted(tagged_objects, key=lambda item: item[0])
    return [obj for i, obj in tagged_objects]

# clears selection order flag
def clear_order_flag(obj):
    try:
        del obj["selection_order"]
    except KeyError:
        pass

# updates selection order when object is selected or deselected
def update_selection_order():
    # do not want selection order for 
    if not bpy.context.selected_objects:
        for obj in bpy.data.objects:
            clear_order_flag(obj)
        return
    selection_order = get_ordered_selection_objects()
    idx = 0
    for obj in selection_order:
        if not obj.select_get():
            selection_order.remove(obj)
            clear_order_flag(obj)
        else:
            obj["selection_order"] = idx
            idx += 1
    for obj in bpy.context.selected_objects:
        if obj not in selection_order:
            obj["selection_order"] = len(selection_order)
            selection_order.append(obj)

# deletes existing wires and cleans up left over meshes
def remove_existing_wires(start_obj, end_obj):
    # delete existing wires
    if start_obj is not None:
        if start_obj.get("output_wire", None):
            for wire in start_obj["output_wire"]:
                #print(wire) #<-- debug
                if wire is not None:
                    bpy.data.objects.remove(wire)
            del start_obj["output_wire"]
        if start_obj.get("output_wire_balls", None):
            for ball in start_obj["output_wire_balls"]:
                if ball is not None:
                    bpy.data.objects.remove(ball)
            del start_obj["output_wire_balls"]
        if start_obj.get("start_vector", None):
            del start_obj["start_vector"]
    if end_obj is not None:
        if end_obj.get("input_wire", None):
            for wire in end_obj["input_wire"]:
                if wire is not None:
                    bpy.data.objects.remove(wire)
            del end_obj["input_wire"]
        if end_obj.get("input_wire_balls", None):
            for ball in end_obj["input_wire_balls"]:
                if ball is not None:
                    bpy.data.objects.remove(ball)
            del end_obj["input_wire_balls"]
        if end_obj.get("end_vector", None):
            del end_obj["end_vector"]
    # delete existing wire meshes with no users (leftover from deleted wires)
    # otherwise there will be many meshes with no users and slows blender down
    for mesh_block in bpy.data.meshes:
        if mesh_block.users == 0:
            #print(f'Deleting mesh {mesh_block.name}')
            bpy.data.meshes.remove(mesh_block)

# gets the selected poles from ordered selection
def get_selected_poles():
    selected_poles = []
    for obj in get_ordered_selection_objects():
        if obj.name.split('.')[0] in wire_pole.PolesDict().poles:
            selected_poles.append(obj)
        else:
            print(f"{obj.name} not in pole_dict")
    return selected_poles

# gets mushroom coordinates of selected pole
def get_mushroom(pole_name):
    pole_name = pole_name.split('.')[0]
    #if pole_name in self.pole_dict:
    if pole_name in wire_pole.PolesDict().poles:
        # returns dict with input and output keys containing input or output coordinates
        return wire_pole.PolesDict().poles[pole_name]
    else:
        print(f"{pole_name} not in pole_dict")
        return None

# gets coordinates of mushroom with respect to world origin
def get_coordinates(obj, mushroom):
    # vector with local coordinates for mushroom (if pole origin is at world origin)
    coord_vector = mathutils.Vector(mushroom)
    # apply world transform to local coordinates vector to get translated and rotated coordinates
    global_coord_vector = obj.matrix_world @ coord_vector
    return global_coord_vector

# get z coordinate for parabola or catenary (use correct equation depending on catenary_enabled)
def get_wire_z(x, p_segment, pole_dist, droop, catenary_enabled, start_z):
    if catenary_enabled:
        #print("catenary") #<-- debug
        a = (pole_dist**2)/(8*droop)
        # fixing catenary equation constant
        a_tol = 0.5
        # x needs to be start x to get correct constant
        dummy_x = -(pole_dist/2)
        catenary = a*(math.cosh((dummy_x)/a)) + (start_z-a-droop)
        # check if constant is within tolerance
        while not (catenary <= (start_z + a_tol) and catenary >= (start_z - a_tol)):
            if catenary >= (start_z + a_tol):
                a += 0.1
            elif catenary <= (start_z - a_tol):
                a -= 0.1
            catenary = a*(math.cosh((dummy_x)/a)) + (start_z-a-droop)
        return a*(math.cosh((x+p_segment)/a)) - a
    else:
        #print("parabola") #<-- debug
        a = droop/((pole_dist**2)/4)
        return a*((x+p_segment)**2)
    
# draws a ball with radius and sides at given coordinates
# not using blender primitive sphere as they cause issues with auto updating
def draw_ball(radius, sides, start_x, start_y, start_z):
    # angle increment for horizontal circle (angle between vertices)
    h_angle_increment = (2*math.pi)/sides

    # top and bottom points of circle
    top = (start_x, start_y, start_z+radius)
    bottom = (start_x, start_y, start_z-radius)
    # coordinate list
    c_list = []
    # face list
    f_list = []
    # add bottom to coordinate list because starting at -90 degrees
    c_list.append(bottom)

    # angle (theta) for horizontal circle
    h_angle = 0
    # angle (phi) for vertical circle
    v_angle = -math.pi/2  # setting to -90 degrees

    # making points
    # amount of horizontal circles
    h_circle_count = sides  # (sides - 2)/2 -> sides
    # increment for vertical circle (angle between horizontal circles)
    v_angle_increment = (2*math.pi)/(2*h_circle_count)
    # draw many horizontal circles with different radii
    for h_circle in range(int(h_circle_count)):
        # start angle at -90 degrees + increment
        v_angle += v_angle_increment
        for i in range(sides):
            # radius of horizontal circle based on vertical angle
            h_radius = radius*math.cos(v_angle)
            # x y and z coordinates
            x = h_radius*(math.cos(h_angle)) + start_x
            y = h_radius*(math.sin(h_angle)) + start_y
            z = radius*math.sin(v_angle) + start_z
            # add coordinate tuple to list
            c_list.append((x, y, z))
            # increment horizontal angle
            h_angle += h_angle_increment

    # add top to list
    c_list.append(top)

    # bottom section
    for v in range(sides):
        v += 1  # skip bottom, bottom is 0
        face = (v+1, v, 0)
        # if v is last point on bottom circle, connect to first point
        if v == sides:
            face = (1, v, 0)
        f_list.append(face)

    # middle sections
    for circle in range(int(h_circle_count)-1):
        for v in range(sides):
            v += 1 + (sides*(circle+1))  # skip bottom and go to current point
            # 0 + 1 + (8*(0+1)) = 9
            face = (v, v-sides, v-sides+1, v+1)  # v, v+1, v-sides+1, v-sides
            # if v is last point on current horizontal circle, connect to first point (in 8 segment circle, it is 16, 24, etc.)
            if v == (sides*(circle+2)):
                face = (v, v-sides, v-sides-sides+1, v-sides+1)
            f_list.append(face)

    # top section
    for v in range(sides):
        v += 1 + sides*(int(h_circle_count)-1)  # go to current point
        h = len(c_list)-1  # top point
        face = (h, v, v+1)
        # if v is last point before top point connect to first point in this circle
        if v == (sides*(int(h_circle_count))):
            face = (h, v, v-sides+1)
        f_list.append(face)

    # balls that are created are named ball
    obj_name = "ball"
    scn = bpy.context.collection
    ball_mesh = bpy.data.meshes.new(obj_name)
    ball_ob = bpy.data.objects.new(obj_name, ball_mesh)
    scn.objects.link(ball_ob)
    # making all points and drawing line between them
    ball_mesh.from_pydata(c_list, [], f_list)
    for poly in ball_mesh.polygons:
        poly.use_smooth = True
    ball_mesh.update()
    return ball_ob

# draw wire using quadratic equation
# can modify droop and segments
def draw_parabolic(w_name, droop, w_segment, start_x, start_y, start_z, end_x, end_y, end_z, catenary_enabled):
    # get distance bewteen poles
    pole_dist = math.sqrt((end_x-start_x)**2 + (end_y-start_y)**2 + (end_z-start_z)**2)
    # distance per segment
    p_segment = pole_dist/w_segment

    x_list = []
    y_list = []
    z_list = []
    x = -(pole_dist/2)
    # create list of coordinates for parabola
    for i in range(1, w_segment):
        # get x, y, z
        wire_z = get_wire_z(x, p_segment, pole_dist, droop, catenary_enabled, start_z) + ((start_z+(i*((end_z-start_z)/w_segment)))-droop)
        x_list.append((start_x+(i*((end_x-start_x)/w_segment))))
        y_list.append((start_y+(i*((end_y-start_y)/w_segment))))
        z_list.append(wire_z)
        x += p_segment

    # adding coordinates to tuple
    co_list = [(start_x, start_y, start_z), (end_x, end_y, end_z)]
    ln_list = [(0, 1)]
    for i in range(1, w_segment):
        co_list.insert(i, (x_list[i-1], y_list[i-1], z_list[i-1]))
        ln_list.append((i, (i+1)))

    scn = bpy.context.collection
    w_mesh = bpy.data.meshes.new(w_name)
    w_obj = bpy.data.objects.new(w_name, w_mesh)
    scn.objects.link(w_obj)
    # making all points and lines
    w_mesh.from_pydata(co_list, ln_list, [])
    w_mesh.update()
    return w_obj

# draw line between start and end points for straight wire
# this is when droop is 0 or segments is 1
def draw_wire(w_name, start_x, start_y, start_z, end_x, end_y, end_z):
    co_list = [(start_x, start_y, start_z), (end_x, end_y, end_z)]
    ln_list = [(0, 1)]
    scn = bpy.context.collection
    w_mesh = bpy.data.meshes.new(w_name)
    w_obj = bpy.data.objects.new(w_name, w_mesh)
    scn.objects.link(w_obj)
    # making all points and lines
    w_mesh.from_pydata(co_list, ln_list, [])
    w_mesh.update()
    return w_obj

# draw 3d wire between start and end points for straight wire (draw_wire but with thickness)
def draw_wire_3d(w_name, radius, start_x, start_y, start_z, end_x, end_y, end_z, sides, shade_smooth):
    angle_increment = (2*math.pi)/sides
    path_list = [(start_x, start_y, start_z), (end_x, end_y, end_z)]
    c_list = []
    # make circles
    angle = 0
    for i in range(len(path_list)-1):
        # current point
        x, y, z = path_list[i]
        # next point
        x2, y2, z2 = path_list[i+1]
        # doing the same thing for all points in the circle (sides)
        for j in range(sides):
            # make directional vector between current and next point
            dir_vec = mathutils.Vector((x2-x, y2-y, 0))
            # make rotational axis vector (to rotate around later)
            rot_vec = mathutils.Vector((x2-x, y2-y, z2-z))

            # make the point on the circle
            # its a vector parallel to current wire segment with length of radius
            point = ((mathutils.Vector((x, y, z)) + (dir_vec.normalized())*radius) - mathutils.Vector((x, y, z)))
            # rotate point to be perpendicular to wire segment
            point.rotate(mathutils.Euler((0, 0, math.radians(90)), "XYZ"))
            # make 3x3 rotational matrix to rotate point around rot_vec
            rot_mat = mathutils.Matrix.Rotation(angle, 3, rot_vec)
            # rotate point by matrix
            point.rotate(rot_mat)
            # move point back to correct coordinates
            point += mathutils.Vector((x, y, z))
            # add point to list
            c_list.append((point.x, point.y, point.z))
            # increment angle
            angle += angle_increment

    # make directional vector between current and next point
    dir_vec = mathutils.Vector((end_x-start_x, end_y-start_y, 0))
    # make rotational axis vector (to rotate around later)
    rot_vec = mathutils.Vector((end_x-start_x, end_y-start_y, end_z-start_z))
    for i in path_list:
        # get x, y, z from current point
        x, y, z = i
        for j in range(sides):
            # make point on the circle
            # its a vector parallel to current wire with length of radius
            point = ((mathutils.Vector((x, y, z)) + (dir_vec.normalized())*radius) - mathutils.Vector((x, y, z)))
            # rotate point to be perpendicular to wire
            point.rotate(mathutils.Euler((0, 0, math.radians(90)), "XYZ"))
            # make 3x3 rotational matrix to rotate point around rot_vec
            rot_mat = mathutils.Matrix.Rotation(angle, 3, rot_vec)
            # rotate point by matrix
            point.rotate(rot_mat)
            # move point back to correct coordinates
            point += mathutils.Vector((x, y, z))
            # add point to list
            c_list.append((point.x, point.y, point.z))
            # increment angle
            angle += angle_increment

    # making faces
    f_list = []
    # do not want to go out of bounds
    for i in range(len(c_list)-sides):
        # if  i == 0, 8, 16, etc. (first point in circle)
        if i%sides == 0:
            f_list.append((i, i+sides, i+sides+sides-1, i+sides-1))
        else:
            f_list.append((i, i+sides, i+sides-1, i-1))
    # start face
    start_cap = []
    end_cap = []
    for i in range(sides):
        # goes from 0->sides-1
        # vertex 0 is 0 degrees, sides/4 = 90 degrees, etc (goes counter clockwise)
        start_cap.append((sides-1)-i)
        end_cap.append(len(c_list)-(sides)+i)
    f_list.append(start_cap)
    f_list.append(end_cap)

    # creating mesh and object
    scn = bpy.context.collection
    w_mesh = bpy.data.meshes.new(w_name)
    w_ob = bpy.data.objects.new(w_name, w_mesh)
    scn.objects.link(w_ob)
    # making all points and drawing line between them
    w_mesh.from_pydata(c_list, [], f_list)
    # making smooth
    if shade_smooth:
        for poly in w_mesh.polygons:
            poly.use_smooth = True
    w_mesh.update()
    return w_ob

# draw parabola or catenary wire with thickness
def parabolic_wire_3d(w_name, droop, w_segment, radius, start_x, start_y, start_z, end_x, end_y, end_z, catenary_enabled, sides, shade_smooth):
    # amount to add to angle for each side
    angle_increment = (2*math.pi)/sides
    
    # get distance bewteen poles
    pole_dist = math.sqrt((end_x-start_x)**2 + (end_y-start_y)**2 + (end_z-start_z)**2)
    # current segment (x value)
    p_segment = pole_dist/w_segment

    # list of wire path (parabola)
    path_list = [(start_x, start_y, start_z)]
    # list of coordinates (circles following parabola)
    c_list = []
    x = -(pole_dist/2)
    # create list of coordinates for parabola
    for i in range(1, w_segment):
        # get x, y, z coordinates
        path_z = get_wire_z(x, p_segment, pole_dist, droop, catenary_enabled, start_z) + ((start_z+(i*((end_z-start_z)/w_segment)))-droop)
        path_x = (start_x+(i*((end_x-start_x)/w_segment)))
        path_y = (start_y+(i*((end_y-start_y)/w_segment)))
        # adding all in tuple to path_list
        path_list.append((path_x, path_y, path_z))
        x += p_segment

    # adding end point to path_list
    path_list.append((end_x, end_y, end_z))

    # make circles
    angle = 0
    for i in range(len(path_list)-1):
        # current point
        x, y, z = path_list[i]
        # next point
        x2, y2, z2 = path_list[i+1]
        # doing the same thing for all points in the circle (sides)
        for j in range(sides):
            # make directional vector between current and next point
            dir_vec = mathutils.Vector((x2-x, y2-y, 0))
            # make rotational axis vector (to rotate around later)
            rot_vec = mathutils.Vector((x2-x, y2-y, z2-z))

            # make the point on the circle
            # its a vector parallel to current wire segment with length of radius
            point = ((mathutils.Vector((x, y, z)) + (dir_vec.normalized())*radius) - mathutils.Vector((x, y, z)))
            # rotate point to be perpendicular to wire segment
            point.rotate(mathutils.Euler((0, 0, math.radians(90)), "XYZ"))
            # make 3x3 rotational matrix to rotate point around rot_vec
            rot_mat = mathutils.Matrix.Rotation(angle, 3, rot_vec)
            # rotate point by matrix
            point.rotate(rot_mat)
            # move point back to correct coordinates
            point += mathutils.Vector((x, y, z))
            # add point to list
            c_list.append((point.x, point.y, point.z))
            # increment angle
            angle += angle_increment
    
    # making circle for end point
    # current point is end_x, end_y, end_z
    # previous point
    prev_x, prev_y, prev_z = path_list[-2]
    # direction vector
    dir_vec = mathutils.Vector((end_x-prev_x, end_y-prev_y, 0))
    # rotational axis vector
    rot_vec = mathutils.Vector((end_x-prev_x, end_y-prev_y, end_z-prev_z))

    # make circle
    angle = 0
    for i in range(sides):
        point = mathutils.Vector((end_x, end_y, end_z)) + dir_vec.normalized()*radius - mathutils.Vector((end_x, end_y, end_z))
        point.rotate(mathutils.Euler((0, 0, math.radians(90)), "XYZ"))
        rot_mat = mathutils.Matrix.Rotation(angle, 3, rot_vec)
        point.rotate(rot_mat)
        point += mathutils.Vector((end_x, end_y, end_z))
        c_list.append((point.x, point.y, point.z))
        angle += angle_increment
    
    # making faces
    f_list = []
    # do not want to go out of bounds
    for i in range(len(c_list)-sides):
        # if  i == 0, 8, 16, etc. (first point in circle)
        if i%sides == 0:
            f_list.append((i, i+sides, i+sides+sides-1, i+sides-1))
        else:
            f_list.append((i, i+sides, i+sides-1, i-1))
    # start and end faces
    start_cap = []
    end_cap = []
    for i in range(sides):
        # goes from 0->sides-1
        # vertex 0 is 0 degrees, sides/4 = 90 degrees, etc (goes counter clockwise)
        start_cap.append((sides-1)-i)
        end_cap.append(len(c_list)-(sides)+i)
    f_list.append(start_cap)
    f_list.append(end_cap)

    # making mesh
    scn = bpy.context.collection
    w_mesh = bpy.data.meshes.new(w_name)
    w_obj = bpy.data.objects.new(w_name, w_mesh)
    scn.objects.link(w_obj)
    # making all points and lines
    w_mesh.from_pydata(c_list, [], f_list)
    # making smooth
    if shade_smooth:
        for poly in w_mesh.polygons:
            poly.use_smooth = True
    w_mesh.update()
    # return created object
    return w_obj

# makes desired amount of balls on wire at locations following parabolic wire
def make_balls(amount, droop, radius, sides, start_x, start_y, start_z, end_x, end_y, end_z):
    # getting distance between poles
    pole_dist = math.sqrt((end_x-start_x)**2 + (end_y-start_y)**2 + (end_z-start_z)**2)
    a = droop/((pole_dist**2)/4)
    # total amount of "segments" in wire
    p_segment = pole_dist/(amount+1)
    x = (-(pole_dist/2))
    balls_list = []
    for i in range(1, amount+1):
        # coordinates to draw ball
        balls_x = (i)*(end_x-start_x)/(amount+1) + start_x
        balls_y = (i)*(end_y-start_y)/(amount+1) + start_y
        balls_z = a*((x+p_segment))**2 + ((i)*(end_z-start_z)/(amount+1) + start_z-droop)
        x += p_segment
        # make ball object
        balls_list.append(draw_ball(radius, sides, balls_x, balls_y, balls_z))
    return balls_list

# chooses what wire to draw depending on settings
def choose_wire(w_name, start_x, start_y, start_z, end_x, end_y, end_z):
    # list to return (will have wire and ball objects)
    return_list = []
    # get config
    wire_config = bpy.context.scene.wire_config
    droop = wire_config.droop
    w_segment = wire_config.segments
    catenary_enabled = wire_config.catenary_wire
    thickness_enabled = wire_config.thick_wire
    radius = wire_config.wire_thickness
    # config for wire balls
    balls_enabled = wire_config.wire_balls_enabled
    balls_radius = wire_config.wire_ball_radius
    balls_sides = wire_config.wire_ball_sides
    balls_amount = wire_config.wire_ball_amount
    #update_mode = wire_config.update_mode
    wire_sides = wire_config.wire_sides
    shade_wire_smooth = wire_config.shade_wire_smooth
    
    # wires
    if (droop == 0) or (w_segment == 1):
        # set droop to be 0 so that the balls will be in the right spot
        droop = 0
        # if thick wire but no droop or segments draw normal 3d wire
        if thickness_enabled:
            return_list.append(draw_wire_3d(w_name, radius, start_x, start_y, start_z, end_x, end_y, end_z, wire_sides, shade_wire_smooth))
        # or just draw normal wire if no thick wire
        else:
            return_list.append(draw_wire(w_name, start_x, start_y, start_z, end_x, end_y, end_z))
    # if thick wire is enabled
    elif thickness_enabled:
        return_list.append(parabolic_wire_3d(w_name, droop, w_segment, radius, start_x, start_y, start_z, end_x, end_y, end_z, catenary_enabled, wire_sides, shade_wire_smooth))
    # if none of the above draw parabolic or catenary wire (parabolic by default)
    else:
        return_list.append(draw_parabolic(w_name, droop, w_segment, start_x, start_y, start_z, end_x, end_y, end_z, catenary_enabled))
    # wire balls
    if balls_enabled:
        return_list.append((make_balls(balls_amount, droop, balls_radius, balls_sides, start_x, start_y, start_z, end_x, end_y, end_z)))
    return return_list

# gets objects returned from making wires and balls (lists)
def get_returned_objects(wire_name, start_x, start_y, start_z, end_x, end_y, end_z, wire_list, balls_list):
    # get active pole (only needed if balls where made to change selection back to poles)
    active_pole = bpy.context.active_object

    # returned list with wires and (possibly) balls
    returned_list = choose_wire(wire_name, start_x, start_y, start_z, end_x, end_y, end_z)
    # add wires to wire_list
    wire_list.append(returned_list[0])
    # if wire balls were created
    if len(returned_list) > 1:
        # add wire balls to balls_list
        balls_list += returned_list[1]
        # deselect balls
        bpy.context.active_object.select_set(state=False)
        # set active pole back to what it was before
        bpy.context.view_layer.objects.active = active_pole
        active_pole.select_set(state=True)
    
    # return lists (if balls not created, balls_list is empty)
    return wire_list, balls_list

# gets selected objects and draws wires using above functions
class WireMain(bpy.types.Operator):
    bl_idname = "wire_ops.draw_parabolic"
    bl_label = "Wire Drawing"
    bl_description = "Draws wire"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"REGISTER"}

    # draw wires first time
    def execute(self, context):
        #context = bpy.context.scene
        selected_poles = get_selected_poles()
        #print(selected_poles) #<-- debug
        # go through selected poles and set downstream (entering wire) and upstream (exiting wire) for poles
        for pole_idx in range(len(selected_poles)-1):
            selected_poles[pole_idx]["upstream"] = selected_poles[pole_idx+1]
            selected_poles[pole_idx+1]["downstream"] = selected_poles[pole_idx]

        # what is start pole and what is end pole
        for obj in selected_poles:
            #print(f'{obj.name} upstream: {obj.get("upstream", None)} downstream: {obj.get("downstream", None)}')
            start_pole = obj.name
            end_obj = (obj.get("upstream", None))
            if end_obj:
                end_pole = end_obj.name
            else:
                # no upstream pole, so this is the last pole
                print(f"no upstream pole for {obj.name}")
                break
            # delete existing wires
            remove_existing_wires(obj, end_obj)

            wire_list = []
            balls_list = []
            # get start and end coordinates for each mushroom in the pole
            for mushroom_index, mushroom in enumerate(get_mushroom(start_pole)["output"]):
                start_x, start_y, start_z = get_coordinates(obj, mushroom)
                end_x, end_y, end_z = get_coordinates(end_obj, get_mushroom(end_pole)["input"][mushroom_index])
                # name of wire is the name of the poles it connects
                wire_name = f"{start_pole}-{end_pole}"
                # get wires and (potentially) balls (balls_list empty if no balls)
                # wires and balls are added to blender objects as custom properties to know what to delete when redrawing
                wire_list, balls_list = get_returned_objects(wire_name, start_x, start_y, start_z, end_x, end_y, end_z, wire_list, balls_list)
            # add wire_list to start and end poles
            obj["output_wire"] = wire_list
            end_obj["input_wire"] = wire_list
            # add wire balls to start and end poles if enabled
            obj["output_wire_balls"] = balls_list
            end_obj["input_wire_balls"] = balls_list

        return {"FINISHED"}

# removes wire properties from selected poles
class RemoveWireProps(bpy.types.Operator):
    bl_idname = "wire_ops.remove_wire_props"
    bl_label = "Remove Wire Properties"
    bl_description = "Removes wires and wire properties of selected poles"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"REGISTER"}

    def execute(self, context):
        context = bpy.context.scene
        selected_poles = [obj for obj in bpy.context.selected_objects]
        for pole in selected_poles:
            # remove upstream property
            if pole.get("upstream", None) is not None:
                del pole["upstream"]
            # remove downstream property
            if pole.get("downstream", None) is not None:
                del pole["downstream"]
            # delete input and output wire objects and properties
            remove_existing_wires(pole, pole)
        print("removed upstream and downstream properties")
        return {"FINISHED"}

# manually update wire
class ManualUpdateWire(bpy.types.Operator):
    bl_idname = "wire_ops.manual_update_wire"
    bl_label = "Update Wire"
    bl_description = "Manually updates wires"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"REGISTER"}

    def execute(self, context):
        update_wire()
        update_wire_between_verts()
        return {"FINISHED"}

# function updates normal wires (delete old wires and drawn new at new location)
def update_wire():
    #print('update wire') #<-- debug
    # get selected poles
    selected_poles = get_selected_poles()
    using_poles = []
    for obj in selected_poles:
        # upstream wires
        start_obj = obj
        end_obj = (obj.get("upstream", None))
        using_poles.append((start_obj, end_obj))
        # downstream wires
        start_obj = (obj.get("downstream", None))
        end_obj = obj
        using_poles.append((start_obj, end_obj))
    for start_obj, end_obj in using_poles:
        wire_list = []
        balls_list = []
        # make sure start and end poles exist
        # also need to make sure get_mushroom does not return None for both objects otherwise wire will not update and throw exception
        if (end_obj and start_obj and (get_mushroom(start_obj.name) and get_mushroom(end_obj.name))) is not None:
            # delete old wires
            remove_existing_wires(start_obj, end_obj)
            # draw new wires
            for mushroom_index, mushroom in enumerate(get_mushroom(start_obj.name)["output"]):
                start_x, start_y, start_z = get_coordinates(start_obj, mushroom)
                end_x, end_y, end_z = get_coordinates(end_obj, get_mushroom(end_obj.name)["input"][mushroom_index])
                # update wire
                wire_name = f"{start_obj.name}-{end_obj.name}"
                # get wires and (potentially) balls (balls_list empty if no balls)
                wire_list, balls_list = get_returned_objects(wire_name, start_x, start_y, start_z, end_x, end_y, end_z, wire_list, balls_list)
            end_obj["input_wire"] = wire_list
            start_obj["output_wire"] = wire_list
            # add wire balls to start and end poles if enabled
            start_obj["output_wire_balls"] = balls_list
            end_obj["input_wire_balls"] = balls_list
        else:
            #print('end_obj is None') #<-- debug
            pass

# draw wire between two vertices selected in edit mode
class WireBetweenVertices(bpy.types.Operator):
    bl_idname = "wire_ops.wire_between_vertices"
    bl_label = "Draw wire between two vertices"
    bl_description = "Draws wire between two selected vertices"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"REGISTER"}

    # coordinates vertex at start and end points of wire will be saved to draw
    # wire when object moves, but as these are coordinates of vertex, if vertex
    # moves separately from object, wire will not be drawn at new location

    def execute(self, context):
        # get selected vertices
        selected_verts = []
        if bpy.context.selected_objects != []:
            for obj in bpy.context.selected_objects:
                if obj.mode != "OBJECT":
                    obj_mode = obj.mode
                    bpy.ops.object.mode_set(mode="OBJECT")
                    for v in obj.data.vertices:
                        if v.select:
                            #selected_verts.append((obj.matrix_world @ mathutils.Vector((v.co.x, v.co.y, v.co.z)), obj))
                            selected_verts.append((mathutils.Vector((v.co.x, v.co.y, v.co.z)), obj))
                    bpy.ops.object.mode_set(mode=obj_mode)
                else:
                    print("one or more objects not in edit mode")
                    return {"CANCELLED"}
        else:
            print("no vertices found/selected")
            return {"CANCELLED"}
        
        for obj_idx in range(len(selected_verts)-1):
            # set upstream and downstream objects
            selected_verts[obj_idx][1]["upstream"] = selected_verts[obj_idx+1][1]
            selected_verts[obj_idx+1][1]["downstream"] = selected_verts[obj_idx][1]

        # make wire
        wire_list = []
        balls_list = []
        for obj in selected_verts:
            # find next object in list
            try:
                next_obj = selected_verts[selected_verts.index(obj)+1]
            except IndexError:
                print("no next object")
                break
            # get coordinates
            #start_x, start_y, start_z = obj[0]
            start_vec = obj[0]
            start_obj = obj[1]
            start_x, start_y, start_z = (start_obj.matrix_world @ start_vec).to_tuple()
            #end_x, end_y, end_z = next_obj[0]
            end_vec = next_obj[0]
            end_obj = next_obj[1]
            end_x, end_y, end_z = (end_obj.matrix_world @ end_vec).to_tuple()
            #print(f'{start_obj.name} to {end_obj.name}') #<-- debug
            wire_name = f"{start_obj.name}-{end_obj.name}"
            # draw wire
            # get wires and (potentially) balls (balls_list empty if no balls)
            wire_list, balls_list = get_returned_objects(wire_name, start_x, start_y, start_z, end_x, end_y, end_z, wire_list, balls_list)
    
        # add wires to objets
        start_obj["output_wire"] = wire_list
        end_obj["input_wire"] = wire_list
        # add vector
        start_obj["start_vector"] = start_vec
        end_obj["end_vector"] = end_vec
        # balls
        start_obj["output_wire_balls"] = balls_list
        end_obj["input_wire_balls"] = balls_list
        return {"FINISHED"}

def update_wire_between_verts():
    # getting selected objects
    selected_objects = []
    if bpy.context.selected_objects != []:
        for obj in bpy.context.selected_objects:
            # upstream
            start_obj = obj
            start_vec = start_obj.get("start_vector", None)
            end_obj = (obj.get("upstream", None))
            selected_objects.append((start_obj, end_obj))
            # downstream
            start_obj = (obj.get("downstream", None))
            end_obj = obj
            end_vec = end_obj.get("end_vector", None)
            selected_objects.append((start_obj, end_obj))
    else:
        print("no objects selected")
    
    for start_obj, end_obj in selected_objects:
        wire_list = []
        balls_list = []
        if (end_obj and start_obj) is not None:
            start_property_arr = start_obj.get("start_vector", None)
            if start_property_arr is None:
                break
            start_vec = mathutils.Vector((start_property_arr[0], start_property_arr[1], start_property_arr[2]))
            end_property_arr = end_obj.get("end_vector", None)
            end_vec = mathutils.Vector((end_property_arr[0], end_property_arr[1], end_property_arr[2]))
            #print(start_vec, end_vec) #<-- debug
            # delete old wires
            remove_existing_wires(start_obj, end_obj)
            # draw new wires from start_vec to end_vec
            start_x, start_y, start_z = (start_obj.matrix_world @ start_vec).to_tuple()
            end_x, end_y, end_z = (end_obj.matrix_world @ end_vec).to_tuple()
            # update wire
            wire_name = f"{start_obj.name}-{end_obj.name}"
            # get wires and (potentially) balls (balls_list empty if no balls)
            wire_list, balls_list = get_returned_objects(wire_name, start_x, start_y, start_z, end_x, end_y, end_z, wire_list, balls_list)
            # update properties
            end_obj["input_wire"] = wire_list
            start_obj["output_wire"] = wire_list
            # update vector
            start_obj["start_vector"] = start_vec
            end_obj["end_vector"] = end_vec
            # update balls
            start_obj["output_wire_balls"] = balls_list
            end_obj["input_wire_balls"] = balls_list
        else:
            pass