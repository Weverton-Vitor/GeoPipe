import glob
import os
import pickle
import re
from PyQt5.QtCore import QByteArray

class NodeRepresentation:
    def __init__(self, name, label="", parameters=[]):
        self.name = name
        self.parameters = parameters
        self.label = label

    def __str__(self):
        output = f"Node: {self.name}\nParameters: \n"
        for parameter in self.parameters:
            output += f"\t{parameter}\n"

        return output

    def add_parameter(self, parameter):
        self.parameters.append(parameter)

    def to_qbytearray(self):
        return QByteArray(pickle.dumps(self))

    @staticmethod
    def from_qbytearray(qbytearray):
        return pickle.loads(qbytearray.data())

def find_all_nodes(project_path):
    """Procura por todos os arquivos 'nodes.py' e extrai os nomes das funções dentro deles."""
    path_nodes = glob.glob(os.path.join(f'{project_path}', "**", "nodes.py"), recursive=True)
    nodes = []

    for node in path_nodes:
        with open(node, "r", encoding="utf-8") as file:
          content = file.read()

        # Regex para capturar funções definidas
        functions = re.findall(r"def (\w+)\s*\(([^)]*)\):", content)

        for function_text in functions:
            node_name = function_text[0]

            parameters = function_text[1].split(',')
            parameters = list(map(lambda x: x.replace('\n', ''), parameters))
            parameters = list(map(lambda x: x.strip(), parameters))

            nodes.append(NodeRepresentation(name=node_name, parameters=parameters))


    return nodes
