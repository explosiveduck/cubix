import sys
import os

def get_path():

    path0 = os.path.realpath(sys.path[0])
    path1 = os.path.realpath(sys.path[1])

    pathtest = os.sep.join(path0.split(os.sep)[:-1])

    if pathtest == path1:
        return path1
    else:
        return path0

def resolve_path(*location):
    path = get_path()
    location = (path,) + location
    location = os.sep.join(location)
    return location

def read_file(path):
    output = ''
    with open(path, 'r') as f:
        output = f.read()
    return output