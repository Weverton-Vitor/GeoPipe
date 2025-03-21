from PyQt5.QtCore import QLineF, QPoint, Qt
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtWidgets import QWidget


class PipelineArrow(QWidget):
    """Widget que representa uma seta conectando dois nodes."""

    def __init__(self, start_node, end_node, parent=None):
        super().__init__(parent)
        self.start_node = start_node
        self.end_node = end_node
        # self.setZOrder(-1)  # Manter atrás dos nodes

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(Qt.black, 4)
        painter.setPen(pen)

        start_pos = self.start_node.mapToParent(
            QPoint(self.start_node.width(), self.start_node.height() // 2)
        )
        end_pos = self.end_node.mapToParent(QPoint(0, self.end_node.height() // 2))

        line = QLineF(start_pos, end_pos)
        painter.drawLine(line)

    def update_position(self):
        self.update()
