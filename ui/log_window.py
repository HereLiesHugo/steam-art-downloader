from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
from PySide6.QtCore import Qt, QObject, Signal
import logging

class QtLogHandler(logging.Handler, QObject):
    """
    Custom Logging Handler that emits a signal with log messages.
    Inherits from both logging.Handler and QObject to support Signals.
    """
    log_signal = Signal(str)

    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        self.log_signal.emit(msg)

class LogWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Logs")
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.hide)
        layout.addWidget(close_btn)
        
    def append_log(self, message: str):
        self.text_area.append(message)
