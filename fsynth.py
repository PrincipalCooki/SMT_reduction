#!/usr/bin/python3

from printer import NetworkPrinter, NetworkNode
import sys
import yaml
from typing import Dict, List
from z3 import *

print("Hello, World!")

# Read the specification given via stdin
# Original code: spec = yaml.safe_load(sys.stdin)
#Mein code:

yaml_file_path = "fsynth-1.0/problems/sat_const_bool.yaml"

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

print("Inputs:", inputs)
print("Outputs:", outputs)  
print("Samples:", samples)
print("Depth:", depth)
print("Width:", width)

s = Solver()

# TODO Encode the given specification into SMT constraints

def div0(a, b):
    return If(b == 0, 0, a / b)


# '+', '-', '*', '/', '<', '==', 'and', 'or', 'not', 'id'
#  0 ,  1 ,  2 ,  3 ,  4 ,  5  ,   6  ,  7  ,   8  ,  9   
def apply_op(op, a, b):
    
    if (isinstance(a, BoolRef)):
        return If(op == 6, And(a, b),  
           If(op == 7, Or(a, b), 
           If(op == 8, Not(a), a)))  
    else: 
        return If(op == 0, a + b, 
                If(op == 1, a - b,  
                If(op == 2, a * b,  
                If(op == 3, div0(a, b),  
                If(op == 4, a < b,  
                If(op == 5, a == b,  
                a))))))  


def initialize_layers():
    layers = []
    for d in range(depth):
        layer = []
        for w in range(width):
            op = Int(f'op_{d}_{w}')
            s.add(And(op >= 0, op <= 9)) 
            # operation is fixed, while the numbers change for each sample!
            changing_numbers = []
            for sample_index in range(len(samples)):
                in_0 = Int(f'in0_{d}_{w}_{sample_index}')
                in_1 = Int(f'in1_{d}_{w}_{sample_index}')
                value = Bool(f'value_{d}_{w}_{sample_index}') 
                changing_numbers.append((in_0, in_1, value))
                s.add(value == apply_op(op, in_0, in_1))
            layer.append((op, changing_numbers))
        layers.append(layer)

    return layers


def find_operation(equations):
    """
    Findet die Operation `op`, die für alle Gleichungen aus `equations` gültig ist.
    :param equations: Liste von Tupeln (a, b, result), die die Gleichungen repräsentieren.
    """
    s = Solver()

    # Symbolische Variable für die Operation
    op = Int('op')
    s.add(And(op >= 0, op <= 9))  # Gültige Operationen

    # Dynamisch Bedingungen für jede Gleichung hinzufügen
    for i, (a_val, b_val, result_val) in enumerate(equations):
        a = Int(f'a_{i}')
        b = Int(f'b_{i}')
        result = Bool(f'result_{i}')

        # Setze die Werte für a, b und result
        s.add(a == a_val)
        s.add(b == b_val)
        s.add(result == result_val)

        # Verknüpfe result mit apply_op
        s.add(result == apply_op(op, a, b))

    # Solver ausführen
    if s.check() == sat:
        model = s.model()
        return model[op].as_long()
    else:
        return None  # Keine Lösung gefunden

# Beispiel: Dynamische Gleichungen
equations = [
    (0, 0, True),  # 2 # 4 = 8
    (1, 1, True),  # 5 # 10 = 50
    (2, 2, True)  # 3 # 3 = 9
]

# Operation herausfinden
operation = find_operation(equations)
if operation is not None:
    print(f"Gefundene Operation: {operation}")
else:
    print("Keine Operation erfüllt alle Bedingungen.")
 


 
layers = initialize_layers()

input_vars = list()
output_vars = list()

# Initialize input and output variables
for sample_index, sample in  enumerate(samples):
    input_dicts = dict()   
    for name, value in inputs.items():
        if value == 'int':
            print("Int add: ", f"{name}_{sample_index}")
            input_dicts[name] = Int(f"{name}_{sample_index}")
        else:
            input_dicts[name] = Bool(f"{name}_{sample_index}")
    input_vars.append(input_dicts)

            
for sample_index, sample in  enumerate(samples):
    output_dicts = dict()
    for name, z3_type in outputs.items():   
        if z3_type == 'int':
            output_dicts[name] = Int(f"{name}_{sample_index}")
        else:
            print("Bool add: ", f"{name}_{sample_index}")
            output_dicts[name] = Bool(f"{name}_{sample_index}")
    output_vars.append(output_dicts)
    
# Connect samples to input and output variables 
for sample_index, sample in  enumerate(samples):
    for name, value in sample.items():
        if name in inputs:
            print("Input name found:", name, value)
            s.add(input_vars[sample_index][name] == value)
        elif name in outputs:
            s.add(output_vars[sample_index][name] == value)

# Geniale funktion!!!! frfr
# da alle einträge außer der ausgewählten 0 sind, regelt die summe den rest
def select_value(input_values, index):
    n = len(input_values)  
    return Sum([If(index == i, input_values[i], 0) for i in range(n)])

# Connect inputs to the first layer
for sample_index, sample_dict in enumerate(input_vars):
    
    for w, (op, changing_numbers) in enumerate(layers[0]):
    
        for (in_0, in_1, value) in changing_numbers:
        #    s.add(in_0 == sample_value)
            s.add(Or([in_0 == i for i in range(len(input_vars))]))
            s.add(in_0 == input_vars[0]["n"])
            s.add(in_1 == input_vars[0]["n"])
        # print([in_0 == i for i in range(len(input_vars))])
        # print([in_1 == i for i in range(len(input_vars))])
        # s.add(Or([in_0 == i for i in range(len(input_vars))])) 
        # s.add(Or([in_1 == i for i in range(len(input_vars))]))
        # s.add(in_0 == 20)
        # s.add(in_1 == 20)
        
global_op = Int('global_op')    
# connect the layers
for d in range(len(layers)):
    layer = layers[d]
    for w in range(len(layer)):
        op, changing_numbers = layer[w]
        s.add(global_op == op)
        for sample_index, (in_0, in_1, value) in enumerate(changing_numbers):
            if d == 0:
                continue
            else:
                input_values = []
                for prev_layer in layers[d - 1]:
                    input_values.append(prev_layer[0][1][sample_index][2]) #0 is width 1 is changing numbers, 2 is the value
            print("input values", input_values)
            print("select value in0", select_value(input_values, in_0))
            print("select value in1", select_value(input_values, in_1))
            # s.add(in_0 == select_value(input_values, in_0))
            
            # s.add(in_1 == select_value(input_values, in_0))


# last layer
# global_op = Int('global_op')      
# for w, (op, changing_numbers) in enumerate(layers[-1]):
#     s.add(global_op == op)
#     for (in_0, in_1, value) in changing_numbers:
#         s.add(value == output_vars[0]["f"])
     
# last layer alternative
# layer[depth][width][op, changing_numbers][in_0, in_1, value][sample_index]
for output_dict in output_vars:
    for name, var in output_dict.items():
        print("Output:", name, var)
        print("Output:", layers[-1][0][1][-1][-1])
        s.add(var == layers[-1][0][1][-1][-1])

print(s.to_smt2())

if s.check() == sat:
    model = s.model()
    print(f"Gefundene Operation: {model[global_op]}")
    print("YEAHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH")
else:
    print("Nooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo.")

    

layers = initialize_layers()

# Connect inputs to the first layer
for w, (op, in_0, in_1, value) in enumerate(layers[0]):
    s.add(Or([in_0 == i for i in range(len(input_vars))])) 
    s.add(Or([in_1 == i for i in range(len(input_vars))]))


def select_value(input_values, index):
    n = len(input_values)  # Anzahl der Eingaben
    return Sum([If(index == i, input_values[i], 0) for i in range(n)])


# Apply constraints layer by layer
for d, layer in enumerate(layers):
    print(f"Schicht {d}:")
    for w, (op, in_0, in_1, value) in enumerate(layer):
        input_values = (
            [input_vars[name] for name in input_vars] if d == 0 else [l[3] for l in layers[d - 1]]
        )
        s.add(value == apply_op(op, select_value(input_values, in_0), select_value(input_values, in_1)))        
        print(f"Layer {d}, Node {w}: op={op}, in_0={in_0}, in_1={in_1}, value={value}")
        print(f"Input Values: {input_values}")
        # print(f"Constraint: {value == apply_op(op, select_value(input_values, in_0), select_value(input_values, in_1))}")



# Connect the last layer to the outputs
for name, var in output_vars.items():
    print("Output:", name, var)
    print("Layer:", layers[-1])
    s.add(var == layers[-1][0][3])
    print(f"Layer {d}, Node {w}, op={op}, in_0={in_0}, in_1={in_1}, value={value}")
    print("Input Values for this layer:", input_values)


for sample in samples:
    for name, value in sample.items():
        if name in input_vars:
            s.add(input_vars[name] == value)
        elif name in output_vars:
            s.add(output_vars[name] == value)


ans = s.check()

if ans == sat:
    # There exists a model => function is realizable
    model = s.model()
    output_printer.set_realizable(True)
    # TODO synthesize the function given the SMT model

    print("Model:")
    print(model)

    output_printer.set_node(0, 0, NetworkNode("=", "n", "n"))
    
    output_printer.set_output("f", 0)

    # Set nodes like this:
    # output_printer.set_node(i, j, NetworkNode(op, in_0, in_1))
    # Set outputs like this:
    # output_printer.set_output(output_name, output_index)
    
else:
    # Function is not realizable
    output_printer.set_realizable(False)

output_printer.print()


