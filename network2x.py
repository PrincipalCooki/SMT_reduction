#!/usr/bin/python3
import argparse
import io
import re
import sys

import yaml


def read_network(stream):
    re_start = re.compile(r"#\s*network")
    re_stop = re.compile(r"#\s*end_network")

    s = io.StringIO()
    lines = iter(stream)
    catch = False
    for line in lines:
        if re_start.match(line):
            catch = True
            continue

        if re_stop.match(line):
            if catch: break
            catch = False

        if catch:
            s.write(line)

    if s.tell() == 0:
        print("network2x: Could not find any network directive in the given input. ", file=sys.stderr)
        sys.exit(10)

    s.seek(0)
    return yaml.safe_load(s)


cli_parser = argparse.ArgumentParser("network2x.py",
                                     description="""Convert a network to dot or SMTlib""")

cli_parser.add_argument("--to-dot", action="store_true", help="outputs Graphviz format of the network")
cli_parser.add_argument("--to-smt", action="store_true", help="outputs SMTlib expression representing the network")

cli_parser.add_argument("--max-width", action="store", help="if set checks the width of the network")
cli_parser.add_argument("--max-depth", action="store", help="if set checks the depth of the network")

cli_parser.add_argument("file", default="-", action="store", help="YAML file of the network. Omitting: sys.stdin")


def to_dot(network):
    def get_source(source, lidx):
        if source is None:
            return None
        elif isinstance(source, int):
            return f"node_{lidx - 1}_{source}"
        else:
            n = f"node_{source}"
            if n not in nodes:
                print(f"{n} [label=\"IN: {source}\",shape=circle,color=red,fontcolor=white,style=filled,fillcolor=red]")
                nodes.add(n)
            return n

    print("digraph G {")
    print("graph [rankdir = LR, splines=ortho];")
    nodes = set()  # catch printed input nodes

    for lidx, layer in enumerate(network['layers']):
        for nidx, node in enumerate(layer):
            operation = node['op']
            self_node = f"node_{lidx}_{nidx}"
            print(f"node_{lidx}_{nidx} [label=\"{operation}\", shape=rectangle]")
            prev_node_a = get_source(node['in_0'], lidx)
            prev_node_b = get_source(node['in_1'], lidx)
            if prev_node_a:
                print(f"{prev_node_a}-> {self_node} [label=\"0\"]")
            if prev_node_b:
                print(f"{prev_node_b}-> {self_node} [label=\"1\"]")

    lidx = len(network['layers']) - 1
    for k, nidx in network['emitted'].items():
        print(f"node_{k} [label=\"Out: {k}\",shape=diamond,color=blue,fontcolor=white,style=filled,fillcolor=blue]")
        print(f"node_{lidx}_{nidx} -> node_{k}")

    print("}")


def to_smt(network):
    exprs = dict()

    def get_input(source, lidx):
        if source is None:
            return None
        elif isinstance(source, int):
            n = f"node_{lidx - 1}_{source}"
            return exprs[n]
        else:
            return source

    def smtop(op):
        match op:
            case '/':
                return 'div0'
            case _:
                return op

    for lidx, layer in enumerate(network['layers']):
        for nidx, node in enumerate(layer):
            self_node = f"node_{lidx}_{nidx}"
            op = smtop(node['op'])
            seq = (op,
                   get_input(node['in_0'], lidx),
                   get_input(node['in_1'], lidx))
            seq = filter(lambda x: x is not None, seq)
            if op == 'id': # skip identity
                exprs[self_node] = list(seq)[1]
            else:
                exprs[self_node] = "(" + ' '.join(seq) + ")"
    lidx = len(network['layers'])
    eq = []
    for k, nidx in network['emitted'].items():
        self_node = get_input(nidx, lidx)
        eq.append(f"(= {k} {self_node})")

    print("(and " + ' '.join(eq) + ")")


def check_inputs(network):
    for node in network['layers'][0]:
        A = node['in_0']
        B = node['in_1']
        if A is not None and isinstance(node['in_0'], int) or\
                B is not None and isinstance(node['in_1'], int):
            print("network2x: First layer can only access input variables. Node=", node)
            sys.exit(6)

    for layer in network['layers'][1:]:  # forget first layer
        for node in layer:
            A = node['in_0']
            B = node['in_1']
            if (A is not None and not isinstance(A, int)) \
                    or (B is not None and not isinstance(node['in_1'], int)):
                print("network2x: Only the first layer is allowed to access input values")
                sys.exit(7)

    last_layer_width = len(network['layers'][-1])
    for k, v in network['emitted'].items():
        if not (0 <= v < last_layer_width):
            print(f"network2x: Output {k} refers to non-existent node {v}.")
            sys.exit(5)


if __name__ == '__main__':
    args = cli_parser.parse_args()

    if args.file is not None and args.file != '-':
        with open(args.file) as fp:
            network = read_network(fp)
    else:
        network = read_network(sys.stdin)

    if network.get('not_realizable', False):
        print("not realizable")
        sys.exit(0)

    if args.max_depth:
        depth = len(network['layers'])
        if depth > args.max_depth:
            print(f"network2x: Given network is deeper {depth} than allowed {args.max_depth}")
            sys.exit(9)

    if args.max_width:
        width = max(map(len, network['layers']))
        if width > args.max_width:
            print(f"network2x: Given network is wider {width} than allowed {args.max_width}")
            sys.exit(8)

    check_inputs(network)

    if args.to_smt:
        to_smt(network)
    else:
        to_dot(network)
