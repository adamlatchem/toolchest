#!blender -b blend-file-name -P blend2json.py -- output-file-name
#
# Render a blend file as json.
#
# File format reference:
# https://svn.blender.org/svnroot/bf-blender/trunk/blender/doc/blender_file_format/
#
# The following can change when blender opens the file:
# . Addresses - the blend file is a memory dump so these change based on where the
#   running instance of blender loads the file. This is not deterministic so
#   excluded from output to prevent excessive VCS diffs.
# . 'filepath' - will change if the file has been moved since last saved. Will
#   appear in VCS diffs in addition to real changes.
# . 'seed' - Changes but will not appear in VCS diffs since both a and b will
#   change to the same value as it is deterministic.
#
# For performance:
# . the blend DNA information is not output. The top level 'version' key
#   can indirectly supply this information.
# . bpy_prop_arrays larger than 100 items render as an md5 hash. This typically
#   happens for icon pixel data.
# . binary data is always rendered as an md5 hash. For example embedded files.
#
# For ease of graph navigation:
# . object references take the form "_identityRef": "<obj-identity>"
# . objects are identified by "_identity": "<obj-identity>"
# To go to an object definition remove 'Ref' from the reference site text and
# search. To find all references add 'Ref' and search. <obj-identity> is of the form
# "ClassName:obj-name" for named objects and "ClassName#instance-number" for
# anonymous objects.
#
import bpy
import json
import sys
import mathutils
import hashlib


class BlendEncoder(json.JSONEncoder):
    """ JSON Encoder customized for Blender """

    def __init__(self, *args, **kwargs):
        self.cycle_detector = {}
        self.pseudo_address = {}
        super(BlendEncoder, self).__init__(*args, **kwargs)

    def default(self, obj):
        """ Override JSONEncode. """
        pod = self.encode_pod(obj)
        if pod is None:
            raise Exception(f'Unexpected type encountered {type(obj)}')
        return pod

    def encode_bpy_prop_array(self, obj):
        """ Encode a bpy_prop_array. """
        if len(obj) > 100:
            digest = hashlib.md5(str([i for i in obj]).encode()).hexdigest()
            return [f"length-items:{len(obj)} md5:{digest}"]
        return [self.encode_pod(value) or value for value in obj]

    def encode_bpy_prop_collection(self, obj):
        """ Encode a bpy_prop_collection. """
        result = {}
        for key in obj.keys():
            value = obj[key]
            result[key] = self.encode_pod(value) or value
        return result

    def encode_bpy_struct(self, obj):
        """ Encode a bpy_struct. """
        self.cycle_detector[self.identity(obj)] = True
        result = {'_identity': self.identity(obj)}
        for key in dir(obj):
            if key[:2] == '__' or key[:3] == 'rna' or key[:6] == 'users_' \
                    or key in ['original', 'bl_rna', 'all_objects', 'keying_sets_all', 'field']:
                # Remove keys that duplicate the graph, are read only, or are metadata
                continue
            try:
                attr = getattr(obj, key)
                if not callable(attr):
                    result[key] = self.encode_pod(attr) or attr
            except:
                # Dynamic attribute failed evaluation so skip
                pass
        return result

    def encode_pod(self, obj):
        """ Encode object as POD or None if type is not supported. """
        if obj is None:
            return None
        elif isinstance(obj, (bool, float, int, str)):
            return obj
        elif isinstance(obj, (list, tuple)):
            return list(self.default(e) for e in obj)
        elif isinstance(obj, (mathutils.Color, mathutils.Euler, mathutils.Matrix,
                              mathutils.Quaternion, mathutils.Vector)):
            return str(obj)
        elif isinstance(obj, set):
            return str(sorted([self.default(e) for e in obj]))
        elif isinstance(obj, bytes):
            return {'length-bytes': len(obj), 'md5': hashlib.md5(obj).hexdigest()}
        elif self.identity(obj) in self.cycle_detector:
            return {'_identityRef': self.identity(obj)}
        elif isinstance(obj, bpy.types.bpy_struct):
            return self.encode_bpy_struct(obj)
        elif isinstance(obj, bpy.types.bpy_prop_collection):
            return self.encode_bpy_prop_collection(obj)
        elif isinstance(obj, bpy.types.bpy_prop_array):
            return self.encode_bpy_prop_array(obj)
        return None

    def identity(self, obj):
        """ Return a unique id for obj.
        As the Python wrapper objects are short lived, id() does not guarantee
        a deterministic unique id. """
        if hasattr(obj, 'name'):
            return f'{obj.__class__.__qualname__}:{obj.name}'
        elif hasattr(obj, 'as_pointer'):
            the_type = obj.__class__.__qualname__
            by_type = self.pseudo_address.setdefault(the_type, {})
            return f'{the_type}#{by_type.setdefault(obj.as_pointer(), len(by_type))}'
        elif isinstance(obj, (bpy.types.bpy_prop_collection, bpy.types.bpy_prop_array)):
            return 'NO-REFERENCES'
        raise Exception(f'Unexpected object {str(obj)}')


def main():
    """ Write current blendfile to output file given as script argument. """
    argv = sys.argv
    argv = argv[argv.index("--") + 1:]
    output_file = argv[0]

    text = json.dumps(bpy.data, indent=1, sort_keys=True, cls=BlendEncoder)

    handle = open(output_file, 'w')
    handle.write(text)
    handle.close()


main()
