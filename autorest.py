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

'''
autoREST is a tool to create simple REST API for legacy applications.

You just need to create a json-like structure in which you define the
  functions that you want to implement, and which is the commandline that
  implements the function.

E.g. a simple API for docker that respond to the next endpoints
    http://localhost:8080/container/
    http://localhost:8080/container/<id>

    endpoints = {
        'container': {
            'callback': {
                'type': 'application',
                'command': [ '/usr/bin/docker', 'ps' ]
            }
        },
        'container_info': {
            'route': 'container',
            'parameters': [ 'cid' ],
            'callback': {
                'type': 'application',
                'command': [ '/usr/bin/docker', 'inspect', '<cid>' ]
            }
        }
    }
    
    if __name__ == '__main__':
        autorest.setup_routing(endpoints)
        bottle.run(host='localhost', port=8080)

The JSON structure
==================
Each attribute for the json structure refer to a route in the endpoint of the server. If no route is specified, the
    route defaults to the name of the function (i.e. http://server/<function>)

The structure of each function is the next: 
{
    'route': <route in the URL>,
    'parameters': [ <ordered list of the parameters in the URL> ] (i.e. [ "param1", "param2" ] will 
        match http://server/<function>/param1/param2)
    'callback': {
        'type': <type of callback> (the only available type at this moment is 'application')
        'command': [
            <ordered list of parameters for the commandline, if you use the pattern <PARAMNAME> 
            and PARAMNAME is in the 'parameters field', it will be substituted for the corresponding parameter>
        ]
    },
    'auth': {
        type: <type of authorization> (the only available type at this moment is 'user:token'),
        data: [
            <list of tuples { "user": "username", "token": "tid" }>
        ] (the data parameter depend on the type of autorization)
    }
}

Extending the API
=================
autoREST is based on bottlepy () so you can add other routes to the bottle server. autoREST will not start the bottle
    server. Instead you must start it by yourself.
'''

import runcommand
import json
import os
import stat
from bottle import route, run, template, response, HTTPResponse, HTTPError, request

class Auth:
    @staticmethod
    def parse(o = None):
        # If there is not any information about authentication, will return no Auth method
        if o is None:
            return None

        if 'type' in o:
            if o['type'] != 'user:token':
                raise Exception('authentication type not recognised')

        if 'data' not in o:
            return Auth_UserToken()
        
        return Auth_UserToken(o['data'])

class Auth_UserToken(Auth):
    def __init__(self, data = None):
        self.user2token = {}
        if data is None:
            return
            
        for udata in data:
            if 'user' in udata and 'token' in udata:
                self.user2token[udata['user']] = udata['token']

    def check(self, user, passwd):
        if user in self.user2token:
            if passwd == self.user2token[user]:
                return True
        return False

class ErrorCodes:
    def __init__(self, o = None):
        self.default = 500
        self.map = {}

    def get_html_error(self, errcode):
        if errcode in self.map: return self.map[errcode]
        return self.default

    def get_from_object(self, o = None):
        if o is None: return
        if type(o)==str:
            o = json.loads(o)

        if 'default' in o: self.default = o['default']
        if 'error' in o:
            for e in o['error']:
                if 'callback' not in e or 'html' not in e:
                    raise Exception("malformed error map")
                self.map[e['callback']] = e['html']

    def build_response(self, errcode, out, err):
        if errcode == 0:
            # If its execution succeeded, we build a response
            v = Response(out)
        else:
            # Otherwise we'll build an error response
            status = self.default
            if errcode in self.map: status = self.map[errcode]
            v = Response({'autorest':{'out': out, 'err': err, 'status': status}})
        return v.response()

class Callback:
    def __init__(self):
        self.type = 'application'
        self.command = None

    def get_from_object(self, o):
        if o is None: return
        if type(o)==str:
            o = json.loads(o)

        if 'type' in o: self.type = o['type']
        if 'command' in o: self.command = o['command']
        if type(self.command)!=list:
            self.command = [ self.command ]

        real_path = os.path.expandvars(os.path.expanduser(self.command[0]))
        try:
            if not (stat.S_IXUSR & os.stat(real_path)[stat.ST_MODE]):
                raise Exception('command %s is not valid' % self.command)
        except:
            raise Exception('command %s is not valid' % self.command)                
        self.command[0] = real_path

class FunctionInfo:
    def __init__(self, name, o):
        self.parameters = []
        self.method = 'GET'
        self.callback = Callback()
        self.auth = None
        self.route = name
        self.errorcodes = ErrorCodes()
        self.get_from_object(o)

    def get_from_object(self, o):
        if type(o)==str:
            o = json.loads(o)

        if 'route' in o: self.route = o['route']
        if 'parameters' in o: self.parameters = o['parameters']
        if 'method' in o: self.method = o['method']
        if 'callback' in o: 
            self.callback.get_from_object(o['callback'])
        if 'auth' in o: 
            self.auth = Auth.parse(o['auth'])

        if 'errorcodes' in o:
            self.errorcodes.get_from_object(o['errorcodes'])

class Response:
    def __init__(self, o = None):
        self.status = 200
        self.out = None
        self.err = None
        self.type = "plain/text"
        if o is not None: self.get_from_object(o)

    def get_from_object(self, _o):
        o = _o
        if type(o)==str:
            try:
                o = json.loads(o)
            except:
                self.out = o
                return

        if 'autorest' in o:
            o = o['autorest']
        else:
            self.out = _o
            return

        if 'status' in o: self.status = o['status']
        if 'out' in o: self.out = o['out']
        if 'err' in o: self.err = o['err']
        if 'type' in o: self.type = o['type']
    
    def response(self):
        out = self.out or ""
        err = self.err or ""
        return HTTPResponse("%s%s" % (out, err), self.status)
        return HTTPError(self.status, "%s%s" % (out, err))

'''
This functions generates one function to serve the route passed in function_info
'''
def getfunction(function_info):
    wrapper = None

    '''
    Here we take benefit from the local scope of the parameters to create the new function that
      reads the data from the function_info structure, which will be particular for each call to
      get_function.
    '''
    def wrapper_app(*args, **kwargs):

        # If the function has an auth structure, we will use it and request the user/password
        #   using the http basic authentication
        if function_info.auth is not None:
            user, password = request.auth or (None, None)
            if user is None or not function_info.auth.check(user, password):
                err = HTTPError(401, "Authentication needed")
                err.add_header('WWW-Authenticate', 'Basic realm="Login required"')
                return err            

        # The call to the command will be in array form, so we ensure that the command is included
        parameters = []
        command = function_info.callback.command
        if type(command)==list: 
            parameters = command[:]
        elif type(command)==str:
            parameters.append(command)
        else:
            raise Exception("type of command not supported: %s" % command)

        # Now we add the parameters (in the same order that are requested in the parameter field)
        for pname in function_info.parameters:
            if pname in kwargs:
                pattern = "<%s>" % pname
                parameters = [ p.replace(pattern, kwargs[pname]) for p in parameters ]
            else:
                raise Exception('parameter %s is not defined' % pname)

        # We will pass the post information to the app as the stdin
        inputtext = request.body.readlines()

        # Finally we run the application
        errcode, output, error = runcommand.runcommand_e(parameters, False, timeout = 5, strin = ''.join(inputtext))
        return function_info.errorcodes.build_response(errcode, output, error)

    # By now we only support callbacks of type application, but the idea is that we could also
    #   create proxy requests (execute an extra curl request to other url) or even simple python
    #   functions
    if function_info.callback.type == 'application':
        wrapper = wrapper_app
    return wrapper

'''
This functions does the magic of registering the routes for the functions, by calling a function to create the
  function that will serve the requests.
'''
def setup_routing(functions):
    for function, info in functions.items():
        f_info = FunctionInfo(function, info)
        param_array = []
        for p in f_info.parameters:
            param_array.append('<%s>' % p)

        s_route = '/%s' % (f_info.route)

        if (len(param_array) > 0):
            s_route = "%s/%s" % (s_route, '/'.join(param_array))
            s_route = s_route.replace('//', '/')

        print "%s @ %s " % (f_info.method, s_route)
        route('%s' % (s_route), f_info.method, getfunction(f_info))