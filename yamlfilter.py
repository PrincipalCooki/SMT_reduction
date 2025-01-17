#!/usr/bin/python3
"""This scripts reads yaml file on stdin, removes the result field, and dumps the yaml back to stdout.
"""

import yaml, sys

if __name__ == '__main__':
    spec = yaml.safe_load(sys.stdin)

    if 'result' in spec:
        del spec['result']

    yaml.safe_dump(spec, sys.stdout)
