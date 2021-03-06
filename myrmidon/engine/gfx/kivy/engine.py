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

- BACKEND FILE -
- GRAPHICS     -

Provides a Kviy-based graphics adaptor.
"""

import copy

from myrmidon import Game, Entity, BaseImage, MyrmidonError
from myrmidon.consts import *

import kivy
from kivy.core.image import Image as Kivy_Image
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Color, Scale, Rotate, PushMatrix, PopMatrix, Translate, Quad
from kivy.graphics.texture import Texture
from kivy.core.window import Window
from kivy.graphics.opengl import glBlendFunc, glBlendFuncSeparate, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ONE


class Myrmidon_Backend(Entity):
    clear_colour = (0.0, 0.0, 0.0, 1.0)
    z_index_dirty = True
    entity_list_draw_order = []

    def __init__(self):
        # Try hiding soft keys on certain ondroid phones
        self.get_device_size_metrics()
        self.entity_draws = {}
        self.widget = None

    def get_device_size_metrics(self):
        self.device_resolution = Window.width, Window.height
        Game.device_scale = float(Window.height) / Game.screen_resolution[1]
        # If any x position adjustment is necessary cos aspect ratio is lower than ideal
        Game.global_x_pos_adjust = 0.0
        if float(self.device_resolution[0]) / self.device_resolution[1] < float(Game.screen_resolution[0]) / Game.screen_resolution[1]:
            Game.global_x_pos_adjust = float((Game.screen_resolution[0] * Game.device_scale) - self.device_resolution[0]) / 2

    def change_resolution(self, resolution):
        pass


    def update_screen_pre(self):
        pass


    def update_screen_post(self):
        pass


    def draw_entities(self, entity_list):
        self.get_device_size_metrics()

        # Create our canvas to draw to if we hadn't got one yet
        if self.widget is None:
            self.widget = Widget()
            Game.engine['window'].kivy_app.widget.add_widget(self.widget)
        self.widget.width = Window.width
        self.widget.height = Window.height

        # If our z order is potentially dirty then we need to completely redraw
        # everything, se we clear the canvas and draw list, then get the proper order.
        if self.z_index_dirty:
            self.widget.canvas.clear()
            self.entity_draws = {}

            #self.entity_list_draw_order = copy.copy(entity_list)
            self.entity_list_draw_order = entity_list
            self.entity_list_draw_order.sort(
                key=lambda object:
                object.z if hasattr(object, "z") else 0,
                reverse = True
                )
            self.z_index_dirty = False

        # Now render for each entity
        for entity in self.entity_list_draw_order:

            if entity.image and getattr(entity.image, "image", None):
                platform.glBlendFunc()
                # Work out the real width/height and screen position of the entity
                size = ((entity.image.width) * (entity.scale * Game.device_scale), (entity.image.height) * (entity.scale * Game.device_scale))
                x, y = entity.get_screen_draw_position()
                y = Game.screen_resolution[1] - (entity.image.height * entity.scale) - y
                pos = ((x * Game.device_scale) - Game.global_x_pos_adjust, y * Game.device_scale)

                # If this entity hasn't yet been attached to the canvas then do so
                if not entity in self.entity_draws:
                    self.entity_draws[entity] = dict()
                    with self.widget.canvas:
                        self.entity_draws[entity]['color'] = color = Color()
                        platform.apply_rgb(entity, color)
                        color.a = entity.alpha
                        PushMatrix()
                        self.entity_draws[entity]['translate'] = Translate()
                        self.entity_draws[entity]['rotate'] = Rotate()
                        self.entity_draws[entity]['rotate'].set(entity.rotation, 0, 0, 1)
                        self.entity_draws[entity]['rect'] = Quad(
                            texture = entity.image.image.texture,
                            points = (0.0, 0.0, size[0], 0.0, size[0], size[1], 0.0, size[1])
                            )
                        self.entity_draws[entity]['translate'].xy = pos
                        PopMatrix()
                    # Otherwise just update values
                else:
                    self.entity_draws[entity]['rotate'].angle = entity.rotation
                    self.entity_draws[entity]['translate'].xy = pos
                    color = self.entity_draws[entity]['color']
                    platform.apply_rgb(entity, color)
                    color.a = entity.alpha
                    self.entity_draws[entity]['rect'].texture = entity.image.image.texture
                    self.entity_draws[entity]['rect'].points = (0.0, 0.0, size[0], 0.0, size[0], size[1], 0.0, size[1])

            entity.draw()


    def draw_single_entity(self, entity):
        pass


    def create_texture_list(self, entity, image):
        return None


    def draw_textured_quad(self, width, height, repeat = None):
        pass


    def register_entity(self, entity):
        self.z_index_dirty = True


    def remove_entity(self, entity):
        self.z_index_dirty = True


    def alter_x(self, entity, x):
        pass


    def alter_y(self, entity, y):
        pass


    def alter_z(self, entity, z):
        self.z_index_dirty = True


    def alter_image(self, entity, image):
        pass


    def alter_alpha(self, entity, alpha):
        pass


    def alter_colour(self, entity, colour):
        pass


    def alter_scale(self, entity, scale):
        pass


    def alter_rotation(self, entity, rotation):
        pass


    def new_image(self, width, height, colour = None):
        return Myrmidon_Backend.Image()


    def draw_line(self, start, finish, colour = (1.0,1.0,1.0,1.0), width = 5.0, noloadidentity = False):
        pass


    def draw_circle(self, position, radius, colour = (1.0,1.0,1.0,1.0), width = 5.0, filled = False, accuracy = 24, noloadidentity = False):
        pass


    def draw_rectangle(self, top_left, bottom_right, colour = (1.0,1.0,1.0,1.0), filled = True, width = 2.0, noloadidentity = False):
        pass


    def rgb_to_colour(self, colour):
        colour = list(colour)
        if kivy.platform in ['ios', 'macosx'] and len(colour) > 3:
            pre_multiply = colour[3] / 255.0
        else:
            pre_multiply = 1.0
        for k,a in enumerate(colour):
            colour[k] = ((a/255.0) * (pre_multiply if k < 3 else 1.0))
        return colour


    class Image(object):
        EMPTY_IMAGE = Kivy_Image(Texture.create(size=(0, 0)))

        width = 0
        height = 0
        filename = None
        is_sequence_image = False

        def __init__(self, image = None, sequence = False, width = None, height = None, mipmap = True):
            if image is None:
                self.image = self.EMPTY_IMAGE
                self.width = 0
                self.height = 0
                return
            if isinstance(image, str):
                self.filename = image
                try:
                    self.image = Kivy_Image(image, mipmap = mipmap)
                except:
                    raise MyrmidonError("Couldn't load image from " + image)
            else:
                self.image = Kivy_Image(image)
            self.width = self.image.width
            self.height = self.image.height

        def destroy(self):
            """
            Explicitly removes this image from the video memory and
            Kivy's cache.
            This functionality requires the custom kivy version at
            http://github.com/arcticshores/kivy
            """
            if self.image is None or self.image is self.EMPTY_IMAGE:
                return

            from kivy.cache import Cache
            from kivy.graphics.opengl import glBindTexture, glDeleteTextures
            from kivy.logger import Logger

            Logger.debug("MyrmidonGFX: Destroying {0}".format(self.filename if self.filename else self.image))

            # Remove from cache
            self.image.remove_from_cache()

            # Convert the ID to the right byte format for the GL method
            a1 = (self.image.texture.id >>  0) & 0xFF
            a2 = (self.image.texture.id >>  8) & 0xFF
            a3 = (self.image.texture.id >> 16) & 0xFF
            a4 = (self.image.texture.id >> 24) & 0xFF

            # Remove texture completely
            glBindTexture(self.image.texture.target, 0)
            glDeleteTextures(1, bytes(bytearray([a1, a2, a3, a4])))

            # Since we've done a manual removal kivy shouldn't do it's own removal later
            self.image.texture.nofree = 1

            # Stop this image from being used as a texture now
            self.image = None


    class _Text(Entity):
        alignment = ALIGN_CENTER
        label = None
        _text = ""
        _font = None
        _antialias = True

        text_image_size = (0,0)

        _shadow = None

        def generate_label(self):
            if self.font is not None:
                label = Label(font_name = self.font.filename, font_size = self.font.size, mipmap = True)
            else:
                label = Label(font_size = "30", mipmap = True)
            return label

        def __init__(self, font, x, y, alignment, text, antialias = True):
            Entity.__init__(self)
            self.font = font
            self.x = x
            self.y = y
            self.z = -500.0
            self.alignment = alignment
            self.text = text
            self.antialias = antialias
            self._is_text = True
            self.rotation = 0.0
            self.normal_draw = False

        def get_screen_draw_position(self):
            """ Overriding entity method to account for text alignment. """
            draw_x, draw_y = self.x, self.y

            if self.alignment == ALIGN_TOP:
                draw_x -= (self.text_image_size[0]/2)
            elif self.alignment == ALIGN_TOP_RIGHT:
                draw_x -= self.text_image_size[0]
            elif self.alignment == ALIGN_CENTER_LEFT:
                draw_y -= (self.text_image_size[1]/2)
            elif self.alignment == ALIGN_CENTER:
                draw_x -= (self.text_image_size[0]/2)
                draw_y -= (self.text_image_size[1]/2)
            elif self.alignment == ALIGN_CENTER_RIGHT:
                draw_x -= self.text_image_size[0]
                draw_y -= (self.text_image_size[1]/2)
            elif self.alignment == ALIGN_BOTTOM_LEFT:
                draw_y -= self.text_image_size[1]
            elif self.alignment == ALIGN_BOTTOM:
                draw_x -= (self.text_image_size[0]/2)
                draw_y -= self.text_image_size[1]
            elif self.alignment == ALIGN_BOTTOM_RIGHT:
                draw_x -= self.text_image_size[0]
                draw_y -= self.text_image_size[1]

            return draw_x, draw_y

        # text
        @property
        def text(self):
             return self._text

        @text.setter
        def text(self, value):
            if self._text == value:
                return
            self._text = value
            self.destroy_text_image()
            self.generate_text_image()

        @text.deleter
        def text(self):
            self._text = ""
            self.destroy_text_image()
            self.generate_text_image()

        def on_exit(self):
            self.destroy_text_image()

        def destroy_text_image(self):
            """Destroy the underlying image."""
            if self.image:
                self.image.destroy()
                self.image = None


    class DefaultText(_Text):
        def generate_text_image(self):
            label = self.generate_label()
            label.text = self._text
            label.texture_update()
            if not label.texture:
                self.text_image_size = (0, 0)
                self.image = Myrmidon_Backend.Image()
                return

            self.text_image_size = label.texture_size
            self.image = Myrmidon_Backend.Image(label.texture)


    class AppleText(_Text):
        def generate_text_image(self):
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            label = self.generate_label()
            label.text = self._text
            label.texture_update()
            if not label.texture:
                self.text_image_size = (0, 0)
                self.image = Myrmidon_Backend.Image()
                return

            self.text_image_size = label.texture_size
            tex = Texture.create(size=label.texture.size, mipmap=True)
            tex.blit_buffer(label.texture.pixels, colorfmt='rgba', bufferfmt='ubyte')
            tex.flip_vertical()
            self.image = Myrmidon_Backend.Image(tex)

    Text = {
        'ios': AppleText,
        'macosx': AppleText,
    }.get(kivy.platform, DefaultText)


# Platform specific functions
class DefaultPlatform(object):
    @staticmethod
    def glBlendFunc():
        """Blend function for blending images onscreen."""
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    @staticmethod
    def apply_rgb(entity, color):
        """Apply an entity's colour and alpha to a Kivy Colour object."""
        color.rgb = entity.colour


class ApplePlatform(object):
    @staticmethod
    def glBlendFunc():
        glBlendFuncSeparate(GL_ONE, GL_ONE_MINUS_SRC_ALPHA, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    @staticmethod
    def apply_rgb(entity, color):
        color.rgb = entity.alpha, entity.alpha, entity.alpha


platform = {
    'ios': ApplePlatform,
    'macosx': ApplePlatform,
}.get(kivy.platform, DefaultPlatform)
