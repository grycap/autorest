# autoREST

autoREST is a tool to create simple REST API for legacy applications.

You just need to create a json-like structure in which you define the functions that you want to implement, and which is the commandline that implements the function.

## Example
E.g. a simple API for docker that respond to the next endpoints

```python
    http://localhost:8080/container/
    http://localhost:8080/container/<id>

    endpoints = {
        'container': {
            'callback': {
                'command': [ '/usr/bin/docker', 'ps' ]
            }
        },
        'container_info': {
            'route': 'container',
            'parameters': [ 'cid' ],
            'callback': {
                'command': [ '/usr/bin/docker', 'inspect', '<cid>' ]
            },
            'errorcodes': {
                'default': 404
            }
        }
    }

    if __name__ == '__main__':
        autorest.setup_routing(endpoints)
        bottle.run(host='localhost', port=8080)
```

At this point you should be able to issue commands like:

```bash
    $ curl -XGET http://localhost:8080/container/
    $ curl -XGET http://localhost:8080/container/b48fb9364e84
```

and the output will be the list of containers (in the case of the first command), and the information for one container (in the case of the second command).

# Documentation

autoREST makes use of a json-like python object with the following structure:

```python
{
    "function_name": <FUNCTION STRUCTURE>,
    "function_name2": <FUNCTION STRUCTURE 2>,
    ...
}
```

It makes use of a JSON object instead of a list in order to make it easier and more readable the creation of the structure that defines the server.

For each function, it is needed to create a structure that defines some features of the function and, in particular, defines how the commandline to implement the function is built.

## The FUNCTION STRUCTURE for each function

Each attribute for the json structure refer to a route in the endpoint of the server. If no route is specified, the
    route defaults to the name of the function (i.e. http://server/<function>)

The structure of each function is the next: 
```python
{
    'route': <route in the URL>,
    'parameters': [ <ordered list of the parameters in the URL> ]
    'callback': {
        'type': <type of callback>,
        'command': [ <ordered list of parameters for the commandline> ]
    },
    'auth': {
        type: <type of authorization>,
        data: [ <data for authorization> ]
    }
}
```

and its default values are the next:

```python
{ 
    'route': <the name of the function>, 
    'parameters': [],
    'callback': {
        'type': 'application',
        'command': []
    },
    'auth': None,
    'errorcodes': {
        'default': 500,
        'error': []
    }
  }
```

### route
The route field refers to the path of the URI that will match the REST function. If not included, the route default to the name of the function.

If the server listens at ```http://localhost:8080```, the route means that the function will try to match at ```http://localhost:8080/<route>/```.

### parameters
It is a sorted list of the parameters that will be matched in the URL. Even if the URL includes the _route_ for the function, if it does not include all the parameters, stated in this field, it will not match.

If the server listens at ```http://localhost:8080```, and the value of parameters is ```[ "param1", "param2" ]```, the function will be triggered if the URL matches ```http://localhost:8080/<route>/<value1>/<value2>```.

Later, the parameters can be used to build the commandline for the legacy application, using their names.

### callback

The _callback_ structure define the command that will implement the function. It has two fields: _type_ and _command_: 

* **type** is the type of callback. At this time, the only type supported is _'application'_. But this parameter is included for the case that it is wanted to extend _autoREST_ with other type of callback such as _REST calls to other URLs_ (i.e. reflections) or _calls to python functions_.

* **command** the callbacks of type _application_ must include this field. It builds the commandline that will be executed, to get the response.

    It is possible to use the parametes included in the field _parameters_ to build the commandline. In order to make it, you can include the name of the parameter between \< and \> to get the value of the refered parameter.

    If defined a function that will match ```http://localhost:8080/<route>/<param1>/<param2>```, it is possible to set a command like ```[ "/bin/ls", "<param1>" ]``` to grab the value of the first parameter.

    It is also possible to use the parameters **inside** a string and its value will be fully substituted. E.g. ```[ "/bin/ls", "/tmp/<param1>" ]```.

### auth

The _auth_ structure is included to protect each of the functions. If included, it will ask the browser for authentication (basic authentication), to include the user and password. It has two fields: _type_ and _command_: 

```python
    'auth': {
        type: 'user:token',
        data: [
            { "user": "username", "token": "tid" }, ...
        ]
    }
```

* **type** is the type of callback. At this time, the only type supported is _'user:token'_. But this parameter is included for the case that it is wanted to extend _autoREST_ with other type of methods of athentication.

* **data** the authentication methods of type _user:token_ must include this field. It includes a list of pairs _user/token_ that will be used to authenticate the access. 

    It is a pythonic list that include tuples with the form ```{ "user": "username", "token": "tid" }```.

### errorcodes

The _errorcodes_ structure defines the _HTML_ errorcode to send to the client, depending on the result of the callback. It has two fields: _default_ and _error_.

* **default** is the default HTML errorcode to send in case of failure of the call.

* **error** is a list of pair _errcode/htmlerror_ that will be used to build the response to the client.

    It is a pythonic list that include tuples with the form ```{ "callback": errno, "html": errcode }```.

## Extending the REST API
autoREST is based on bottlepy () so you can add other routes to the bottle server. autoREST will not start the bottle
    server. Instead you must start it by yourself.