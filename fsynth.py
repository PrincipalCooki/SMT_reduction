#!/usr/bin/python3

from printer import NetworkPrinter, NetworkNode
import sys
import yaml
from typing import Dict, List
from z3 import *

# Read the specification given via stdin
# spec = yaml.safe_load(sys.stdin)
#Mein code:

yaml_file_path = "problems/sat_const_bool.yaml"

# YAML-Datei laden
try:
    with open(yaml_file_path, "r") as file:
        spec = yaml.safe_load(file)
except FileNotFoundError:
    print(f"Fehler: Datei '{yaml_file_path}' nicht gefunden.", file=sys.stderr)
    sys.exit(1)
except yaml.YAMLError as e:
    print(f"Fehler beim Laden der YAML-Datei: {e}", file=sys.stderr)
    sys.exit(1)

inputs: Dict[str, str] = spec['inputs']
outputs: Dict[str, str] = spec['outputs']
samples: List[Dict[str, str]] = spec['samples']
depth = int(spec['depth'])
width = int(spec['width'])

output_printer = NetworkPrinter(depth, width, outputs)

s = Solver()

# TODO Encode the given specification into SMT constraints

def div0(a, b):
    return If(b == 0, 0, a / b)

# '+', '-', '*', '/', 'id  '<', '==', 'and', 'or', 'not', 'id'
#  0 ,  1 ,  2 ,  3 ,  4 ,  5 ,   6  ,  7  ,   8  ,  9  , 10
# optype = True: optype is int, otherwise bool 
def apply_op(op, a, b):
    
    return If(op == 0, a + b, 
                If(op == 1, a - b,  
                If(op == 2, a * b,  
                If(op == 3, div0(a, b),  
                If(op == 4, a ,   
                If(op == 5, a < b,  
                If(op == 6, a == b,  
                If(op == 7, a*b,  # And
                If(op == 8, (a+b) - (a*b), # Or
                If(op == 9, 1 - a, a)))))))))) # Not            


def initialize_layers():
    layers = []
    for d in range(depth):
        layer = []
        for w in range(width):
            op = Int(f'op_{d}_{w}')
            optype = Bool(f'optype_{d}_{w}')
            s.add(And(op >= 0, op <= 10)) 
            # optype is the type of the output, True means Int output
            s.add(optype == If(op <= 4, True, False)) # TODO identity does not work 
            in_0 = Int(f'in0_{d}_{w}')
            in_1 = Int(f'in1_{d}_{w}')
            out = Int(f'out_{d}_{w}')
            # operation is fixed, while the output changes for each sample!
            values = []
            for i in range(len(samples)):
                values.append(Int(f'value_{d}_{w}_{i}'))
            layer.append((op, optype, in_0, in_1, values))
        layers.append(layer)

    return layers

# Geniale funktion!!!! frfr
# da alle einträge außer der ausgewählten 0 sind, regelt die summe den rest
# TODO every indix is only allowed once 
def select_value(input_values, index):
    n = len(input_values)  
    s.add(index < n)
    s.add(index >= 0)
    return Sum([If(index == i, input_values[i], 0) for i in range(n)])

def select_value_bool(input_values, index):
    n = len(input_values)
    s.add(index < n)
    s.add(index >= 0)
    return Or([And(index == i, input_values[i]) for i in range(n)])
 
layers = initialize_layers()

input_vars = list()
output_vars = list()

input_vars = {name: Int(name) for name, dtype in inputs.items()}
output_vars = {name: Int(name) for name, dtype in outputs.items()}
# input_vars = {name: Int(name) if dtype == 'int' else Bool(name) for name, dtype in inputs.items()}
# output_vars = {name: Int(name) if dtype == 'int' else Bool(name) for name, dtype in outputs.items()}
# print("input varts: ", input_vars)

# Connect inputs to the first layer
for w, (op, optype, in_0, in_1, values) in enumerate(layers[0]):
    s.add(Or([in_0 == i for i in range(len(input_vars))])) 
    s.add(Or([in_1 == i for i in range(len(input_vars))]))


for d in range(len(layers)):
    layer = layers[d]
    for w, (op, optype, in_0, in_1, values) in enumerate(layer):
        for i, sample in enumerate(samples):
            # print("Sample: ", sample)

            if d == 0:
                input_values = []
                for input_vars_index, name in enumerate(input_vars):
                    input_values.append(sample[name])
                    # falls intput int ist wähle eine inputtype int operation aus

                    if inputs[name] == 'int':
                        s.add(If(in_0 == input_vars_index, op <= 6, True))
                        s.add(If(in_1 == input_vars_index, op <= 6, True))
                    else:
                        s.add(If(in_0 == input_vars_index, op > 6, True))
                        s.add(If(in_1 == input_vars_index, op > 6, True))
            else:
                input_values = []
                for block_index, prev_block in enumerate(layers[d - 1]):
                    (op_prev, optype_prev, in_0_prev, in_1_prev, values_prev) = prev_block
                    input_values.append(values_prev[i])

                    s.add(If(in_0 == block_index, If(optype_prev, op <= 6, op > 6), True))
                    s.add(If(in_1 == block_index, If(optype_prev, op <= 6, op > 6), True))

            s.add(values[i] == apply_op(op, select_value(input_values, in_0), select_value(input_values, in_1)))


# add constraints to output

possible_outputs = []
for (op, optype, in_0, in_1, values) in layers[-1]:
    possible_outputs.append(values)

last_optypes = []
for (op, optype, in_0, in_1, values) in layers[-1]:
    last_optypes.append(optype)

for i, sample in enumerate(samples):
    for name in output_vars:
        output_index = Int(f'output_index_{name}')

        s.add(sample[name] == select_value([row[i] for row in possible_outputs], output_index))
        if outputs[name] == 'int':
            s.add(select_value_bool(last_optypes, output_index))
        else:
            s.add(Not(select_value_bool(last_optypes, output_index)))
        
# print(s.to_smt2())
ans = s.check()

op_sign = ['+', '-', '*', '/', 'id', '<', '=', 'and', 'or', 'not', 'id']

if ans == sat:
    # There exists a model => function is realizable
    model = s.model()
    output_printer.set_realizable(True)
    # TODO synthesize the function given the SMT model

    for w, (op, optype, in_0, in_1, values) in enumerate(layers[0]):
        name0 = next((name for i, name in enumerate(input_vars) if i == model[in_0].as_long()), "")
        name1 = next((name for i, name in enumerate(input_vars) if i == model[in_1].as_long()), "")
        
        node = NetworkNode(op_sign[model[op].as_long()], name0, name1)
        output_printer.set_node(0, w, node)

    for d, layer in enumerate(layers[1:], start = 1):
        for w, (op, optype, in_0, in_1, values) in enumerate(layer):
            node = NetworkNode(op_sign[model[op].as_long()],  model[in_0].as_long(),  model[in_1].as_long())
            output_printer.set_node(d, w, node)

    for i, name in enumerate(output_vars):
        output_index = Int(f'output_index_{name}')
        model_output_index = model[output_index].as_long()
        output_printer.set_output(name, model_output_index)

    # output_printer.set_output("f", 0)

    # Set nodes like this:
    # output_printer.set_node(i, j, NetworkNode(op, in_0, in_1))
    # Set outputs like this:
    # output_printer.set_output(output_name, output_index)
    
else:
    # Function is not realizable
    output_printer.set_realizable(False)

output_printer.print()
