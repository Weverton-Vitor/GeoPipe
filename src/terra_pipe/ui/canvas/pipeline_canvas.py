from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QColor, QPainter, QPen
from PyQt5.QtWidgets import (
    QWidget,
)

from terra_pipe.ui.utils.nodes_registry import NodeRepresentation
from terra_pipe.ui.components.arrows.pipeline_arrow import PipelineArrow
from terra_pipe.ui.components.nodes.pipeline_node import PipelineNode
from terra_pipe.ui.dialogues.dependency_dialogue import DependencyDialog
from PyQt5.QtCore import pyqtSignal


class PipelineCanvas(QWidget):
    """Área de canvas onde os nodes são colocados e conectados"""

    selected_node_changed = pyqtSignal(str)  # Sinal personalizado

    def __init__(self, parent=None):
        super().__init__(parent)
        self.nodes = []
        self.connections = []
        self.setAcceptDrops(True)
        self.setMinimumSize(800, 600)
        self.current_connection = None
        self.connecting_mode = False
        self.selected_node = None
        self.painter = QPainter(self)

        # Habilitar acompanhamento do mouse para desenhar conexões
        self.setMouseTracking(True)

    def set_selected_node(self, node):
        self.selected_node = node
        self.selected_node_changed.emit("")

    def paintEvent(self, event):
        self.painter.setRenderHint(QPainter.Antialiasing)

        # Desenhar fundo
        self.painter.fillRect(self.rect(), QColor(240, 240, 240))

        # Desenhar grade de fundo (opcional)
        self.painter.setPen(QPen(QColor(220, 220, 220), 1))
        for x in range(0, self.width(), 20):
            self.painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 20):
            self.painter.drawLine(0, y, self.width(), y)

        # Desenhar conexões entre nodes
        # self.painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))
        # for conn in self.connections:
        #     start_node, start_port, end_node, end_port = conn
        #     for node in self.nodes:
        #         if node.node_id == start_node:
        #             start_pos = node.pos() + QPoint(node.width(), 30 + 15 * start_port)
        #         if node.node_id == end_node:
        #             end_pos = node.pos() + QPoint(0, 30 + 15 * end_port)

        #     # Desenhar linha de conexão com curva bezier
        #     self.painter.drawLine(start_pos, end_pos)

        # Desenhar conexão atual sendo criada
        # if self.connecting_mode and self.current_connection:
        #     start_node, start_port, mouse_pos = self.current_connection
        #     for node in self.nodes:
        #         if node.node_id == start_node:
        #             start_pos = node.pos() + QPoint(node.width(), 30 + 15 * start_port)
        #             self.painter.setPen(QPen(Qt.darkGray, 2, Qt.DashLine))
        #             self.painter.drawLine(start_pos, mouse_pos)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            if (
                event.mimeData().text().startswith("component:")
                or event.mimeData().text().startswith("dependency:")
                or event.mimeData().text().startswith("node:")
            ):
                event.acceptProposedAction()

    def dropEvent(self, event):
        mime_data = event.mimeData()

        if mime_data.hasText():
            # Criar novo node ou mover node existente
            data = mime_data.text()

            if data.startswith("component:"):
                # Novo node de componente da barra lateral
                component_name = data.split(":")[1]
                node_raw_representation = NodeRepresentation.from_qbytearray(
                    mime_data.data("raw_node")
                )

                new_node = PipelineNode(
                    name=component_name,
                    node_raw_representation=node_raw_representation,
                    inputs=node_raw_representation.parameters,
                    parent=self,
                )
                new_node.move(
                    event.pos() - QPoint(new_node.width() // 2, new_node.height() // 2)
                )
                new_node.show()
                self.nodes.append(new_node)
            elif data.startswith("dependency:"):
                dlg = DependencyDialog(parent=self, nodes=self.nodes)
                dlg.exec()

                if dlg.accepted:
                    node1, node2 = dlg.node1, dlg.node2
                    new_arrow = PipelineArrow(node1, node2, parent=self)
                    new_arrow.show()
                    self.connections.append(new_arrow)

            elif data.startswith("node:"):
                # Mover node existente
                node_id = int(data.split(":")[1])
                for node in self.nodes:
                    if node.node_id == node_id:
                        node.move(
                            event.pos() - QPoint(node.width() // 2, node.height() // 2)
                        )
                        break

            self.update()
            event.acceptProposedAction()

    def mousePressEvent(self, event):
        # Verificar se clicou em uma porta de saída para iniciar uma conexão

        for node in self.nodes:
            node_rect = node.geometry()
            for i, _ in enumerate(node.outputs):
                port_y = 30 + i * 15
                port_rect = QPoint(node_rect.right() - 10, node_rect.top() + port_y)

                if (event.pos() - port_rect).manhattanLength() < 10:
                    self.connecting_mode = True
                    self.current_connection = (node.node_id, i, event.pos())
                    self.update()
                    return

        # Verificar se clicou em um node para seleção
        # for node in self.nodes:
        #     if node.geometry().contains(event.pos()):

        #         self.selected_node = node
        #         self.selected_node.color= QColor(100, 100, 0)
        #         self.selected_node.update()
        #         self.update()
        #         return

        # Nada foi clicado, desselecione
        self.selected_node = None

    # def mouseReleaseEvent(self, event):
    #     if self.connecting_mode and self.current_connection:
    #         # Verificar se soltou sobre uma porta de entrada
    #         for node in self.nodes:
    #             node_rect = node.geometry()
    #             for i, _ in enumerate(node.inputs):
    #                 port_y = 30 + i * 15
    #                 port_rect = QPoint(node_rect.left(), node_rect.top() + port_y)

    #                 if (event.pos() - port_rect).manhattanLength() < 10:
    #                     # Criar conexão
    #                     start_node, start_port, _ = self.current_connection
    #                     self.connections.append(
    #                         (start_node, start_port, node.node_id, i)
    #                     )
    #                     break

    #         self.connecting_mode = False
    #         self.current_connection = None
    #         self.update()

    def mouseMoveEvent(self, event):
        if self.connecting_mode and self.current_connection:
            # Atualizar posição do mouse para desenhar a linha
            self.current_connection = (
                self.current_connection[0],
                self.current_connection[1],
                event.pos(),
            )
            self.update()

    def keyPressEvent(self, event):
        # Deletar node selecionado quando pressionar Delete
        if event.key() == Qt.Key_Delete and self.selected_node:
            # Remover conexões relacionadas a este node
            node_id = self.selected_node.node_id
            self.connections = [
                c for c in self.connections if c[0] != node_id and c[2] != node_id
            ]

            # Remover o node
            self.nodes.remove(self.selected_node)
            self.selected_node.deleteLater()
            self.selected_node = None
            self.update()

    def get_pipeline_data(self):
        """Captura os dados do pipeline para gerar código"""
        nodes_data = [node.get_node_data() for node in self.nodes]
        return {"nodes": nodes_data, "connections": self.connections}

    def load_pipeline_data(self, data):
        """Carrega um pipeline a partir dos dados salvos"""
        # Limpar canvas
        for node in self.nodes:
            node.deleteLater()
        self.nodes = []
        self.connections = []

        # Recriar nodes
        for node_data in data["nodes"]:
            new_node = PipelineNode(
                node_data["name"], node_data["inputs"], node_data["outputs"], self
            )
            new_node.node_id = node_data["id"]
            new_node.move(node_data["position"][0], node_data["position"][1])
            new_node.show()
            self.nodes.append(new_node)

        # Recriar conexões
        self.connections = data["connections"]
        self.update()
