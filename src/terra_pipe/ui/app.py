import json
import sys

from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from terra_pipe.ui.canvas.pipeline_canvas import PipelineCanvas
from terra_pipe.ui.screens.canvas_screen import CanvasScreen
from terra_pipe.ui.screens.execute_screen_widget import PipelineExecutionScreen


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
            ("Editar Pipeline", self.edit_pipeline),
            ("Executar", self.execute),
        ]

        for name, method in actions:
            action = QAction(name, self)
            action.triggered.connect(method)
            toolbar.addAction(action)

    def setup_layout(self):
        """Configura o layout principal da aplicação"""

        # Widget principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        self.stack = QStackedWidget()

        self.canvas_screen = CanvasScreen()

        self.execute_pipeline_screen = PipelineExecutionScreen(
            execute_callback=self.execute
        )

        self.stack.addWidget(self.canvas_screen)
        self.stack.addWidget(self.execute_pipeline_screen)

        main_layout.addWidget(self.stack)

    # TODO: Criar novo pipeline
    def new_pipeline(self):
        """Cria um novo pipeline, apagando o atual se necessário"""
        if self.canvas_screen.canvas.nodes:
            reply = QMessageBox.question(
                self,
                "Confirmar",
                "Isso irá apagar o pipeline atual. Continuar?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return

        self.canvas.clear()
        self.current_file = None
        self.update()
        self.canvas = PipelineCanvas()

    def open_pipeline(self):
        """Abre um pipeline salvo em JSON"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Abrir Pipeline", "", "Pipeline (*.json)"
        )
        if filename:
            # try:
            with open(filename, "r") as f:
                data = json.load(f)
            self.canvas_screen.canvas.load_pipeline_data(data)
            self.current_file = filename
            self.canvas_screen.pipeline_name_field.setText(data.get("Pipeline", ""))
            self.statusBar().showMessage(f"Pipeline carregado de {filename}")
        # except Exception as e:
        # QMessageBox.critical(self, "Erro", f"Não foi possível abrir o arquivo: {str(e)}")

    def save_pipeline(self):
        """Salva o pipeline atual"""
        if not self.current_file:
            filename, _ = QFileDialog.getSaveFileName(
                self, "Salvar Pipeline", "", "Pipeline (*.json)"
            )
            if not filename:
                return
            if not filename.endswith(".json"):
                filename += ".json"
            self.current_file = filename

        try:
            with open(self.current_file, "w") as f:
                json_export = {"Pipeline": self.canvas_screen.pipeline_name_field.text()}
                json_export = {**json_export, **self.canvas_screen.canvas.get_pipeline_data()}
                json.dump(json_export, f, indent=2)
            self.statusBar().showMessage(f"Pipeline salvo em {self.current_file}")
        except Exception as e:
            QMessageBox.critical(
                self, "Erro", f"Não foi possível salvar o arquivo: {str(e)}"
            )

    def edit_pipeline(self):
        """Exporta o pipeline para código Python do Kedro"""
        self.stack.setCurrentIndex(0)

    # TODO: Executar o pipeline
    # TODO: validar o pipeline
    # TODO: valdidar os nodes
    # TODO: validar os inputs e outputs
    # TODO: validar os tipos de dados
    # TODO: validar o nome do pipeline
    def execute(self):
        """Executa o pipeline"""
        # Se o pipeline não tiver nome ou não estiver salvo, avisa o usuário
        if self.canvas_screen.pipeline_name_field.text() == "":
            QMessageBox.warning(
                self, "Aviso", "Por favor, salve e forneça um nome para o pipeline."
            )
            return

        if self.current_file is None:
            self.save_pipeline()

        try:
            self.stack.setCurrentIndex(1)

            # Aqui você pode adicionar a lógica para executar o pipeline
            # QMessageBox.information(self, "Sucesso", "Pipeline executado com sucesso!")
        except Exception as e:
            QMessageBox.critical(
                self, "Erro", f"Não foi possível executar o pipeline: {str(e)}"
            )




def main():
    app = QApplication(sys.argv)
    ex = KedroVisualEditor()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
