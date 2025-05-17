from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)

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

SATELITE_LIST = ["Landsat", "Sentinel"]


class ParameterWidget(QWidget):
    """Widget para editar um único parâmetro com nome, tipo e valor"""

    def __init__(self, name, label="", param_type="str", value="", parent=None):
        super().__init__(parent)
        self.name = name
        self.label = label
        self.param_type = param_type

        self.file_input = None
        self.initUI()

        self.name_edit.setText(label)
        # self.type_combo.setCurrentText(param_type)
        # self.value_edit.setText(value)

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

        # Botão para remover o parâmetro
        # self.remove_btn = QToolButton()
        # self.remove_btn.setText("X")

        layout.addWidget(self.name_edit, 2)
        # layout.addWidget(self.type_combo, 2)
        # layout.addWidget(self.remove_btn, 1)

        # TODO apply factory method design pattern
        if self.param_type == "date":
            self.value_edit = QDateEdit()
            self.value_edit.setCalendarPopup(True)  # habilita o calendário popup
            self.value_edit.setDate(QDate.currentDate())
            layout.addWidget(self.value_edit, 3)
        elif self.param_type == "file":
            self.value_edit = QLineEdit()
            self.value_edit.setDisabled(True)
            self.value_edit.setMinimumWidth(100)

            self.browse_button = QPushButton("Procurar...")
            self.browse_button.clicked.connect(self.select_dir_or_file)
            self.value_edit.mousePressEvent = lambda event: self.select_dir_or_file(file=True)

            layout.addWidget(self.value_edit, 4)
            layout.addWidget(self.browse_button, 1)
        elif self.param_type == "directory":
            self.value_edit = QLineEdit()
            self.value_edit.setDisabled(True)
            self.value_edit.setMinimumWidth(100)

            self.browse_button = QPushButton("Procurar...")
            self.browse_button.clicked.connect(self.select_dir_or_file)
            self.value_edit.mousePressEvent = lambda event: self.select_dir_or_file(file=False)

            layout.addWidget(self.value_edit, 4)
            layout.addWidget(self.browse_button, 1)

        elif self.param_type == "satelite":
            self.value_edit = QComboBox()
            self.value_edit.addItems(SATELITE_LIST)
            layout.addWidget(self.value_edit, 3)
        elif self.param_type == "bool":
            self.value_edit = QComboBox()
            self.value_edit.addItems(["Sim", "Não"])
            layout.addWidget(self.value_edit, 3)
        else:
            self.value_edit = QLineEdit()
            self.value_edit.setPlaceholderText("Valor")
            layout.addWidget(self.value_edit, 3)

        self.setLayout(layout)

    def get_parameter_data(self):
        """Retorna os dados do parâmetro"""
        return {
            "name": self.name,
            "label": self.label,
            # "type": self.type_combo.currentText(),
            "value": self.value_edit.text(),
        }

    def select_dir_or_file(self, file: bool = False):
        """Abre um diálogo para selecionar um diretório ou arquivo"""
        path = ""

        if self.param_type == "directory":
            path = QFileDialog.getExistingDirectory(
                self, "Selecionar Diretório", "", QFileDialog.ShowDirsOnly
            )
        else:
            path, _ = QFileDialog.getOpenFileName(
                self, "Selecionar Arquivo", "", "Todos os Arquivos (*)"
            )

        if path:
            self.file_input = path
            self.value_edit.setPlaceholderText(self.file_input)
