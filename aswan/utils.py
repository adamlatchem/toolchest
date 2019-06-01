""" Low level Utilities. """
import select
import sys
import os


def bytes_to_unicode_records(byte_string, delimiter, encoding):
    """ Convert a byte string to a tuple containing an array of unicode
    records and any remainder to be used as a prefix next time. """
    string = byte_string.decode(encoding)
    records = string.split(delimiter)
    return (records[:-1], records[-1].encode(encoding))


def read_available_bytes(file=sys.stdin, chunk_size=4096):
    """ Read all available data from f in chucks of chunk_size returning a byte
    array or None if nothing read. """
    buffer = b''
    while True:
        read_list, _, exception_list = select.select([file], [], [file], 0)
        if file in exception_list:
            print('stdin error')
            break
        if file in read_list:
            chunk = os.read(file.fileno(), chunk_size)
            if chunk == b'':
                break
            buffer += chunk
        else:
            break
    return buffer
