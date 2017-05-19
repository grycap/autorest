# coding: utf-8
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

import autorest
import bottle

functions = {
    'container': {
        'callback': {
            'type': 'application',
            'command': [ '/usr/bin/docker', 'ps', '-a' ]
        }
    },
    'container_info': {
        'route': 'container',
        'parameters': [ 'cid' ],
        'callback': {
            'type': 'application',
            'command': [ '/usr/bin/docker', 'inspect', '<cid>' ]
        },
        'errorcodes': {
            'default': 404
        }
    },
    'image': {
        'callback': {
            'command': [ '/usr/bin/docker', 'images' ]
        }
    },
    'image_info': {
        'route': 'image',
        'parameters': [ 'iid' ],
        'callback': {
            'command': [ '/usr/bin/docker', 'inspect', '<iid>' ]
        },
        'errorcodes': {
            'default': 404
        }
    }
}

if __name__ == '__main__':
    autorest.setup_routing(functions)
    bottle.run(host='localhost', port=8080)