# ...existing code...
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class DependencyDialog(QDialog):
    """Pop-up para selecionar dois nodes e criar uma dependência."""

    def __init__(self, nodes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Criar Dependência")
        self.setModal(True)
        self.selected_nodes = (None, None)
        self.selected_nodes_widgets = (None, None)

        layout = QVBoxLayout()

        # Select 1
        self.select1_label = QLabel("Selecionar Node 1:")
        self.select1 = QComboBox()
        self.select1.addItems([node.name for node in nodes])
        layout.addWidget(self.select1_label)
        layout.addWidget(self.select1)

        # Select 2
        self.select2_label = QLabel("Selecionar Node 2:")
        self.select2 = QComboBox()
        self.select2.addItems([node.name for node in nodes])
        layout.addWidget(self.select2_label)
        layout.addWidget(self.select2)

        # Atualizar disponibilidade dos selects
        self.select1.currentIndexChanged.connect(self.update_select2)

        # Botões
        button_layout = QHBoxLayout()
        self.create_button = QPushButton("Criar")
        self.cancel_button = QPushButton("Cancelar")
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Conectar botões
        self.create_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)


    def accept(self):
        """Sobrescreve o método accept para salvar os nodes selecionados."""
        self.selected_nodes_widgets = filter(lambda node: node.name in self.get_selected_nodes(), self.parent().nodes)
        super().accept()

    def update_select2(self):
        """Atualiza os itens disponíveis no segundo select."""
        selected_node = self.select1.currentText()
        self.select2.clear()
        self.select2.addItems(
            [node.name for node in self.parent().nodes if node.name != selected_node]
        )

    def get_selected_nodes(self):
        """Retorna os nodes selecionados."""
        return self.select1.currentText(), self.select2.currentText()
