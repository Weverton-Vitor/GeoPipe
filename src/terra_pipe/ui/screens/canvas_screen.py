from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from terra_pipe.ui.canvas.component_list import ComponentList
from terra_pipe.ui.canvas.pipeline_canvas import PipelineCanvas
from terra_pipe.ui.components.panels.node_panel import NodePanel


class CanvasScreen(QWidget):
    def __init__(self):
        self.selected_node = None
        super().__init__()
        self.setWindowTitle("Execução de Pipeline")
        self.resize(600, 400)

        # Layout principal
        main_layout = QHBoxLayout()

         # Painel de Componentes (Esquerda)
        component_panel = QWidget()
        component_layout = QVBoxLayout(component_panel)

        # Campo de nome do pipeline
        self.pipeline_name_field = QLineEdit()
        self.pipeline_name_field.setPlaceholderText("Nome do Pipeline:")
        component_layout.addWidget(self.pipeline_name_field)

        component_layout.addWidget(QLabel("Componentes"))
        self.component_list = ComponentList()
        component_layout.addWidget(self.component_list)
        component_panel.setMaximumWidth(300)
        main_layout.addWidget(component_panel)

        # Área principal - Canvas de pipeline
        self.canvas = PipelineCanvas()
        main_layout.addWidget(self.canvas)
        self.canvas.selected_node_changed.connect(self.update_property_panel)

        # Painel de Propriedades (Direita)
        self.property_panel = NodePanel(parent=self, node=self.canvas.selected_node)
        self.property_panel.hide()
        main_layout.addWidget(self.property_panel)

        self.setLayout(main_layout)

    def update_property_panel(self, text):
        self.property_panel.set_node(self.canvas.selected_node)
        if self.canvas.selected_node:
            self.property_panel.show()
        else:
            self.property_panel.hide()
