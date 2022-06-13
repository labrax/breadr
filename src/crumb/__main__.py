
import sys
import argparse

import settings as settings

def main():
    parser = argparse.ArgumentParser(prog='breadr', usage='%(prog)s [options]')
    parser.add_argument('show', type=str, help='displays information about a slice file')
    parser.add_argument('run', type=str, help='executes a slice file')
    parser.parse_args(args=None if sys.argv[1:] else ['--help'])

if __name__ == '__main__':
    main()