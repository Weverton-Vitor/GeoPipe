from PyQt5.QtCore import QMimeData, QPoint, Qt
from PyQt5.QtGui import QColor, QDrag, QFont, QPainter, QPen, QPixmap, QLinearGradient
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QObject, QEvent

from PyQt5.QtGui import QTextOption, QFont, QPainter
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel


class PipelineNode(QWidget):
    """Widget que representa um node do pipeline Kedro"""

    def __init__(self, name, node_raw_representation, inputs=None, outputs=None, parent=None):
        super().__init__(parent)
        self.name = name
        self.inputs = inputs or []
        self.outputs = outputs or []
        self.node_id = id(self)
        self.setFixedSize(160, 90)
        self.initUI()
        self.installEventFilter(self)
        self.default_node_color = QColor(255, 0, 200)
        self.selected_node_color = QColor(0, 0, 200)
        self.color = self.default_node_color
        self.node_raw_representation = node_raw_representation


    def initUI(self):
        self.setAcceptDrops(True)
        self.setFont(QFont("Arial", 10, QFont.Bold))

    def get_node_color(self):
        if "input" in self.name.lower():
            return QColor(100, 200, 100)
        elif "output" in self.name.lower():
            return QColor(200, 100, 100)
        return QColor(100, 100, 200)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Gradiente no fundo do node
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, self.color.lighter(130))
        gradient.setColorAt(1, self.color.darker(130))
        painter.setBrush(gradient)
        painter.setPen(QPen(Qt.black, 2))
        painter.drawRoundedRect(2, 2, self.width() - 4, self.height() - 4, 15, 15)

        painter.setPen(Qt.white)
        painter.setFont(QFont("Arial", 10, QFont.Bold))

        text_rect = QRectF(self.rect())  # Define a área onde o texto será desenhado

        text_option = QTextOption()
        text_option.setWrapMode(QTextOption.WordWrap)  # Habilita quebra de linha automática
        text_option.setAlignment(Qt.AlignCenter)  # Alinha o texto no centro

        painter.drawText(text_rect, self.name, text_option)

        # Desenhar portas de entrada
        # for i, input_name in enumerate(self.inputs):
        #     y_pos = 30 + i * 15
        #     painter.setPen(QPen(Qt.black, 1))
        #     painter.setBrush(Qt.white)
        #     painter.drawEllipse(5, y_pos, 12, 12)
        #     # painter.drawText(20, y_pos + 10, input_name)

        # # Desenhar portas de saída
        # for i, output_name in enumerate(self.outputs):
        #     y_pos = 30 + i * 15
        #     painter.setPen(QPen(Qt.black, 1))
        #     painter.setBrush(Qt.white)
        #     painter.drawEllipse(self.width() - 17, y_pos, 12, 12)
        #     # painter.drawText(self.width() - 85, y_pos + 10, output_name)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()


    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(f"node:{self.node_id}")
        drag.setMimeData(mime)
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        drag.setPixmap(pixmap)
        drag.exec_(Qt.MoveAction)

    def get_node_data(self):
        return {
            "name": self.name,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "position": (self.pos().x(), self.pos().y()),
            "id"
            : self.node_id,
        }
    
    def eventFilter(self, obj, event):
        if obj == self and event.type() == QEvent.MouseButtonRelease:
            
            # Check if node is already selected, if so, deselect it
            if self.parent().selected_node == self:
                self.color = self.default_node_color
                self.parent().set_selected_node(None)
                self.update()
                self.parent().update()
                return True
            
            if self.parent().selected_node is not None:
                # Update old selected node
                self.parent().selected_node.color = self.parent().selected_node.default_node_color
                self.parent().selected_node.update()
                self.parent().update()

            
            # Update new selected node
            self.parent().set_selected_node(self)
            self.color = self.selected_node_color
            self.parent().update()
            self.update()
            return True
        
        return super().eventFilter(obj, event)
    
    