#!/usr/bin/python3

from io import StringIO
import argparse
import tempfile
import subprocess
import time
from pathlib import Path
import yaml

NOT_REALIZABLE = 'not realizable'


def findsize(filename: Path, ns: argparse.Namespace):
    width = ns.width
    for depth in range(1, ns.depth):
        print("Depth: ", depth, "Width:", width)
        suc = validate(filename, width, depth, ns.fsynth)
        if suc:
            print("Found solution with depth:", depth, "Descrease width")
            last_working_width = width
            try_width = last_working_width/2
            while last_working_width != try_width:
                suc = validate(filename, try_width, depth, ns.fsynth)
                if suc:
                    last_working_width = try_width
                    try_width = int( last_working_width/2 )
                else:
                    try_width = int( (try_width + last_working_width)/2 )

            print(f"size found {filename} with width:{try_width} and depth:{depth}")
            update(filename, try_width, depth)


def update(filename: Path, w: int, d: int, target: Path = None):
    with filename.open() as fp:
        data = yaml.safe_load(fp)

    data["width"] = w
    data["depth"] = d
    s = StringIO()
    yaml.safe_dump(data, s)

    if target is None:
        target = filename

    with target.open('w') as fp:
        fp.write(s.getvalue())



def validate(filename: Path, width: int, depth: int, fsynth: str):
    fsynth = Path(fsynth).absolute()


    tmp = Path(tempfile.mktemp(".yaml", "fsynth_input"))
    update(filename, width, depth, target=tmp)

    cli = f"cat {tmp.absolute()} | python3 {fsynth} | tail -n 1"
    print("Execute: ", cli)
    start = time.process_time()
    status, out = subprocess.getstatusoutput(cli)
    stop = time.process_time()
    print(f"Test {filename} w:{width} d:{depth} in {stop-start} ms")

    if status != 0:
        return False

    print("Solution: ", out)

    return out != NOT_REALIZABLE





# def check(filename, last_line):
#     global SUCCESS, FAILURE
#     last_line = last_line.strip()
#     import z3
#     with open(filename) as fh:
#         spec = yaml.safe_load(fh)
#     result: str = spec['result']

#     if result == NOT_REALIZABLE:
#         if last_line == NOT_REALIZABLE:
#             SUCCESS += 1
#         else:
#             FAILURE += 1
#         return
#     elif last_line == NOT_REALIZABLE:
#         FAILURE += 1
#         return

#     smt = io.StringIO()
#     for x, t in list(spec['inputs'].items()) + list(spec['outputs'].items()):
#         type = t.capitalize()
#         smt.write(f"(declare-const {x} {type})\n")

#     smt.write(f"(assert (not (= {result} {last_line})))")

#     # SMT test
#     # print(smt.getvalue())

#     s = z3.Solver()
#     s.from_string(smt.getvalue())
#     ans = s.check()
#     print("Result: ", ans)
#     if ans == z3.unsat:
#         SUCCESS += 1
#     else:
#         print("Model:", s.model())
#         FAILURE += 1


if __name__ == '__main__':
    cli_parser = argparse.ArgumentParser("findsize.py",
                                         description="""This scripts finds the minimum width and depth for a given circuit.""")
    cli_parser.add_argument("--fsynth", help="path to the fsynth.py", default="fsynth.py")
    cli_parser.add_argument("--width", help="maximal width", metavar="INT", type=int, default=10)
    cli_parser.add_argument("--depth", help="maximal depth", metavar="INT", type=int, default=10)
    cli_parser.add_argument("files", action='append', help="YAML files", metavar="FILENAME")

    ns = cli_parser.parse_args()

    for fil in ns.files:
        findsize(Path(fil), ns)
