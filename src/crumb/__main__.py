"""Breadr main executer"""
from multiprocessing.sharedctypes import Value
import sys
import argparse
import json
import pprint

from .settings import Settings
from .bakery_items.slice import Slice


def main():
    """Main function"""
    parser = argparse.ArgumentParser(prog='breadr', usage='%(prog)s [options]')
    parser.add_argument('file', type=str, help='Slice file')
    parser.add_argument('-show', help='displays information about a slice file', action='store_true')
    parser.add_argument('-run', help='executes a slice file', action='store_true')
    parser.add_argument('-input', type=str, help='set input parameters, use comma separated values with equals')
    parser.add_argument('-setting', type=str, help='set some settings, use comma separated values with equals')
    arguments = parser.parse_args(args=None if sys.argv[1:] else ['--help'])

    # set settings before running
    if arguments.setting:
        for i in arguments.setting.split(','):
            setting, value = i.split('=')
            Settings.set_setting(setting, value)
    # load the file and show some info
    if arguments.show:
        with open(arguments.file, mode='r', encoding='utf-8') as open_file:
            pprint.pprint(json.loads(open_file.read()))
    # compile input bits, split , then split =
    input = {}
    if arguments.input:
        for i in arguments.input.split(','):
            this_input, value = i.split('=')
            input[this_input] = value
    # show time!
    if arguments.run:
        slice = Slice('main_exec')
        slice.load_from_file(arguments.file)
        for slice_input, value in input.items():
            if slice_input in slice.input:
                type = slice.input[slice_input]
                try:
                    input[slice_input] = type(input[slice_input])
                except ValueError as exc:
                    raise ValueError(f'Invalid type for "{slice_input}", expected "{type.__name__}".') from exc
        ret = slice.run(input)
        pprint.pprint(ret)


if __name__ == '__main__':
    main()
