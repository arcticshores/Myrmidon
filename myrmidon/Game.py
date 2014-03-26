"""
Myrmidon
Copyright (c) 2010 Fiona Burrows
 
Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:
 
The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.
 
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
 
---------------------
 
An open source, actor based framework for fast game development for Python.

This contains the primary Game object from where you manipulate
and interact with the application.
"""

import sys, os, math, copy, inspect
from myrmidon.consts import *


class Game(object):

    # Engine related
    started = False

    # Set to true at run-time and Myrmidon will not create a screen,
    # nor will it accept input or execute any entities in a loop.
    # No backend engines are initialised.
    # Any entity objects you create will not interate their generator
    # unless you run Entity._iterate_generator manually.
    test_mode = False
    
    engine_def = {
        "window" : "pygame",
        "gfx" : "opengl",
        "input" : "pygame",
        "audio" : "pygame"
        }
    engine_plugin_def = {
        "window" : [],
        "gfx" : [],
        "input" : [],
        "audio" : []
        }
    engine = {
        "window" : None,
        "gfx" : None,
        "input" : None,
        "audio" : None
        }

    current_fps = 30
    fps = 0

    # Display related
    screen_resolution = 1024,768
    lowest_resolution = 800,600
    full_screen = False

    # Entity related
    entity_list = []
    entities_to_remove = []
    remember_current_entity_executing = []
    current_entity_executing = None
    entity_priority_dirty = True
    did_collision_check = False


    @classmethod
    def define_engine(cls, window = None, gfx = None, input = None, audio = None):
        """
        Use this before creating any entities to redefine which engine backends to use.
        """
        if window:
            cls.engine_def['window'] = window
        if gfx:
            cls.engine_def['gfx'] = gfx
        if input:
            cls.engine_def['input'] = input
        if audio:
            cls.engine_def['audio'] = audio

            
    @classmethod
    def define_engine_plugins(cls, window = [], gfx = [], input = [], audio = []):
        """
        Use this before creating any entities to specify which engine plugins you require,
        if any.
        Pass in lists of strings of plugin names.
        """
        cls.engine_plugin_def['window'] = window
        cls.engine_plugin_def['gfx'] = gfx
        cls.engine_plugin_def['input'] = input
        cls.engine_plugin_def['audio'] = audio
            

    @classmethod
    def init_engines(cls):
        # Attempt to dynamically import the required engines 
        try:
            for backend_name in ['window', 'gfx', 'input', 'audio']:
                backend_module = __import__(
                    "myrmidon.engine.%s.%s.engine" % (backend_name, cls.engine_def[backend_name]),
                    globals(),
                    locals(),
                    ['Myrmidon_Backend'],
                    0
                    )
                cls.engine[backend_name] = backend_module.Myrmidon_Backend()
                
        except ImportError as detail:
            print("Error importing a backend engine.", detail)
            sys.exit()
            
        # Test mode uses dummy engines
        if cls.test_mode:
            from backend_dummy import MyrmidonWindowDummy, MyrmidonGfxDummy, MyrmidonInputDummy, MyrmidonAudioDummy
            cls.engine['window'] = MyrmidonWindowDummy()
            cls.engine['gfx'] = MyrmidonGfxDummy()
            cls.engine['input'] = MyrmidonInputDummy()
            cls.engine['audio'] = MyrmidonAudioDummy()
            return
        

    @classmethod
    def load_engine_plugins(cls, engine_object, backend_name):
        # Import plugin modules and create them
        try:
            engine_object.plugins = {}
            if len(cls.engine_plugin_def[backend_name]):
                for plugin_name in  cls.engine_plugin_def[backend_name]:
                    plugin_module = __import__(
                        "engine.%s.%s.plugins.%s" % (backend_name, cls.engine_def[backend_name], plugin_name),
                        globals(),
                        locals(),
                        ['Myrmidon_Backend'],
                        -1
                        )
                    engine_object.plugins[plugin_name] = plugin_module.Myrmidon_Engine_Plugin(engine_object)
                
        except ImportError as detail:
            print("Error importing a backend engine plugin.", detail)
            sys.exit()

            
    @classmethod
    def start_game(cls):
        """
        Called by entities if a game is not yet started.
        It initialises engines.
        """
        # Start up the backends
        cls.init_engines()
        cls.clock = cls.engine['window'].Clock()


    @classmethod
    def run_game(cls):
        """
        Called by entities if a game is not yet started.
        Is responsible for the main loop.
        """
        # No execution of anything if in test mode.
        if cls.test_mode:
            return
        
        while cls.started:
            # Reorder Entities by execution priority if necessary
            if cls.entity_priority_dirty == True:
                cls.entity_list.sort(
                    reverse=True,
                    key=lambda object:
                    object.priority if hasattr(object, "priority") else 0
                    )
                cls.entity_priority_dirty = False

            # If we have an input engine enabled we pass off to it
            # to manage and process input events.
            if cls.engine['input']:
                cls.engine['input'].process_input()

            # For each entity in priority order we iterate their
            # generators executing their code
            for entity in cls.entity_list:
                if entity.status == 0:
                    cls.current_entity_executing = entity
                    entity._iterate_generator()

            # If we have marked any entities for removal we do that here
            for x in cls.entities_to_remove:
                if x in cls.entity_list:
                    cls.entity_list.remove(x)
            cls.entities_to_remove = []

            # If we did a collision along the way then we should reset any
            # optimisations we may or may not have done on each entity.
            if cls.did_collision_check:
                cls.did_collision_check = False
                for entity in cls.entity_list:
                    entity.reset_collision_model()

            # Pass off to the gfx engine to display entities
            cls.engine['gfx'].update_screen_pre()
            cls.engine['gfx'].draw_entities(cls.entity_list)              
            cls.engine['gfx'].update_screen_post()

            # Wait for next frame, hitting a particular fps
            cls.fps = int(cls.clock.get_fps())
            cls.clock.tick(cls.current_fps)


    @classmethod
    def change_resolution(cls, resolution):
        cls.screen_resolution = resolution
        cls.engine['window'].change_resolution(resolution)
        cls.engine['gfx'].change_resolution(resolution)

        

    ##############################################
    # ENTITIES
    ##############################################
    @classmethod
    def entity_register(cls, entity):
        """
        Registers an entity with Myrmidon so it will be executed.
        """
        cls.entity_list.append(entity)
        cls.engine['gfx'].register_entity(entity)
        cls.entity_priority_dirty = True

        # Handle relationships
        if cls.current_entity_executing != None:
            entity.parent = cls.current_entity_executing
                
            if not entity.parent.child == None:
                entity.parent.child.prev_sibling = entity
                    
            entity.next_sibling = entity.parent.child
            entity.parent.child = entity


    @classmethod        
    def signal(cls, entity, signal_code, tree=False):
        """ Signal will let you kill a entity or put it to sleep
        
            Will accept an Entity object directly, an Entity type (will also match
            all child types of that Entity or the Entity type as a string.
            If more than one Entity matches, all of them will be signalled.
        
            The tree parameter can be used to recursively signal all the 
            entity's descendants
        
            Signal types-
            S_KILL - Permanently removes the entity
            S_SLEEP - Entity will disappear and will stop executing code
            S_FREEZE - Entity will stop executing code but will still appear
                and will still be able to be checked for collisions.
            S_WAKEUP - Wakes up or unfreezes the entity """
        
        # We've entered a specific type as a string
        if isinstance(entity, str):
            entity_iter = copy.copy(cls.entity_list)            
            for obj in entity_iter:
                if obj.__class__.__name__ == entity:
                    cls.single_object_signal(obj, signal_code, tree)

        # We've passed in a class type directly
        elif inspect.isclass(entity):
            entity_iter = copy.copy(cls.entity_list)            
            for obj in entity_iter:
                if isinstance(obj, entity):
                    cls.single_object_signal(obj, signal_code, tree)
            
        # Passed in an object directly    
        else:
            cls.single_object_signal(entity, signal_code, tree)
            return


    @classmethod
    def single_object_signal(cls, entity, signal_code, tree = False):
        """ Used by signal as a shortcut """
        
        # do children
        if tree:
            next_child = entity.child
            while next_child != None:
                cls.single_object_signal(next_child, signal_code, True)
                next_child = next_child.next_sibling
        
        # do this one
        if signal_code == S_KILL:
            cls.entity_destroy(entity)
        elif signal_code == S_WAKEUP:
            entity.status = 0
        elif signal_code == S_SLEEP:
            entity.status = S_SLEEP
        elif signal_code == S_FREEZE:
            entity.status = S_FREEZE


    @classmethod        
    def get_entities(cls, entity_type, tree=False):
        """This method returns a list of all Entities matching a type searched for.

        Keyword arguments:
        -- entity_type: Pass in either an Entity class (not instanced object)
          or a string containing the name of the class searching for.
          If passing in a class, this will also match all child classes.
        -- tree: If True then all childen of matched Entities  will be added too.
        """
        found_entity_list = []
        # We've entered a specific type as a string
        if isinstance(entity_type, str):
            for obj in cls.entity_list:
                if obj.__class__.__name__ == entity_type:
                    cls.add_entity_to_list(obj, found_entity_list, tree = tree)

        # We've passed in a class type directly
        elif inspect.isclass(entity_type):
            for obj in cls.entity_list:
                if isinstance(obj, entity_type):
                    cls.add_entity_to_list(obj, found_entity_list, tree = tree)

        return found_entity_list
    

    @classmethod
    def add_entity_to_list(cls, entity, entity_list, tree = False):
        """Used by the get_entities method to add a single Entity object to
        a list, if it doesn't already exist in the list, along with a tree of
        children if applicable.

        Keyword arguments:
        -- entity: An Entity obj to add to the given list.
        -- entity_list: The list to add to.
        -- tree: If we want to also add all the children of the Entity to the
          list. (default False)
        """
        if not entity in entity_list:
            entity_list.append(entity)

        if tree:
            next_child = entity.child
            while next_child != None:
                if not next_child in entity_list:
                    entity_list.append(next_child)
                next_child = next_child.next_sibling
           

    @classmethod
    def entity_destroy(cls, entity):
        """ Removes a entity """
        if (not entity in Game.entity_list) or (entity in Game.entities_to_remove):
            return
        entity.on_exit()
        cls.engine['gfx'].remove_entity(entity)
        Game.entities_to_remove.append(entity)

        
    ##############################################
    # INPUT
    ##############################################
    @classmethod        
    def keyboard_key_down(cls, key_code):
        """
        Ask if a key is currently being pressed.
        Pass in key codes that is relevant to your chosen input backend.
        """
        if not cls.engine['input']:
            raise MyrmidonError("Input backend not initialised.")
        return cls.engine['input'].keyboard_key_down(key_code)


    @classmethod        
    def keyboard_key_released(cls, key_code):
        """
        Ask if a key has just been released last frame.
        Pass in key codes that is relevant to your chosen input backend.
        """
        if not cls.engine['input']:
            raise MyrmidonError("Input backend not initialised.")
        return cls.engine['input'].keyboard_key_released(key_code)


    @classmethod
    def mouse(cls):
        """Gives access to an Entity object that represents the mouse.
        """
        return cls.engine['input'].mouse
    

    ##############################################
    # MEDIA 
    ##############################################
    @classmethod
    def load_image(cls, image = None, sequence = False, width = None, height = None, **kwargs):
        """Creates and returns an Image object that we can then attach to an Entity's image member
        to display graphics.
        A particular graphics engine may also have their own specific arguments not documented here.

        Keyword arguments:
        image -- The filesystem path to the filename that the image is contained in. Typically this can
          also be a pointer to already loaded image data if the gfx in-use supports such behaviour. (for
          instance, engines using PyGame to load images can be given a PyGame surface directly.) (Required)
        sequence -- Denotes if the image being loaded contains a series of images as frames. (default False)
        width -- If we have a sequence of images, this denotes the width of each frame. (default None)
        height -- The height of a frame in a sequence image, if not supplied this will default to
          the width. (default None)
        """
        return cls.engine['gfx'].Image(image, sequence, width, height, **kwargs)


    @classmethod
    def load_font(cls, font = None, size = 20, **kwargs):
        """Creates and returns a Font object that we give to the write_text method to specify how to render
        text. You can also dynamically change the font attribute of Text objects.
        A particular window engine may also have their own specific arguments not documented here.

        Keyword arguments:
        font -- The filesystem path to the filename that the font is contained in. Typically this can
          also be a pointer to an already loaded font if the engine in-use supports this behaviour. (For
          instance, eungines using Pygame for font loading can be given a pygame.font.Font object directly.)
          If None is supplied then the default internal font will be used if applicable. (default None)
        size -- The size of the text that we want to display. What this value actually relates to is dependant
          on the font loading engine used. (default 20)
        """
        return cls.engine['window'].Font(font, size, **kwargs)


    @classmethod
    def load_audio(cls, audio):
        """Creates and returns an Audio object that we can manipulate directly to play sounds.
        A particular audio engine may also have their own specific arguments not documented here.

        Keyword arguments:
        audio -- The filesystem path to the file that the sound is contained at. Typically this can
          also be a pointer to an already loaded audio object if the engine in-use supports this behaviour.
          (For instance, eungines using Pygame for audio can be given a pygame.mixer.Sound object directly.)
          (default None)
        """
        return cls.engine['audio'].Audio(audio)
    
    
    ##############################################
    # TEXT HANDLING
    ##############################################
    @classmethod    
    def write_text(cls, x, y, font, alignment = 0, text = "", antialias = True):
        return cls.engine['gfx'].Text(font, x, y, alignment, text, antialias = True)

    @classmethod    
    def delete_text(cls, text):
        if text in Game.entity_list:
            Game.entity_destroy(text)


    ##############################################
    # HELPFUL MATH
    ##############################################
    @classmethod    
    def get_distance(cls, pointa, pointb):
        return math.sqrt((math.pow((pointb[1] - pointa[1]), 2) + math.pow((pointb[0] - pointa[0]), 2)))

    @classmethod    
    def move_forward(cls, pos, distance, angle):
        pos2 = [0.0,0.0]
        
        pos2[0] = pos[0] + distance * math.cos(math.radians(angle))
        pos2[1] = pos[1] + distance * math.sin(math.radians(angle))             

        return pos2

    @classmethod    
    def angle_between_points(cls, pointa, pointb):
        """
        Take two tuples each containing coordinates between two points and
        returns the angle between those in degrees
        """
        return math.degrees(math.atan2(pointb[1] - pointa[1], pointb[0] - pointa[0]))

    @classmethod 
    def normalise_angle(cls, angle):
        """
        Returns an equivalent angle value between 0 and 360
        """
        """
        while angle < 0.0:
            angle += 360.0
        while angle >= 360.0:
            angle -= 360.0
        return angle
        """
        return angle % 360.0
    
    @classmethod
    def angle_difference(cls, start_angle, end_angle, skip_normalise = False):
        """
        Returns the angle to turn by to get from start_angle to end_angle.
        The sign of the result indicates the direction in which to turn.
        """
        if not skip_normalise:
            start_angle = cls.normalise_angle(start_angle)
            end_angle = cls.normalise_angle(end_angle)
        
        difference = end_angle - start_angle
        if difference > 180.0:
            difference -= 360.0
        if difference < -180.0:
            difference += 360.0
            
        return difference
    
    @classmethod
    def near_angle(cls, curr_angle, targ_angle, increment, leeway = 0):
        """ 
        Returns an angle which has been moved from 'curr_angle' closer to 
        'targ_angle' by 'increment'. increment should always be positive, as 
        angle will be rotated in the direction resulting in the shortest 
        distance to the target angle.
        leeway specifies an acceptable distance from the target to accept,
        allowing you to specify a cone rather than a specific point.
        """
        # Normalise curr_angle
        curr_angle = cls.normalise_angle(curr_angle)
            
        # Normalise targ_angle
        targ_angle = cls.normalise_angle(targ_angle)
            
        # calculate difference
        difference = cls.angle_difference(curr_angle, targ_angle, skip_normalise = True)
            
        # do increment
        if math.fabs(difference) <= leeway:
            return curr_angle
        elif math.fabs(difference) < increment:
            return targ_angle
        else:
            dir = difference / math.fabs(difference)
            return curr_angle + (increment * dir)


    @classmethod
    def rotate_point(cls, x, y, rotation):
        """Rotates a point in euclidian space using a rotation matrix.

        Keyword arguments:
        -- x:  First coordinate part of the point.
        -- y:  Second coordinate part of the point.
        -- rotation:  The amount to rotate by in degrees."""
        rotation = math.radians(rotation)
        return (math.cos(rotation) * x - math.sin(rotation) * y,
                math.sin(rotation) * x + math.cos(rotation) * y)


    @classmethod
    def rotate_point_about_point(cls, x, y, rotation, rotate_about_x, rotate_about_y):
        """Similar to rotate_point but allows specification of a separate point
        in space to rotate around.

        Keyword arguments:
        -- x:  First coordinate part of the point.
        -- y:  Second coordinate part of the point.
        -- rotation:  The amount to rotate by in degrees.
        -- rotate_about_x: First coordinate part of the point to rotate around.
        -- rotate_about_y: Second coordinate part of the point to rotate around."""
        p = cls.rotate_point(x - rotate_about_x, y - rotate_about_y, rotation)
        return p[0] + rotate_about_x, p[1] + rotate_about_y


    @classmethod
    def point_in_rectangle(cls, point, rectangle_origin, rectangle_size):
        """Returns True/False if a point is within a rectangle shape.

        Keyword arguments:
        -- point: Tuple containing the coordinates of the point.
        -- rectangle_origin: Tuple containing the position of the rectangle.
        -- rectangle_size: Tuple containing the width and height of the rectangle.
        """
        return (point[0] > rectangle_origin[0] and \
               point[0] < (rectangle_origin[0] + rectangle_size[0]) and \
               point[1] > rectangle_origin[1] and \
               point[1] < (rectangle_origin[1] + rectangle_size[1]))


    ##############################################
    # COLLISION ROUTINES
    ##############################################

    
    @classmethod
    def collision_rectangle_to_rectangle(cls, rectangle_a, rectangle_b):
        """
        Uses the separating axis theorem to check collisions between two
        Entities. Both must have COLLISION_TYPE_RECTANGLE set as their collision type.
        Returns True/False on collision.

        Keyword arguments:
        -- rectangle_a: The first Entity we are checking.
        -- rectangle_b: The Entity we are checking the first one against.
        """
        # retrieve loctaions of box corners
        check_object_a = rectangle_a.collision_rectangle_calculate_corners()
        check_object_b = rectangle_b.collision_rectangle_calculate_corners()

        # Step 1 is calculating the 4 axis of our two objects
        # we will use them check the collisions
        axis = [(0,0), (0,0), (0,0), (0,0)]
            
        axis[0] = (check_object_a['ur'][0] - check_object_a['ul'][0],
                   check_object_a['ur'][1] - check_object_a['ul'][1])

        axis[1] = (check_object_a['ur'][0] - check_object_a['lr'][0],
                   check_object_a['ur'][1] - check_object_a['lr'][1])
            
        axis[2] = (check_object_b['ul'][0] - check_object_b['ll'][0],
                   check_object_b['ul'][1] - check_object_b['ll'][1])

        axis[3] = (check_object_b['ul'][0] - check_object_b['ur'][0],
                   check_object_b['ul'][1] - check_object_b['ur'][1])

        # We will need to determine a collision for each of the 4 axis
        # If any of the axis do ~not~ collide then we determine that no
        # collision has occured.
        for single_axis in axis:
            # Step 2 is projecting the vectors of each corner of each rectangle
            # on to the axis. This is to determine the min/max projected vectors
            # of each rectangle.
            corner_vector_projection = {rectangle_a: dict(check_object_a), rectangle_b: dict(check_object_b)}
            rectangle_bounds = {rectangle_a: {'min' : None, 'max' : None}, rectangle_b: {'min' : None, 'max' : None}}

            for object_ in corner_vector_projection:
                for corner_name in corner_vector_projection[object_]:
                    projection = (
                        (
                            (corner_vector_projection[object_][corner_name][0] * single_axis[0]) + (corner_vector_projection[object_][corner_name][1] * single_axis[1])
                        ) / (
                            (single_axis[0] * single_axis[0]) + (single_axis[1] * single_axis[1])
                        )
                    )
                    corner_vector_projection[object_][corner_name] = ((projection * single_axis[0]) * single_axis[0]) + ((projection * single_axis[1]) * single_axis[1])

                    # Step 3 is working out what the min and max location of each corner
                    # projected on the axis is for each rectangle.
                    if rectangle_bounds[object_]['min'] is None or corner_vector_projection[object_][corner_name] < rectangle_bounds[object_]['min']:
                        rectangle_bounds[object_]['min'] = corner_vector_projection[object_][corner_name]

                    if rectangle_bounds[object_]['max'] is None or corner_vector_projection[object_][corner_name] > rectangle_bounds[object_]['max']:
                        rectangle_bounds[object_]['max'] = corner_vector_projection[object_][corner_name]

            # Step 4 is determining if the min and max corner projections of each rectangle on the axis overlap
            # If they don't then we can conclude that no collision has occured.
            if not (rectangle_bounds[rectangle_b]['min'] <= rectangle_bounds[rectangle_a]['max'] and rectangle_bounds[rectangle_b]['max'] >= rectangle_bounds[rectangle_a]['min']):
                return False
                
        # If we have got this far then we can assume that a collision has occured.
        return True


    @classmethod
    def collision_point_to_rectangle(cls, point, rectangle):
        """
        Checks the collision between an Entity with it's type as COLLISION_TYPE_POINT
        against one set as COLLISION_TYPE_RECTANGLE
        Returns True/False on collision.

        Keyword arguments:
        -- point: The Entity that is a point.
        -- rectangle: The Entity this is a rectangle.
        """
        # Get all usable values
        check_object_a = point.collision_point_calculate_point()
        check_object_b = rectangle.collision_rectangle_calculate_corners()
        check_object_b_size = rectangle.collision_rectangle_size()

        # rotate the point by -rectangle_angle around the centre of the rectangle
        rotated_point = Game.rotate_point_about_point(
            check_object_a[0],
            check_object_a[1],
            -rectangle.rotation,
            rectangle.x,
            rectangle.y
            )
        
        # Check that point is within the rectangle
        return Game.point_in_rectangle(rotated_point, (rectangle.x, rectangle.y), check_object_b_size)
    

    @classmethod
    def collision_circle_to_rectangle(cls, circle, rectangle):
        """
        Checks the collision between an Entity with it's type as COLLISION_TYPE_CIRCLE
        against one set as COLLISION_TYPE_RECTANGLE
        Returns True/False on collision.

        Keyword arguments:
        -- circle: The Entity that is a circle.
        -- rectangle: The Entity this is a rectangle.
        """
        check_object_a = circle
        check_object_b = rectangle
        check_object_a_radius = check_object_a.collision_circle_calculate_radius()
        check_object_b_corners = check_object_b.collision_rectangle_calculate_corners()
        check_object_b_size = check_object_b.collision_rectangle_size()
        
        # rotate the cicle by -rectangle_angle around the centre of the rectangle
        rotated_ciricle = Game.rotate_point_about_point(
            check_object_a.x,
            check_object_a.y,
            -check_object_b.rotation,
            check_object_b.x,
            check_object_b.y
            )

        half_width = check_object_b_size[0] / 2
        half_height = check_object_b_size[1] / 2
        
        circle_distance = (abs(rotated_ciricle[0] - check_object_b.x), abs(rotated_ciricle[1] - check_object_b.y))

        if circle_distance[0] > (half_width + check_object_a_radius) or \
           circle_distance[1] > (half_height + check_object_a_radius):
            return False

        if circle_distance[0] <= half_width or \
           circle_distance[1] <= half_height:
            return True

        corner_distance_sq = ((circle_distance[0] - half_width) ** 2) + ((circle_distance[1] - half_height) ** 2)

        return (corner_distance_sq <= (check_object_a_radius**2))                            


    @classmethod
    def collision_circle_to_circle(cls, circle_a, circle_b):
        """
        Checks the collision between two Entities of type as COLLISION_TYPE_CIRCLE.
        Returns True/False on collision.

        Keyword arguments:
        -- circle_a: The first Entity.
        -- circle_b: The Entity we are checking against.
        """
        check_object_a = circle_a
        check_object_b = circle_b
        check_object_a_radius = check_object_a.collision_circle_calculate_radius()
        check_object_b_radius = check_object_b.collision_circle_calculate_radius()

        # Outside of each others radius
        if check_object_a.get_distance((check_object_b.x, check_object_b.y)) > check_object_a_radius + check_object_b_radius:
            return False

        return True


    @classmethod
    def collision_point_to_circle(cls, point, circle):
        """
        Checks the collision between an Entity with it's type as COLLISION_TYPE_POINT
        against one set as COLLISION_TYPE_CIRCLE
        Returns True/False on collision.

        Keyword arguments:
        -- point: The Entity that is a point.
        -- circle: The Entity this is a circle.
        """
        check_object_a = point
        check_object_b = circle
        check_object_a_point = check_object_a.collision_point_calculate_point()
        check_object_b_radius = check_object_b.collision_circle_calculate_radius()
                    
        # Outside of each others radius
        if cls.get_distance(check_object_a_point, (check_object_b.x + check_object_b_radius, check_object_b.y + check_object_b_radius)) > check_object_b_radius:
            return False

        return True


    @classmethod
    def collision_point_to_point(cls, point_a, point_b):
        """
        Checks collision between two Entities with their type as COLLISION_TYPE_POINT.
        Practically useless but here for completion.
        Returns True/False on collision.        

        Keyword arguments:
        -- point_a: The first Entity.
        -- point_b: The Entity we are checking against.
        """        
        point_a = point_a.collision_point_calculate_point()
        point_b = point_b.collision_point_calculate_point()
        return True if point_a[0] == point_b[0] and point_a[1] == point_b[1] else False


# Define the collision function lookups so we entities know which one to call
# depending on the types of Entities it is comparing.
# (We can't create this  function map until the class has been defined so we must
# do it out of the class definition here.)
Game.collision_methods = {
        (COLLISION_TYPE_RECTANGLE, COLLISION_TYPE_RECTANGLE) : Game.collision_rectangle_to_rectangle,
        (COLLISION_TYPE_POINT, COLLISION_TYPE_RECTANGLE) : Game.collision_point_to_rectangle,
        (COLLISION_TYPE_RECTANGLE, COLLISION_TYPE_POINT) : Game.collision_point_to_rectangle,
        (COLLISION_TYPE_CIRCLE, COLLISION_TYPE_RECTANGLE) : Game.collision_circle_to_rectangle,
        (COLLISION_TYPE_RECTANGLE, COLLISION_TYPE_CIRCLE) : Game.collision_circle_to_rectangle,
        (COLLISION_TYPE_CIRCLE, COLLISION_TYPE_CIRCLE) : Game.collision_circle_to_circle,
        (COLLISION_TYPE_POINT, COLLISION_TYPE_CIRCLE) : Game.collision_point_to_circle,
        (COLLISION_TYPE_CIRCLE, COLLISION_TYPE_POINT) : Game.collision_point_to_circle,
        (COLLISION_TYPE_POINT, COLLISION_TYPE_POINT) : Game.collision_point_to_point
        }



class MyrmidonError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


