
from PyQt5.QtCore import QMimeData, Qt
from PyQt5.QtGui import QDrag, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QListWidget,
    QListWidgetItem,
)

from terra_pipe.nodes_registry import find_all_nodes

UI_NODES_NAME = {
    "apply_canny": "Detecção de bordas com Canny",
    "apply_cfmask": "Detecção de nuvems e suas sombras com CFMask",
    "apply_deep_water_map": "Detecção de Água com o Deep Water Map",
    "apply_fmask": "Detecção de nuvems e suas sombras com FMask",
    "cloud_removal": "Remoção de nuvens",
    "LT5": "Landsat 5 TM",
    "LT7": "Landsat 7 ETM+",
    "LT8": "Lansat 8 OLI/TIRS",
    "LT9": "Landast 9 OLI/TIRS2",
    "ST2": "Sentinel 2",
}

class ComponentList(QListWidget):
    """Lista de componentes disponíveis para arrastar para o canvas"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.raw_nodes = []

        # Adicionar componentes de exemplo
        # components = [
        #     "Landsat 5 TM",
        #     "Landsat 7 ETM+",
        #     "Lansat 8 OLI/TIRS",
        #     "Landast 9 OLI/TIRS2",
        #     "Sentinel 2",
        #     "Cloud Detection",
        #     "Clear Image",
        #     "Deep Water Map",
        #     "Canny",
        #     "Dependency"
        # ]

        components = [
        ]

        # components.append("Landsat 5 TM")
        # components.append("Landsat 7 ETM+")
        # components.append("Lansat 8 OLI/TIRS")
        # components.append("Landast 9 OLI/TIRS2")
        # components.append("Sentinel 2")

        nodes = find_all_nodes("../../")
        for node in nodes:
            if node.name in UI_NODES_NAME.keys():
                components.append(UI_NODES_NAME[f"{node.name}"])

                node.label = UI_NODES_NAME[f"{node.name}"]
                self.raw_nodes.append(node)

        components.append("Dependency")

        for comp in components:
            item = QListWidgetItem(comp)
            self.addItem(item)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item:
            mime = QMimeData()
            if item.text() == "Dependency":
                mime.setText(f"dependency:{item.text()}")
            else:
                mime.setText(f"component:{item.text()}")

                node = list(filter(lambda x: x.label == item.text(), self.raw_nodes))[0]

                mime.setData("raw_node", node.to_qbytearray())

            drag = QDrag(self)
            drag.setMimeData(mime)

            # Criar ícone simples para o drag
            pixmap = QPixmap(100, 30)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setPen(Qt.black)
            painter.drawText(5, 15, item.text())
            painter.end()

            drag.setPixmap(pixmap)
            drag.exec_(Qt.CopyAction)
