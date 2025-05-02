import json
import sys

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from terra_pipe.ui.canvas.component_list import ComponentList
from terra_pipe.ui.canvas.pipeline_canvas import PipelineCanvas
from terra_pipe.ui.components.panels.node_panel import NodePanel
from terra_pipe.ui.components.panels.node_panel_resizable import ResizableNodePanel

# Tentar importar o Kedro (necessário em produção)
try:
    from kedro.pipeline import Pipeline, node
    from kedro.pipeline.modular_pipeline import pipeline
    KEDRO_AVAILABLE = True
except ImportError:
    KEDRO_AVAILABLE = False
    print("Aviso: Kedro não encontrado. Algumas funcionalidades estarão limitadas.")


class KedroVisualEditor(QMainWindow):
    """Janela principal da aplicação"""

    def __init__(self):
        super().__init__()
        self.current_file = None
        self.initUI()

    def initUI(self):
        """Configura a interface gráfica do editor"""
        self.setWindowTitle("Kedro Visual Pipeline Builder")
        self.setGeometry(100, 100, 1200, 800)

        self.setup_toolbar()
        self.setup_layout()
        self.show()

    def setup_toolbar(self):
        """Cria a barra de ferramentas"""
        toolbar = QToolBar("Ferramentas")
        self.addToolBar(toolbar)

        actions = [
            ("Novo", self.new_pipeline),
            ("Abrir", self.open_pipeline),
            ("Salvar", self.save_pipeline),
            ("Editar Pipeline", self.export_to_kedro),
            ("Executar", self.execute)
        ]
        
        for name, method in actions:
            action = QAction(name, self)
            action.triggered.connect(method)
            toolbar.addAction(action)

    def setup_layout(self):
        """Configura o layout principal da aplicação"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # Painel de Componentes (Esquerda)
        component_panel = QWidget()
        component_layout = QVBoxLayout(component_panel)
        component_layout.addWidget(QLabel("Componentes"))
        
        self.component_list = ComponentList()
        component_layout.addWidget(self.component_list)
        component_panel.setMaximumWidth(200)
        main_layout.addWidget(component_panel)

        # Área principal - Canvas de pipeline
        self.canvas = PipelineCanvas()
        main_layout.addWidget(self.canvas)
        self.canvas.selected_node_changed.connect(self.update_property_panel)

        # Painel de Propriedades (Direita)
        self.property_panel = NodePanel(parent=self, node=self.canvas.selected_node)
        self.property_panel.hide()
        main_layout.addWidget(self.property_panel)

    #TODO: Criar novo pipeline
    def new_pipeline(self):
        """Cria um novo pipeline, apagando o atual se necessário"""
        if self.canvas.nodes:
            reply = QMessageBox.question(self, "Confirmar", "Isso irá apagar o pipeline atual. Continuar?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return

        self.canvas.clear()
        self.current_file = None

    def open_pipeline(self):
        """Abre um pipeline salvo em JSON"""
        filename, _ = QFileDialog.getOpenFileName(self, "Abrir Pipeline", "", "Pipeline (*.json)")
        if filename:
            # try:
                with open(filename, "r") as f:
                    data = json.load(f)
                self.canvas.load_pipeline_data(data)
                self.current_file = filename
                self.statusBar().showMessage(f"Pipeline carregado de {filename}")
            # except Exception as e:
                # QMessageBox.critical(self, "Erro", f"Não foi possível abrir o arquivo: {str(e)}")

    def save_pipeline(self):
        """Salva o pipeline atual"""
        if not self.current_file:
            filename, _ = QFileDialog.getSaveFileName(self, "Salvar Pipeline", "", "Pipeline (*.json)")
            if not filename:
                return
            if not filename.endswith(".json"):
                filename += ".json"
            self.current_file = filename

        try:
            with open(self.current_file, "w") as f:
                json.dump(self.canvas.get_pipeline_data(), f, indent=2)
            self.statusBar().showMessage(f"Pipeline salvo em {self.current_file}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível salvar o arquivo: {str(e)}")

    def export_to_kedro(self):
        """Exporta o pipeline para código Python do Kedro"""
        if not KEDRO_AVAILABLE:
            QMessageBox.warning(self, "Aviso", "Kedro não está instalado. Esta é apenas uma visualização do código.")
            return

        if not self.canvas.nodes:
            QMessageBox.information(self, "Informação", "Nenhum pipeline para exportar.")
            return

        try:
            filename, _ = QFileDialog.getSaveFileName(self, "Exportar para Kedro", "", "Python (*.py)")
            if filename:
                with open(filename, "w") as f:
                    f.write(self.generate_kedro_code())
                self.statusBar().showMessage(f"Código Kedro exportado para {filename}")
                QMessageBox.information(self, "Sucesso", f"Pipeline exportado com sucesso para {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível exportar: {str(e)}")

    def generate_kedro_code(self):
        """Gera código Python para o pipeline do Kedro"""
        pipeline_data = self.canvas.get_pipeline_data()
        nodes, connections = pipeline_data["nodes"], pipeline_data["connections"]

        code = """# Código gerado pelo Kedro Visual Pipeline Builder
            from kedro.pipeline import Pipeline, node
            from kedro.pipeline.modular_pipeline import pipeline

            """
        
        for n in nodes:
            func_name = n["name"].lower().replace(" ", "_")
            inputs = ", ".join(n["inputs"])
            outputs = ", ".join(n["outputs"])
            code += f"def {func_name}({inputs}):\n    pass\n\n"

        code += "def register_pipelines():\n    return {\n        '__default__': Pipeline([\n"
        
        for n in nodes:
            func_name = n["name"].lower().replace(" ", "_")
            inputs = ', '.join(f'"{i}"' for i in n["inputs"])
            outputs = ', '.join(f'"{o}"' for o in n["outputs"])
            code += f"        node({func_name}, [{inputs}], [{outputs}], name='{n['name']}'),\n"
        
        code += "    ])\n}\n"
        return code
    
    def execute(self):
        pass

    def update_property_panel(self, text):
        self.statusBar().showMessage(text)
        self.property_panel.set_node(self.canvas.selected_node)
        if self.canvas.selected_node:
            self.property_panel.show()
        else:
            self.property_panel.hide()

def main():
    app = QApplication(sys.argv)
    ex = KedroVisualEditor()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()