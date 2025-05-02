import glob
import os
import pickle
import re
from PyQt5.QtCore import QByteArray

params_labels = {
        "color_file_log_path": "Diretório de logs da remoção de nuvens",
        "cloud_removal_log": "Diretório de logs da remoção de nuvens",
        "save_clean_images_path": "Diretório de imagens limpas",
        "save_masks_path": "Diretório de máscaras",
        "save_plots_path": "Diretório de gráficos",
        "location_name": "Nome do local",
        "init_date": "Data inicial",
        "final_date": "Data final",
        "dowload_path": "Diretório de download",
        "roi": "Região de interesse (Shapefile)",
        "collection_ids": "ID das coleções",
        "prefix_images_name": "Prefixo do nome das imagens",
        "selected_bands": "Bandas selecionadas",
        "scale": "Escala (em metros)",
        "skip_download": "Pular download",
        "canny_output_save_path": "Diretório de saída do Canny",
        "cfmask_output_save_path": "Diretório de saída do CFMask",
        "images_path": "Diretório de imagens",
        "sigma": "Sigma para o Canny",
        "lower_factor": "Fator inferior para o Canny",
        "upper_factor": "Fator superior para o Canny",
        "boa_path": "Caminho do BOA (Bottom of Atmosphere)",
        "toa_path": "Caminho do TOA (Top of Atmosphere)",
        "toa_dowload_path": "Caminho de Download do TOA (Top of Atmosphere)",
        "boa_dowload_path": "Caminho de Download do BOA (Bottom of Atmosphere)",
        "scale_factor": "Fator de escala",
        "skip_masks": "Pular máscara",
        "skip_canny": "Pular Canny",
        "water_masks_save_path": "Diretório de saída do Deep Water Map",
        "water_masks": "Máscaras de água",
        "offset": "Offset",
        "skip_deepewatermap": "Pular Deep Water Map",
        "skip_cfmask": "Pular CFMask",
        "threshold": "Limiar para o Deep Water Map",
        "path_images": "Caminho das imagens",
        "path_masks": "Caminho das máscaras",
        "output_path": "Caminho de saída",
        "cloud_and_cloud_shadow_pixels": "Pixels de nuvens e sombras de nuvens",
        "skip_clean": "Pular limpeza",
    }


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
    
    def to_dict(self):
        return {
            "name": self.name,
            "label": self.label,
            "parameters": self.parameters,
        }

    def add_parameter(self, parameter):
        self.parameters.append(parameter)

    def to_qbytearray(self):
        return QByteArray(pickle.dumps(self))

    @staticmethod
    def from_qbytearray(qbytearray):
        return pickle.loads(qbytearray.data())


class ParameterRepresentation:
    def __init__(self, name, label, value=""):
        self.name = name
        self.label = label
        self.param_type = "str"
        self.value = value

    def __str__(self):
        return f"Parameter: {self.name}, Default Value: {self.name}, Type: {self.param_type}, Value: {self.value}"

    def to_qbytearray(self):
        return QByteArray(pickle.dumps(self))

    def to_dict(self):
        return {
            "name": self.name,
            "label": self.label,
            "param_type": "str",
            "value": self.value,
        }

    @staticmethod
    def from_qbytearray(qbytearray):
        return pickle.loads(qbytearray.data())
    



def find_all_nodes(project_path):
    """Procura por todos os arquivos 'nodes.py' e extrai os nomes das funções dentro deles."""
    path_nodes = glob.glob(
        os.path.join(f"{project_path}", "**", "nodes.py"), recursive=True
    )
    nodes = []
    min_param_name_len = 4

    for node in path_nodes:
        with open(node, "r", encoding="utf-8") as file:
            content = file.read()

        # Regex para capturar funções definidas
        functions = re.findall(r"def (\w+)\s*\(([^)]*)\):", content)
        for function_text in functions:
            node_name = function_text[0]

            parameters = function_text[1].split(",")
            parameters = list(
                map(lambda x: x.replace("\n", "").replace(" ", ""), parameters)
            )
            parameters = list(map(lambda x: x.strip().split("=")[0], parameters))
            parameters = list(
                filter(
                    lambda x: "*" not in x and len(x) > min_param_name_len, parameters
                )
            )

            parameters = list(map(
                lambda x: ParameterRepresentation(
                    name=x.split(":")[0].strip(),
                    label=params_labels[x.split(":")[0].strip()],
                    value=None,
                ),
                parameters,
            ))


            nodes.append(NodeRepresentation(name=node_name, parameters=parameters))

    return nodes
