import bpy
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
        # importing user settings and options
        config = context.scene.config
        # tolerence for distance in kd tree
        dist_tol = config.kd_tol
        # droop of wire, assuming positive z-up
        # set to 0 to disable; 1 works well with 30-m spacing beteen poles
        droop = config.droop
        # amount of segments that construct parabola
        w_segment = config.segments
        # check if coordinates of mushrooms exist in model
        # disable if recieving "IndexError: list index out of range" error
        check_coordinates = config.check_wire
        # auto droop wire
        # calculates 'ideal' droop based on distance wire travels
        auto_droop_enabled = config.auto_droop
        # auto segments wire
        # calculates 'ideal' segments based on distance wire travels
        auto_segments_enabled = config.auto_segments
        # old parabolic wire
        # does not look good but more reliable
        eight_part_wire_enabled = config.eight_part_wire
        # catenary wire
        # little difference from parabolic wire
        catenary_wire_enabled = config.catenary_wire
        # balls used for visibility of wire, usually seen in areas with low flying aircraft
        # balls enabled
        balls_enabled = config.wire_balls
        # balls amount
        # 3 are usually seen; 0 will disable even if balls_enabled is true
        balls_amount = config.wire_balls_amount
        # balls radius
        balls_radius = config.wire_balls_radius
        # balls sides
        balls_sides = config.wire_balls_sides
        
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
            # gets name of object without periods
            pole_name = pole_name.split('.')[0]
            # dictionary with all mushroom coordinates
            # key needs to be name of the object
            # list with tuple coordinates, order is Left, Right, Middle, XYZ order
            pole_dict = {
                'pole_a': [(-0.375, 1.8, 5.2441), (-0.375, -1.8, 5.2441), (-0.375, -0.55, 5.2441)],
            }
            
            # if object name matches any known poles, use those coordinates
            if pole_name in pole_dict:
                return pole_dict[pole_name]
            # if object name does not match any known poles, return cancelled
            else:
                print('pole not found')
                return {'CANCELLED'}

        # gets coordinates of object
        # inputs: object, kd tree, "mushroom" tuple, kd tolerence
        def find_coord(obj, kd, mushroom, dist_tol):
            if check_coordinates:
                coord_tree = kd.find_range(mushroom, dist_tol)
                # getting vector from matrix
                #print(coord_tree[0][0]) #<-- debug
                coord_vec = coord_tree[0][0]
            else:
                coord_vec = mathutils.Vector(mushroom)
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

        # draws straight wire (no droop/parabola)
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

        # automatic droop for wire
        # inputs: start coordinates, end coordinates
        def auto_droop(start_x, start_y, start_z, end_x, end_y, end_z):
            # getting distance between start and end coordinates
            dist = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2 + (end_z - start_z)**2)
            # set droop
            droop = (dist/30)*1
            return droop

        # sees if segments need to be increased
        # inputs: start coordintes, end coordinates
        def auto_segments(start_x, start_y, start_z, end_x, end_y, end_z):
            # segments are 16 unless it needs to be increased
            w_segment = 16
            # get distance between start and end points
            dist = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2 + (end_z - start_z)**2)
            # get distance including droop
            drooped_dist = (math.sqrt((dist/2)**2 + droop**2))*2
            # distance above which increase segments
            drooped_dist_threshold = 92
            # amount by which segments are increased
            segment_increase = 4
            #print('dist:',drooped_dist) #<-- debug
            # if distance is above threshold, increase segments
            if drooped_dist >= drooped_dist_threshold:
                w_segment = 16 + (int(drooped_dist/drooped_dist_threshold)*segment_increase)
            return w_segment
            
        # draws balls (the balls that can be seen on wires near areas with low-flying aircraft)
        # inputs: start coordinates, end coordinates, function constant a, ball radius, ball sides
        def balls(start_x, start_y, start_z, end_x, end_y, end_z, a, radius, sides):
            # getting coordinates for ball
            # currently they follow parabola only
            for i in range(1, balls_amount+1):
                dist = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2 + (end_z - start_z)**2)
                x = (-(dist/2)) + (i*(dist/balls_amount))
                # coordinates where to draw ball
                balls_x = (i)*(end_x-start_x)/(balls_amount+1) + start_x
                balls_y = (i)*(end_y-start_y)/(balls_amount+1) + start_y
                balls_z = a*(x-((dist/balls_amount)/2))**2 + ((i)*(end_z-start_z)/(balls_amount+1) + start_z-droop)
                # create sphere for ball
                bpy.ops.mesh.primitive_uv_sphere_add(segments=sides, ring_count=sides, radius=radius, location=(balls_x, balls_y, balls_z))

        # corrects 'a' costant in catenary equation
        # inputs: start z, a, x
        def tune_cat_a(start_z, a, x):
            tune_tol = 0.5
            cat_eq = a*(math.cosh((x)/a)) + (start_z-a-droop)
            # check if current a will result in start_z when x is put into catenary equation
            while not (cat_eq <= (start_z + tune_tol) and cat_eq >= (start_z - tune_tol)):
                if cat_eq >= (start_z + tune_tol):
                    a += 0.1
                elif cat_eq <= (start_z - tune_tol):
                    a -= 0.1

                cat_eq = a*(math.cosh((x)/a)) + (start_z-a-droop)
            return a

        # draws wire using quadratic function to get more natural shape
        # inputs: wire name, start coordinates, end coordinates
        def parabolic_wire(w_name, start_x, start_y, start_z, end_x, end_y, end_z):
            # getting distance between poles
            pole_dist = abs(math.sqrt(((end_x-start_x)**2 + (end_y-start_y)**2 + (end_z-start_z)**2)))
            # constant multiplier in quadratic
            a = droop/((pole_dist**2)/4)
            p_segment = pole_dist/w_segment

            x_list = []
            y_list = []
            z_list = []
            x = -(pole_dist/2)
            for i in range(1, w_segment):
                # quadratic equation; first part (before +) is quadratic, after is z-axis manipulation
                wire_z = a*((x+p_segment)**2) + ((start_z+(i*((end_z-start_z)/w_segment)))-droop)
                x_list.append((start_x+(i*((end_x-start_x)/w_segment))))
                y_list.append((start_y+(i*((end_y-start_y)/w_segment))))
                z_list.append(wire_z)
                x += p_segment

            # adding coordinates to tuple for points
            co_list = [(start_x, start_y, start_z), (end_x, end_y, end_z)]
            ln_list = [(0, 1)]
            for i in range (1, (w_segment)):
                co_list.insert(i, (x_list[i-1], y_list[i-1], z_list[i-1]))
                ln_list.append((i, (i+1)))

            scn = bpy.context.collection
            w_mesh = bpy.data.meshes.new(w_name)
            w_ob = bpy.data.objects.new(w_name, w_mesh)
            scn.objects.link(w_ob)
            # making all points and drawing line between them
            w_mesh.from_pydata(co_list, ln_list, [])
            w_mesh.update()
            # setting created wire as active
            bpy.context.view_layer.objects.active = w_ob

            # draws balls if enabled and amount is more than 0
            if (balls_enabled) and (balls_amount > 0):
                balls(start_x, start_y, start_z, end_x, end_y, end_z, a, balls_radius, balls_sides)

        # draws wire using catenary equation to get more natural shape (https://en.wikipedia.org/wiki/Catenary)
        # looks pretty much the same as parabolic wire; exessive droop may cause undesired results
        # inputs: wire name, start coordinates, end coordinates
        def catenary_wire(w_name, start_x, start_y, start_z, end_x, end_y, end_z):
            # getting distance between poles
            pole_dist = abs(math.sqrt(((end_x-start_x)**2 + (end_y-start_y)**2 + (end_z-start_z)**2)))
            # constant multiplier in catenary
            a = (pole_dist**2)/(8*droop)
            p_segment = pole_dist/w_segment

            x_list = []
            y_list = []
            z_list = []
            x = -(pole_dist/2)
            a = tune_cat_a(start_z, a, x)
            for i in range(1, w_segment):
                # catenary equation; first part (before +) is catenary, after is z-axis manipulation
                # subtracting a at the end because (0, a) is the lowest point of the catenary
                wire_z = a*(math.cosh((x+p_segment)/a)) + ((start_z+(i*((end_z-start_z)/w_segment)))-a-droop)
                x_list.append((start_x+(i*((end_x-start_x)/w_segment))))
                y_list.append((start_y+(i*((end_y-start_y)/w_segment))))
                z_list.append(wire_z)
                x += p_segment

            # adding coordinates into tuple for points
            co_list = [(start_x, start_y, start_z), (end_x, end_y, end_z)]
            ln_list = [(0, 1)]
            for i in range(1, (w_segment)):
                co_list.insert(i, (x_list[i-1], y_list[i-1], z_list[i-1]))
                ln_list.append((i, (i+1)))

            scn = bpy.context.collection
            w_mesh = bpy.data.meshes.new(w_name)
            w_ob = bpy.data.objects.new(w_name, w_mesh)
            scn.objects.link(w_ob)
            # making all points and drawing line between them
            w_mesh.from_pydata(co_list, ln_list, [])
            w_mesh.update()
            # setting created wire to active
            bpy.context.view_layer.objects.active = w_ob

        # draws 8-part parabolish wire
        # not recommended for use, parabolic and catenary look beter
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

        # loops through selected objects and creates wires
        for obj in selected_list:
            # gets name of object
            start_pole = obj.name

            # gets next object to draw wires to
            next_obj = int(selected_list.index(obj)) + 1
            if next_obj <= (int(len(selected_list))-1):
                end_obj = (selected_list[next_obj])
                # name of next object
                end_pole = end_obj.name
            else:
                # if it is last object do nothing
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
            #      creating ending KD tree      #
            #####################################
            end_mesh = end_obj.data
            end_size = len(end_mesh.vertices)
            end_kd = mathutils.kdtree.KDTree(end_size)

            for i, v in enumerate(end_mesh.vertices):
                end_kd.insert(v.co, i)
            end_kd.balance()
            #####################################
            #             draw wire             #
            #####################################
            for mushroom in get_mushroom(start_pole):
                #print(mushroom, obj, kd) #<-- debug
                # get coordinates of start mushroom
                start_x = find_coord(obj, kd, mushroom, dist_tol)[0]
                start_y = find_coord(obj, kd, mushroom, dist_tol)[1]
                start_z = find_coord(obj, kd, mushroom, dist_tol)[2]
                # it is assumed that two poles have same number of mushrooms. you cant have 2 mushrooms feed into 1
                try:
                    end_index = get_mushroom(start_pole).index(mushroom)
                    end_x = find_coord(end_obj, end_kd, get_mushroom(end_pole)[end_index], dist_tol)[0]
                    end_y = find_coord(end_obj, end_kd, get_mushroom(end_pole)[end_index], dist_tol)[1]
                    end_z = find_coord(end_obj, end_kd, get_mushroom(end_pole)[end_index], dist_tol)[2]
                except:
                    print('Unequal amount of mushrooms')
                    return {'CANCELLED'}
                
                if auto_droop_enabled and (droop != 0) and (not eight_part_wire_enabled):
                    droop = auto_droop(start_x, start_y, start_z, end_x, end_y, end_z)
                    #print(droop) #<-- debug
                if auto_segments_enabled and (droop != 0) and (not eight_part_wire_enabled):
                    w_segment = auto_segments(start_x, start_y, start_z, end_x, end_y, end_z)
                    #print(w_segment) #<-- debug
                # checks that next pole has different location
                if (start_x != end_x) or (start_y != end_y) or (start_z != end_z):
                    # draw straight wire
                    if droop == 0 or w_segment <= 2:
                        draw_wire('wire', start_x, start_y, start_z, end_x, end_y, end_z)
                    # draws eight part wire
                    elif (eight_part_wire_enabled == True):
                        eight_part_wire('8_wire', start_x, start_y, start_z, end_x, end_y, end_z)
                    elif (catenary_wire_enabled == True):
                        catenary_wire('catenary_wire', start_x, start_y, start_z, end_x, end_y, end_z)
                    # draws parabola wire
                    else:
                        parabolic_wire('p_wire', start_x, start_y, start_z, end_x, end_y, end_z)
            print('finished')
        return {'FINISHED'}
