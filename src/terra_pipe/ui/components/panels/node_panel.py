from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from PyQt5.QtGui import QPalette, QColor

TYPE_MAP = { 
    "str": "string",
    "int": "Inteiro",
    "float": "Decimal",
    "bool": "Booleano",
    "list": "Lista",
    "dict": "Dicionário",
    "DataFrame": "DataFrame",
    "Series": "Series",
}


class ParameterWidget(QWidget):
    """Widget para editar um único parâmetro com nome, tipo e valor"""

    def __init__(self, name="", param_type="str", value="", parent=None):
        super().__init__(parent)
        self.initUI()
        self.name_edit.setText(name)
        # self.type_combo.setCurrentText(param_type)
        self.value_edit.setText(value)

    def initUI(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Nome do parâmetro
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nome")
        self.name_edit.setMinimumWidth(100)
        self.name_edit.setDisabled(True)

        # Tipo do parâmetro
        # self.type_combo = QComboBox()
        # self.type_combo.addItems(list(TYPE_MAP.values()))

        # Valor do parâmetro
        self.value_edit = QLineEdit()
        self.value_edit.setPlaceholderText("Valor")

        # Botão para remover o parâmetro
        # self.remove_btn = QToolButton()
        # self.remove_btn.setText("X")

        layout.addWidget(self.name_edit, 3)
        # layout.addWidget(self.type_combo, 2)
        layout.addWidget(self.value_edit, 3)
        # layout.addWidget(self.remove_btn, 1)

        self.setLayout(layout)

    def get_parameter_data(self):
        """Retorna os dados do parâmetro"""
        return {
            "name": self.name_edit.text(),
            # "type": self.type_combo.currentText(),
            "value": self.value_edit.text(),
        }


class NodePanel(QWidget):
    """Painel lateral para editar um PipelineNode"""

    def __init__(self, node=None, parent=None):
        super().__init__(parent)
        self.node = node
        self.input_params = []  # Lista de widgets de parâmetros de entrada
        self.output_params = []  # Lista de widgets de parâmetros de saída
        self.initUI()

        if node is not None:
            self.set_node(node)

    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)

        # Área com scroll para comportar muitos parâmetros
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_contents = QWidget()
        scroll_layout = QVBoxLayout(scroll_contents)
        scroll_layout.setAlignment(Qt.AlignTop)

        # Nome do node
        name_group = QGroupBox("Informações do Node")
        name_layout = QFormLayout()
        name_group.setMaximumHeight(100)


        self.name_edit = QLineEdit()
        self.name_edit.setDisabled(True)
        name_layout.addRow("Nome:", self.name_edit)

        self.func_edit = QLineEdit()
        self.func_edit.setDisabled(True)
        name_layout.addRow("Função:", self.func_edit)

        name_group.setLayout(name_layout)
        scroll_layout.addWidget(name_group)

        # Parâmetros de entrada
        input_group = QGroupBox("Parâmetros de Entrada")
        input_group.setMaximumHeight(300)
        input_layout = QVBoxLayout()

        self.input_container = QWidget()
        self.input_container_layout = QVBoxLayout(self.input_container)
        self.input_container_layout.setContentsMargins(0, 0, 0, 0)
        self.input_container_layout.setSpacing(5)

        input_header = QWidget()
        input_header_layout = QHBoxLayout(input_header)
        input_header_layout.setContentsMargins(0, 0, 0, 0)

        # Headers para os campos de entrada
        input_header_layout.addWidget(QLabel("Nome"), 3)
        # input_header_layout.addWidget(QLabel("Tipo"), 2)
        input_header_layout.addWidget(QLabel("Valor"), 2)
        # input_header_layout.addWidget(QLabel(""), 1)  # Espaço para o botão de remover

        input_layout.addWidget(input_header)
        input_layout.addWidget(self.input_container)

        # Botão para adicionar entrada
        # self.add_input_btn = QPushButton("Adicionar Entrada")
        # self.add_input_btn.clicked.connect(self.add_input_parameter)
        # input_layout.addWidget(self.add_input_btn)

        input_group.setLayout(input_layout)
        scroll_layout.addWidget(input_group, 0)

        # Parâmetros de saída
        # output_group = QGroupBox("Parâmetros de Saída")
        # output_layout = QVBoxLayout()

        # self.output_container = QWidget()
        # self.output_container_layout = QVBoxLayout(self.output_container)
        # self.output_container_layout.setContentsMargins(0, 0, 0, 0)
        # self.output_container_layout.setSpacing(5)

        # output_header = QWidget()
        # output_header_layout = QHBoxLayout(output_header)
        # output_header_layout.setContentsMargins(0, 0, 0, 0)

        # # Headers para os campos de saída
        # output_header_layout.addWidget(QLabel("Nome"), 3)
        # # output_header_layout.addWidget(QLabel("Tipo"), 2)
        # output_header_layout.addWidget(QLabel("Valor"), 3)
        # # output_header_layout.addWidget(QLabel(""), 1)  # Espaço para o botão de remover

        # output_layout.addWidget(output_header)
        # output_layout.addWidget(self.output_container)

        # Botão para adicionar saída
        # self.add_output_btn = QPushButton("Adicionar Saída")
        # self.add_output_btn.clicked.connect(self.add_output_parameter)
        # output_layout.addWidget(self.add_output_btn)

        # output_group.setLayout(output_layout)
        # scroll_layout.addWidget(output_group)

        scroll_area.setWidget(scroll_contents)
        main_layout.addWidget(scroll_area, 0)

        # Botões de ação
        button_layout = QHBoxLayout()

        self.save_button = QPushButton("Aplicar Alterações")
        self.save_button.clicked.connect(self.save_changes)
        button_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("Cancelar")
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self.setMinimumWidth(450)

    def add_input_parameter(self):
        """Adiciona um novo parâmetro de entrada"""
        param_widget = ParameterWidget(parent=self.input_container)
        # param_widget.remove_btn.clicked.connect(
        #     lambda: self.remove_parameter(param_widget, is_input=True)
        # )
        self.input_container_layout.addWidget(param_widget)
        self.input_params.append(param_widget)

    def add_output_parameter(self):
        """Adiciona um novo parâmetro de saída"""
        param_widget = ParameterWidget(parent=self.output_container)
        # param_widget.remove_btn.clicked.connect(
        #     lambda: self.remove_parameter(param_widget, is_input=False)
        # )
        self.output_container_layout.addWidget(param_widget)
        self.output_params.append(param_widget)

    def remove_parameter(self, param_widget, is_input=True):
        """Remove um parâmetro"""
        if is_input:
            self.input_params.remove(param_widget)
        else:
            self.output_params.remove(param_widget)

        param_widget.setParent(None)
        param_widget.deleteLater()

    def clear_parameters(self):
        """Limpa todos os parâmetros"""
        # Remover parâmetros de entrada
        for param in self.input_params[:]:
            self.remove_parameter(param, is_input=True)

        # Remover parâmetros de saída
        for param in self.output_params[:]:
            self.remove_parameter(param, is_input=False)

    def set_node(self, node):
        """Define o node a ser editado e preenche os campos com seus dados"""
        self.node = node

        if node:
            # Preencher dados básicos
            self.name_edit.setText(node.name)
            self.func_edit.setText(
                node.func_name
                if hasattr(node, "func_name")
                else node.name.lower().replace(" ", "_")
            )

            # Limpar parâmetros existentes
            self.clear_parameters()

            # Preencher parâmetros de entrada
            for i, input_name in enumerate(node.inputs):
                param_name = input_name.split(":")[0].strip()
                # param_type = input_name.split(":")[1].strip()
                
                # param_type = (
                #     node.input_types[i] if hasattr(node, "input_types") else "str"
                # )
                param_value = (
                    node.input_values[i] if hasattr(node, "input_values") else ""
                )

                param_widget = ParameterWidget(
                    name=param_name, value=param_value, parent=self.input_container
                )
                # param_widget.remove_btn.clicked.connect(
                #     lambda checked=False, w=param_widget: self.remove_parameter(
                #         w, is_input=True
                #     )
                # )
                self.input_container_layout.addWidget(param_widget)
                self.input_params.append(param_widget)

            # Preencher parâmetros de saída
            for i, output_name in enumerate(node.outputs):
                param_type = (
                    node.output_types[i] if hasattr(node, "output_types") else "str"
                )
                param_value = (
                    node.output_values[i] if hasattr(node, "output_values") else ""
                )

                param_widget = ParameterWidget(
                    output_name, param_type, param_value, self.output_container
                )
                # param_widget.remove_btn.clicked.connect(
                #     lambda checked=False, w=param_widget: self.remove_parameter(
                #         w, is_input=False
                #     )
                # )
                self.output_container_layout.addWidget(param_widget)
                self.output_params.append(param_widget)

    def save_changes(self):
        """Atualiza os valores do node com os do painel"""
        if self.node:
            # Atualizar dados básicos
            self.node.name = self.name_edit.text()
            self.node.func_name = self.func_edit.text()

            # Atualizar parâmetros de entrada
            self.node.inputs = []
            self.node.input_types = []
            self.node.input_values = []

            for param_widget in self.input_params:
                param_data = param_widget.get_parameter_data()
                print(param_data)
                self.node.inputs.append(param_data["name"])
                self.node.input_values.append(param_data["value"])

            # Atualizar parâmetros de saída
            self.node.outputs = []
            self.node.output_types = []
            self.node.output_values = []

            for param_widget in self.output_params:
                param_data = param_widget.get_parameter_data()
                self.node.outputs.append(param_data["name"])
                self.node.output_types.append(param_data["type"])
                self.node.output_values.append(param_data["value"])

            # Atualizar visualização do node
            self.node.update()

            # Emitir sinal de mudança (se implementado)
            if hasattr(self, "node_changed") and callable(
                getattr(self, "node_changed")
            ):
                self.node_changed.emit(self.node)
