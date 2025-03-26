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
        self.nodes = nodes  # Armazena os nodes localmente

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

        # Atualiza o segundo select com base no primeiro inicialmente
        self.update_select2()

    def accept(self):
        """Sobrescreve o método accept para salvar os nodes selecionados."""
        selected_names = self.get_selected_nodes()
        self.node1 = next(node for node in self.nodes if node.name == selected_names[0])
        self.node2 = next(node for node in self.nodes if node.name == selected_names[1])
        super().accept()

    def update_select2(self):
        """Atualiza os itens disponíveis no segundo select para evitar repetições."""
        selected_node = self.select1.currentText()
        self.select2.clear()

        # Adiciona apenas os nodes que não são o selecionado no select1
        self.select2.addItems([node.name for node in self.nodes if node.name != selected_node])

        # Se não houver mais opções no select2, desativá-lo
        self.select2.setEnabled(self.select2.count() > 0)


    def get_selected_nodes(self):
        """Retorna os nomes dos nodes selecionados."""
        return self.select1.currentText(), self.select2.currentText()
