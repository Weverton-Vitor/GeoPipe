from PyQt5.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class PipelineExecutionScreen(QWidget):
    def __init__(self, execute_callback):
        super().__init__()
        self.setWindowTitle("Execução de Pipeline")
        self.resize(600, 400)

        self.execute_callback = execute_callback
        # Layout principal
        main_layout = QVBoxLayout()

        # Botão de execução
        self.run_button = QPushButton("Executar Pipeline")

        # Barra de progresso (opcional, placeholder)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)

        # Área de log de execução
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("Logs da execução aparecerão aqui...")

        # Adiciona tudo ao layout
        main_layout.addWidget(self.run_button)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.log_output)

        self.setLayout(main_layout)
