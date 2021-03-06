#!/usr/bin/env python

from distutils.core import setup

setup(
    name = 'Myrmidon',
    version = '0.5',
    description = '2D game framework for rapid development',
    author = 'Fiona Burrows',
    author_email = 'fiona@justfiona.com',
    url = 'http://www.github.com/Fiona/Myrmidon',
    packages = [
        'myrmidon', 'myrmidon.engine',
        'myrmidon.engine.audio', 'myrmidon.engine.audio.pygame', 'myrmidon.engine.audio.kivy',
        'myrmidon.engine.window', 'myrmidon.engine.window.pygame', 'myrmidon.engine.window.kivy',
        'myrmidon.engine.input', 'myrmidon.engine.input.pygame', 'myrmidon.engine.input.kivy',
        'myrmidon.engine.gfx', 'myrmidon.engine.gfx.opengl', 'myrmidon.engine.gfx.modern_opengl', 'myrmidon.engine.gfx.kivy',
    ],
    requires = ['pygame', 'OpenGL']
    )
