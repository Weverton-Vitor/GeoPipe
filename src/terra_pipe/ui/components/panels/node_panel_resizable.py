from PyQt5.QtWidgets import QHBoxLayout, QSizeGrip

from terra_pipe.ui.components.panels.node_panel import NodePanel


class ResizableNodePanel(NodePanel):
    def initUI(self):
        super().initUI()

        # Adicione um QSizeGrip para redimensionamento
        size_grip = QSizeGrip(self)

        # Modifique o layout principal para incluir o size grip
        main_layout = self.layout()

        # Crie um layout horizontal para o size grip
        grip_layout = QHBoxLayout()
        grip_layout.addStretch()
        grip_layout.addWidget(size_grip)

        # Adicione o layout do grip ao layout principal
        main_layout.addLayout(grip_layout)
