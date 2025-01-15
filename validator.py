#!/usr/bin/python3

import argparse
import io
import subprocess
import time
from pathlib import Path
from statistics import mean, stdev, median
import z3

import yaml

# STATISTICS
ERRORS = 0
SUCCESS = 0
FAILURE = 0
TIMINGS = []


def validate(filename: Path, ns: argparse.Namespace):
    global ERRORS, SUCCESS, FAILURE, TIMINGS

    with filename.open() as fp:
        spec = yaml.safe_load(fp)
        depth = spec['depth']
        width = spec['width']

    fsynth = Path(ns.fsynth).absolute()
    fsynth_prefix = ns.fsynth_prefix
    pre_filter = ns.pre_filter
    post_filter = ns.post_filter

    n2x = (Path(__file__).parent / "network2x.py").absolute()

    cli = f"cat {filename.absolute()} | {pre_filter} | {fsynth_prefix} python3 {fsynth} " \
          f"| python3 {n2x} --to-smt --max-width {width} --max-depth {depth} -"
    print("Execute: ", cli)
    start = time.process_time()
    status, out = subprocess.getstatusoutput(cli)
    stop = time.process_time()

    if status != 0:
        print("Terminated with status code: ", status)
        print("Output:", out)
        ERRORS = ERRORS + 1
        return

    print("Took: ", stop - start, "ms")
    TIMINGS.append(stop - start)

    print("Solution: ", out)
    check(spec, out)


NOT_REALIZABLE = "not realizable"


def check(spec, last_line, use_result=False):
    global SUCCESS, FAILURE
    last_line = last_line.strip()

    result: str = spec["result"]

    if result == NOT_REALIZABLE:
        if last_line == NOT_REALIZABLE:
            SUCCESS += 1
        else:
            FAILURE += 1
        return
    elif last_line == NOT_REALIZABLE:
        FAILURE += 1
        return

    if use_result:
        check_by_result(result, last_line, spec)
    else:
        check_by_samples(last_line, spec)


def check_by_samples(last_line: str, spec):
    global SUCCESS, FAILURE
    samples = spec["samples"]

    def make_var(x, t):
        if t == "int":
            return z3.Int(x)
        elif t == "bool":
            return z3.Bool(x)

    def py_value(x):
        if x.is_int():
            return int(str(x))
        elif x.is_bool():
            return "true" == str(x)

    inputs = {x: make_var(x, t) for x, t in spec["inputs"].items()}
    outputs = {x: make_var(x, t) for x, t in spec["outputs"].items()}
    all = {}
    all.update(inputs)
    all.update(outputs)

    s = z3.Solver()
    eq = z3.parse_smt2_string(f"(assert {last_line})", sorts={}, decls=all)
    s.add(eq)

    for sample in samples:
        assum = [var == sample[k] for k, var in inputs.items()]
        ans = s.check(assum)
        if ans == z3.sat:
            m = s.model()
            actual = {x: py_value(m[d]) for x, d in all.items()}
            error = [actual[k] != v for k, v in sample.items()]
            # print(f"Tested against {len(error)} samples: {error}")
            if any(error):
                FAILURE += 1
                return
        else:
            print("Applied sample with inputs:", assum, f" but receive {ans}!")
            FAILURE += 1
            return
    SUCCESS += 1


def check_by_result(result: str, last_line: str, spec):
    global SUCCESS, FAILURE

    smt = io.StringIO()
    for x, t in list(spec["inputs"].items()) + list(spec["outputs"].items()):
        type = t.capitalize()
        smt.write(f"(declare-const {x} {type})\n")
        smt.write(f"(assert (not (= {result} {last_line})))")

        # SMT test
        # print(smt.getvalue())

    s = z3.Solver()
    s.from_string(smt.getvalue())
    ans = s.check()
    print("Result: ", ans)
    if ans == z3.unsat:
        SUCCESS += 1
    else:
        print("Model:", s.model())
        FAILURE += 1


if __name__ == "__main__":
    cli_parser = argparse.ArgumentParser(
        "validator.py",
        description="""This scripts validates a given solution against a set of function specifications.""",
    )
    cli_parser.add_argument(
        "--fsynth", help="path to the fsynth.py", metavar="fsynth.py"
    )
    cli_parser.add_argument(
        "--fsynth-prefix",
        help="programs to sandbox fsynth",
        metavar="commands",
        default="",
    )
    cli_parser.add_argument(
        "--pre-filter",
        help="Command or script to filter the YAML input",
        metavar="command",
        default="cat",
    )
    cli_parser.add_argument(
        "--post-filter",
        help="Command that is applied to the stdout of fsynth. Use it for network2x",
        metavar="COMMAND",
        default="python3 network2x.py --to-smt -"
    )

    cli_parser.add_argument(
        "-r",
        "--result",
        help="Use the result field for validation check, otherwise just use the samples.",
    )
    cli_parser.add_argument(
        "files", action="append", help="YAML files", metavar="FILENAME"
    )

    ns = cli_parser.parse_args()

    for fil in ns.files:
        validate(Path(fil), ns)

    print("Statistics:")
    print("ERRORS:", ERRORS)
    print("SUCCESS:", SUCCESS)
    print("FAILURE:", FAILURE)
    if len(TIMINGS) > 1:
        print(f"Timings: mean={mean(TIMINGS)} std={stdev(TIMINGS)} median={median(TIMINGS)}")

