#!/usr/bin/env python
#
# autoREST - ease the creation of REST APIs for commandline applications
#
# Copyright (C) 2017 - GRyCAP - Universitat Politecnica de Valencia
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# 
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import version

setup(name='autorest',
      version=version.get(),
      description='autoREST is a tool to create simple REST API for legacy applications',
      author='Carlos de Alfonso',
      author_email='caralla@upv.es',
      url='https://github.com/grycap/autorest',
      packages = [ 'autorest' ],
      package_dir = { 'autorest' : '.'},
)
