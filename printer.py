from collections import namedtuple
from typing import Dict, List
import yaml
import sys

"""
NetworkNode represents a single node in the network with a concrete operation and two inputs:
    op: The operation of the node (one of '+', '-', '*', '/', '=', '<', 'id', 'and', 'or', 'not')
    in_0: The first input to the node (String for the first layer otherwise an integer)
    in_1: The second input to the node (String for the first layer otherwise an integer)
"""
NetworkNode = namedtuple('NetworkNode', ['op', 'in_0', 'in_1'])

class NetworkPrinter:
    """
    Allows the printing of a network in the required output format
    """
    def __init__(self, depth : int, width : int, outputs : Dict[str, str]):
        """
        Initializes the network printer
        :param depth: The depth of the network
        :param width: The width of the network
        :param outputs: A dictionary of output names to output types
        """
        self.depth = depth
        self.width = width
        self.realizable = None
        self.nodes = [ [None]*self.width for _ in range(self.depth) ]
        self.outputs = { cur_out[0] : None for cur_out in outputs.items()}

    def set_realizable(self, realizable : bool):
        """
        Sets whether the network is realizable
        :param realizable: Whether the network is realizable
        """
        self.realizable = realizable

    def set_node(self, depth : int, width : int, node : NetworkNode):
        """
        Sets a node in the network
        :param depth: The depth position of the node (i.e. the layer)
        :param width: The width position of the node (i.e. the index in the layer)
        :param node: The node to set: Use NetworkNode(op, in_0, in_1)
        """
        assert depth < self.depth, f"Tried to set node at depth {depth} but max depth is {self.width}"
        assert width < self.width, f"Tried to set node at width {width} but max width is {self.width}"
        assert self.nodes[depth][width] is None, f"Tried to set node at ({depth}, {width}) but it is already set"
        if depth == 0:
            assert type(node.in_0) is str, f"Tried to set node at ({depth}, {width}) but in_0 ({node.in_0}) is not an input variable"
            assert type(node.in_1) is str or node.in_1 is None, f"Tried to set node at ({depth}, {width}) but in_1 ({node.in_1}) is not an input variable"
        else:
            assert type(node.in_0) is int, f"Tried to set node at ({depth}, {width}) but in_0 ({node.in_0}) is not an int"
            assert node.in_0 < self.width, f"Tried to set node at ({depth}, {width}) but in_0 ({node.in_0}) is not less than width"
            assert type(node.in_1) is int or node.in_1 is None, f"Tried to set node at ({depth}, {width}) but in_1 ({node.in_1}) is not an int"
            assert node.in_1 is None or node.in_1 < self.width, f"Tried to set node at ({depth}, {width}) but in_1 ({node.in_1}) is not less than width"
        assert node.op in ['+', '-', '*', '/', '=', '<', 'id', 'and', 'or', 'not'], f"Tried to set node at ({depth}, {width}) but op ({node.op}) is not a valid op"

        self.nodes[depth][width] = node

    def set_output(self, output : str, value : int):
        """
        Sets an output in the network
        :param output: The name of the output
        :param value: The node index of the last layer
        """
        assert output in self.outputs, f"Tried to set output {output} but it is not in the output list"
        assert self.outputs[output] is None, f"Tried to set output {output} but it is already set"
        assert value < self.width, f"Tried to set output {output} but value {value} is not less than width"
        self.outputs[output] = value

    def print(self):
        """
        Prints the network in the required output format
        """
        assert self.realizable is not None, "Tried to print but realizable is not set"
        if self.realizable:
            # Unwrap named tuples
            output_layers = [list(filter(lambda x: x != None,map(lambda n: {"op": n.op, "in_0": n.in_0, "in_1": n.in_1} if n is not None else None, layer))) for layer in self.nodes]
            result = {
                "layers": output_layers,
                "emitted" : self.outputs,
                'not_realizable': False
            }
        else:
            result = { 'not_realizable': True }

        print("# network")
        yaml.dump(result, sys.stdout)
        print("# end_network")
