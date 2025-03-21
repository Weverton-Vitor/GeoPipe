from PyQt5.QtWidgets import (
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class NodePanel(QWidget):
    """Painel lateral para editar um PipelineNode"""
    def __init__(self, node=None, parent=None):
        super().__init__(parent)
        self.node = node
        self.initUI()
        if node is not None:
            self.set_node(node)

    def initUI(self):
        layout = QVBoxLayout()

        self.name_label = QLabel("Nome:")
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_edit)

        self.inputs_label = QLabel("Entradas:")
        self.inputs_list = QListWidget()
        layout.addWidget(self.inputs_label)
        layout.addWidget(self.inputs_list)

        self.outputs_label = QLabel("Saídas:")
        self.outputs_list = QListWidget()
        layout.addWidget(self.outputs_label)
        layout.addWidget(self.outputs_list)

        self.save_button = QPushButton("Salvar")
        self.save_button.clicked.connect(self.save_changes)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def set_node(self, node):
        """Define o node a ser editado e preenche os campos com seus dados"""
        self.node = node
        if node:
            self.name_edit.setText(node.name)
            self.inputs_list.clear()
            self.inputs_list.addItems(node.inputs)
            self.outputs_list.clear()
            self.outputs_list.addItems(node.outputs)

    def save_changes(self):
        """Atualiza os valores do node com os do painel"""
        if self.node:
            self.node.name = self.name_edit.text()
            self.node.inputs = [self.inputs_list.item(i).text() for i in range(self.inputs_list.count())]
            self.node.outputs = [self.outputs_list.item(i).text() for i in range(self.outputs_list.count())]
            self.node.update()
