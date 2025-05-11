import sys
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget, QPushButton

from terra_pipe.ui.screens.execute_screen_widget import PipelineExecutionScreen

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("App com páginas")
        self.resize(800, 600)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        layout = QVBoxLayout(central_widget)

        # Cria o QStackedWidget que armazenará as telas
        self.stacked = QStackedWidget()
        layout.addWidget(self.stacked)

        # Cria as "páginas"
        self.home_page = self.build_home_page()
        self.execution_page = PipelineExecutionScreen(execute_callback=self.execute)

        # Adiciona ao stacked
        self.stacked.addWidget(self.home_page)
        self.stacked.addWidget(self.execution_page)

    def build_home_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        button = QPushButton("Ir para execução")
        button.clicked.connect(lambda: self.stacked.setCurrentWidget(self.execution_page))
        layout.addWidget(button)
        page.setLayout(layout)
        return page

    def execute(self):
        print("Executando pipeline...")  # Sua lógica de execução aqui



def main():
    app = MainWindow()
    sys.exit(app.exec_)


if __name__ == "__main__":
    main()