import bpy
import bmesh
import mathutils
from mathutils import Vector
import math
from __main__ import *

# [9B6M0M6K7Y,

class WireMain(bpy.types.Operator):
    bl_idname = 'wire_ops.draw_parabolic'
    bl_label = 'Wire Drawing'
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        config = context.scene.config
        
        # tolerence for distance in kd tree
        dist_tol = config.kd_tol
        # droop of wire, assuming positive z-up
        # set to 0 to disable; 1 works well with 30-m spacing beteen poles
        droop = config.droop
        # amount of segments that construct parabola
        w_segment = config.segments
        # old parabolic wire
        # does not look as good but more reliable
        eight_part_wire_enabled = config.eight_part_wire
        
        # list of all selected objects
        selected_list = []

        # gets all objects that are selected and adds them to selected_list
        if bpy.context.selected_objects != []:
            for obj in bpy.context.selected_objects:
                selected_list.append(obj)
                
        else:
            print('no pole found/selected')
            return {'CANCELLED'}
        
        # gets coordinates of the "mushrooms"
        # inputs: obj; variable from selected_list
        def get_mushroom(pole_name):
            # list of returned mushrooms
            mushroom_list = []
            # gets name of object without periods
            pole_name = pole_name.split('.')[0]
            # list with tuple coordinates, order is Left, Right, Middle (Ground)
            pole_a = [(-0.375, 1.8, 5.2441), (-0.375, -1.8, 5.2441), (-0.375, -0.55, 5.2441)]
            # if object name matches any known poles, use those coordinates
            if pole_name == 'pole_a':
                mushroom_list = pole_a
            return mushroom_list

        # gets coordinates of object
        # inputs: object, kd tree, "mushroom" type, kd tolerence
        def find_coord(obj, kd, mushroom, dist_tol):
            coord_tree = kd.find_range(mushroom, dist_tol)
            # getting vector from matrix
            #print(coord_tree[0][0]) #<-- debug
            coord_vec = coord_tree[0][0]
            # getting rotation of starting object in euler
            coord_rot = ((obj.matrix_world).to_euler())
            # rotating vector
            coord_vec.rotate(coord_rot)
            # splitting rotated vector into x, y, z parts
            loc_x = coord_vec[0]
            loc_y = coord_vec[1]
            loc_z = coord_vec[2]
            # adding world translation to coordintes
            loc_x += obj.matrix_world[0][3]
            loc_y += obj.matrix_world[1][3]
            loc_z += obj.matrix_world[2][3]
            loc_xyz = [loc_x, loc_y, loc_z]
            return loc_xyz

        # draws straight wire (no sag/droop/parabola)
        # inputs: wire name, start coordintes, end coordinates
        def draw_wire(w_name, start_x, start_y, start_z, end_x, end_y, end_z):
            scn = bpy.context.collection
            w_mesh = bpy.data.meshes.new(w_name)
            w_ob = bpy.data.objects.new(w_name, w_mesh)
            scn.objects.link(w_ob)
            # making two points, then drawing line between them
            w_mesh.from_pydata([(start_x, start_y, start_z), (end_x, end_y, end_z)],[(0, 1)],[])
            w_mesh.update()
            bpy.context.view_layer.objects.active = w_ob
            # updating mesh
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.mode_set(mode='OBJECT')

        # draws wire using quadratic function to get more natural shape
        # inputs: wire name, start coordinates, end coordinates
        def parabolic_wire(w_name, start_x, start_y, start_z, end_x, end_y, end_z):
            # getting droop midpoint
            mid_x = (start_x+end_x)/2
            mid_y = (start_y+end_y)/2
            # getting distance between poles
            x_dist = (end_x - start_x)**2
            y_dist = (end_y - start_y)**2
            z_dist = (end_z - start_z)**2
            pole_dist = abs(math.sqrt((x_dist+y_dist+z_dist)))
            mid_xy = abs(math.sqrt(((mid_x)**2)+((mid_y)**2)))
            start_xy = math.sqrt(((start_x)**2)+((start_y)**2))
            # constant multiplier in quadratic
            a = droop/(pole_dist*(pole_dist/4))
            p_iterator = pole_dist/w_segment

            x_list = []
            y_list = []
            z_list = []
            p_dist = start_xy
            for i in range(1, w_segment):
                # quadratic equation; first part (before +) is quadratic, after is z-axis manipulation
                wire_z = a*((p_dist - mid_xy + p_iterator)**2) + ((start_z+(i*((end_z-start_z)/w_segment)))-droop)
                x_list.append((start_x+(i*((end_x-start_x)/w_segment))))
                y_list.append((start_y+(i*((end_y-start_y)/w_segment))))
                z_list.append(wire_z)
                p_dist += p_iterator

            co_list = [(start_x, start_y, start_z), (end_x, end_y, end_z)]
            ln_list = [(0, 1)]
            for i in range (1, (w_segment-1)):
                co_list.insert(i, (x_list[i-1], y_list[i-1], z_list[i-1]))
                ln_list.append((i, (i+1)))

            scn = bpy.context.collection
            w_mesh = bpy.data.meshes.new(w_name)
            w_ob = bpy.data.objects.new(w_name, w_mesh)
            scn.objects.link(w_ob)
            # making all points and drawing line between them
            w_mesh.from_pydata(co_list, ln_list, [])
            w_mesh.update()
            # selecting created wire object
            bpy.context.view_layer.objects.active = w_ob

        # draws 8-part parabolish wire
        # inputs: wire name, start coordinates, end coordinates
        def eight_part_wire(w_name, start_x, start_y, start_z, end_x, end_y, end_z):
            # between start and end
            mid_x = (start_x+end_x)/2
            mid_y = (start_y+end_y)/2
            mid_z = (start_z+end_z)/2
            # between start and middle
            quarter_1_x = (start_x+mid_x)/2
            quarter_1_y = (start_y+mid_y)/2
            quarter_1_z = (start_z+mid_z)/2
            # between middle and end
            quarter_2_x = (end_x+mid_x)/2
            quarter_2_y = (end_y+mid_y)/2
            quarter_2_z = (end_z+mid_z)/2
            # between start and quarter 1
            eight_1_x = (start_x+quarter_1_x)/2
            eight_1_y = (start_y+quarter_1_y)/2
            eight_1_z = (start_z+quarter_1_z)/2
            # between quarter 1 and middle
            eight_2_x = (mid_x+quarter_1_x)/2
            eight_2_y = (mid_y+quarter_1_y)/2
            eight_2_z = (mid_z+quarter_1_z)/2
            # between middle and quarter 2
            eight_3_x = (mid_x+quarter_2_x)/2
            eight_3_y = (mid_y+quarter_2_y)/2
            eight_3_z = (mid_z+quarter_2_z)/2
            # between end and quarter 2
            eight_4_x = (end_x+quarter_2_x)/2
            eight_4_y = (end_y+quarter_2_y)/2
            eight_4_z = (end_z+quarter_2_z)/2

            eight_droop = droop*(1/2)
            quart_droop = droop*(3/4)
            half_droop = droop*(7/8)

            # subtracting droop from z coordinates
            mid_z -= droop
            eight_3_z -= half_droop
            eight_2_z -= half_droop
            quarter_1_z -= quart_droop
            quarter_2_z -= quart_droop
            eight_1_z -= eight_droop
            eight_4_z -= eight_droop

            scn = bpy.context.collection
            w_mesh = bpy.data.meshes.new(w_name)
            w_ob = bpy.data.objects.new(w_name, w_mesh)
            scn.objects.link(w_ob)
            # making all points and drawing line between them
            w_mesh.from_pydata([
                                (start_x, start_y, start_z),                # 0
                                (eight_1_x, eight_1_y, eight_1_z),          # 1
                                (quarter_1_x, quarter_1_y, quarter_1_z),    # 2
                                (eight_2_x, eight_2_y, eight_2_z),          # 3
                                (mid_x, mid_y, mid_z),                      # 4
                                (eight_3_x, eight_3_y, eight_3_z),          # 5
                                (quarter_2_x, quarter_2_y, quarter_2_z),    # 6
                                (eight_4_x, eight_4_y, eight_4_z),          # 7
                                (end_x, end_y, end_z)                       # 8
                               ],
                               [
                                (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8)
                               ],[])
            w_mesh.update()
            bpy.context.view_layer.objects.active = w_ob
            # updating mesh
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.mode_set(mode='OBJECT')

        for obj in selected_list:
            # gets name of object
            start_pole = obj.name
            # gets mushroom coordinates for start object
            mushroom_L = get_mushroom(start_pole)[0]
            mushroom_R = get_mushroom(start_pole)[1]
            mushroom_G = get_mushroom(start_pole)[2]

            # gets next object to draw wires to
            next_obj = int(selected_list.index(obj)) + 1
            if next_obj <= (int(len(selected_list))-1):
                end_obj = (selected_list[next_obj])
                # name of next object
                end_pole = end_obj.name
                # gets mushroom coordinates for end object
                end_mushroom_L = get_mushroom(end_pole)[0]
                end_mushroom_R = get_mushroom(end_pole)[1]
                end_mushroom_G = get_mushroom(end_pole)[2]
            else:
                # if it is last object
                print('reached end/only one pole selected')
                return {'PASS_THROUGH'}
            #####################################
            #     creating starting KD tree     #
            #####################################
            mesh = obj.data
            size = len(mesh.vertices)
            kd = mathutils.kdtree.KDTree(size)

            for i, v in enumerate(mesh.vertices):
                kd.insert(v.co, i)
            kd.balance()
            #####################################
            #     finding start coordinates     #
            #####################################
            start_G_x = find_coord(obj, kd, mushroom_G, dist_tol)[0]
            start_G_y = find_coord(obj, kd, mushroom_G, dist_tol)[1]
            start_G_z = find_coord(obj, kd, mushroom_G, dist_tol)[2]

            start_L_x = find_coord(obj, kd, mushroom_L, dist_tol)[0]
            start_L_y = find_coord(obj, kd, mushroom_L, dist_tol)[1]
            start_L_z = find_coord(obj, kd, mushroom_L, dist_tol)[2]

            start_R_x = find_coord(obj, kd, mushroom_R, dist_tol)[0]
            start_R_y = find_coord(obj, kd, mushroom_R, dist_tol)[1]
            start_R_z = find_coord(obj, kd, mushroom_R, dist_tol)[2]
            #####################################
            #      creating ending KD tree      #
            #####################################
            end_mesh = end_obj.data
            end_size = len(end_mesh.vertices)
            end_kd = mathutils.kdtree.KDTree(end_size)

            for i, v in enumerate(end_mesh.vertices):
                end_kd.insert(v.co, i)
            end_kd.balance()
            #####################################
            #      finding end coordinates      #
            #####################################
            end_G_x = find_coord(end_obj, end_kd, end_mushroom_G, dist_tol)[0]
            end_G_y = find_coord(end_obj, end_kd, end_mushroom_G, dist_tol)[1]
            end_G_z = find_coord(end_obj, end_kd, end_mushroom_G, dist_tol)[2]

            end_L_x = find_coord(end_obj, end_kd, end_mushroom_L, dist_tol)[0]
            end_L_y = find_coord(end_obj, end_kd, end_mushroom_L, dist_tol)[1]
            end_L_z = find_coord(end_obj, end_kd, end_mushroom_L, dist_tol)[2]

            end_R_x = find_coord(end_obj, end_kd, end_mushroom_R, dist_tol)[0]
            end_R_y = find_coord(end_obj, end_kd, end_mushroom_R, dist_tol)[1]
            end_R_z = find_coord(end_obj, end_kd, end_mushroom_R, dist_tol)[2]
            #####################################
            #             draw wire             #
            #####################################
            # checking that creating vertices will result in wire
            if (start_G_x != end_G_x) or (start_G_y != end_G_y) or (start_G_z != end_G_z):
                # if resulting in wire, create vertices and wire
                # checks that droop is not 0
                if (droop == 0 or w_segment <= 1):
                    # draws straight wire if droop == 0 or w_segment <= 1
                    draw_wire('wire_gnd', start_G_x, start_G_y, start_G_z, end_G_x, end_G_y, end_G_z)
                elif (eight_part_wire_enabled == True):
                    # draws eight-segmented wire if true
                    eight_part_wire('wire_gnd', start_G_x, start_G_y, start_G_z, end_G_x, end_G_y, end_G_z)
                else:
                    # draws parabola wire if droop != 0
                    parabolic_wire('wire_gnd', start_G_x, start_G_y, start_G_z, end_G_x, end_G_y, end_G_z)

            if (start_L_x != end_L_x) or (start_L_y != end_L_y) or (start_L_z != end_L_z):
                if (droop == 0 or w_segment <= 1):
                    draw_wire('wire_left', start_L_x, start_L_y, start_L_z, end_L_x, end_L_y, end_L_z)
                elif (eight_part_wire_enabled == True):
                    eight_part_wire('wire_left', start_L_x, start_L_y, start_L_z, end_L_x, end_L_y, end_L_z)
                else:
                    parabolic_wire('wire_left', start_L_x, start_L_y, start_L_z, end_L_x, end_L_y, end_L_z)

            if (start_R_x != end_R_x) or (start_R_y != end_R_y) or (start_R_z != end_R_z):
                if (droop == 0 or w_segment <= 1):
                    draw_wire('wire_right', start_R_x, start_R_y, start_R_z, end_R_x, end_R_y, end_R_z)
                elif (eight_part_wire_enabled == True):
                    eight_part_wire('wire_right', start_R_x, start_R_y, start_R_z, end_R_x, end_R_y, end_R_z)
                else:
                    parabolic_wire('wire_right', start_R_x, start_R_y, start_R_z, end_R_x, end_R_y, end_R_z)
            print('finished')
        return {'FINISHED'}
