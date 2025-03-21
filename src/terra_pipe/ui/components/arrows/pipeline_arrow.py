from PyQt5.QtCore import QLineF, QPoint, QPointF, Qt
from PyQt5.QtGui import QPainter, QPen, QBrush, QPolygonF
from PyQt5.QtWidgets import QWidget
import math


class PipelineArrow(QWidget):
    """Widget que representa uma seta conectando dois nodes."""

    def __init__(self, start_node, end_node, parent=None):
        super().__init__(parent)
        self.start_node = start_node
        self.end_node = end_node
        self.setFixedSize(parent.size())  # Garante que o widget cobre a área total
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Define a caneta para a linha principal
        pen = QPen(Qt.black, 3)  # Espessura da linha
        painter.setPen(pen)

        # Obtém as coordenadas globais dos nodes e converte para locais
        start_pos = self.start_node.mapToParent(
            QPoint(self.start_node.width(), self.start_node.height() // 2)
        )
        end_pos = self.end_node.mapToParent(QPoint(0, self.end_node.height() // 2))

        # Converte para coordenadas locais do `PipelineArrow`
        start_pos = self.mapFromParent(start_pos)
        end_pos = self.mapFromParent(end_pos)

        # Desenha a linha principal
        line = QLineF(QPointF(start_pos), QPointF(end_pos))
        painter.drawLine(line)

        # Adiciona a ponta da seta (triângulo)
        self.draw_arrow_head(painter, line)

    def draw_arrow_head(self, painter, line):
        """Desenha a ponta da seta como um triângulo."""
        arrow_size = 12  # Tamanho da ponta da seta

        # Calcula o ângulo da linha
        angle = math.atan2(-line.dy(), line.dx())

        # Define os pontos do triângulo da ponta da seta
        p1 = line.p2()  # Ponto final da linha
        p2 = p1 + QPointF(
            -arrow_size * math.cos(angle - math.pi / 6),
            arrow_size * math.sin(angle - math.pi / 6),
        )
        p3 = p1 + QPointF(
            -arrow_size * math.cos(angle + math.pi / 6),
            arrow_size * math.sin(angle + math.pi / 6),
        )

        # Cria um polígono para desenhar a ponta da seta
        arrow_head = QPolygonF([p1, p2, p3])

        # Define um pincel preto para preencher o triângulo
        painter.setBrush(QBrush(Qt.black))
        painter.drawPolygon(arrow_head)

    def update_position(self):
        self.update()
