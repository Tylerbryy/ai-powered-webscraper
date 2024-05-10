import sys
import json
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QMessageBox, QLineEdit, QFrame, QDialog, QScrollArea, QFileDialog, QProgressBar, QTabWidget, QGroupBox, QFormLayout
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette, QSyntaxHighlighter, QTextCharFormat
import re
from scrapegraphai.graphs import SmartScraperGraph

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "openai_api_key": ""
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    else:
        return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file)

class JsonSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._mapping = {}

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#f92672"))
        self._mapping['{'] = keyword_format
        self._mapping['}'] = keyword_format
        self._mapping['['] = keyword_format
        self._mapping[']'] = keyword_format
        self._mapping[':'] = keyword_format
        self._mapping[','] = keyword_format

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#e6db74"))
        self._mapping['"'] = string_format

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#ae81ff"))
        self._mapping['\\b\\d+\\b'] = number_format

    def highlightBlock(self, text):
        for pattern, format in self._mapping.items():
            for match in re.finditer(pattern, text):
                start, end = match.span()
                self.setFormat(start, end - start, format)

class JsonViewerDialog(QDialog):
    def __init__(self, json_data):
        super().__init__()
        self.json_data = json_data
        self.setWindowTitle("JSON Viewer")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        text_edit = QTextEdit(self)
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Fira Code", 10))
        text_edit.setText(json.dumps(json_data, indent=2))

        highlighter = JsonSyntaxHighlighter(text_edit.document())

        scroll_area = QScrollArea(self)
        scroll_area.setWidget(text_edit)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        download_button = QPushButton("Download JSON")
        download_button.clicked.connect(self.download_json)
        button_layout.addWidget(download_button)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def download_json(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save JSON File", "", "JSON Files (*.json)")
        if file_path:
            with open(file_path, 'w') as file:
                json.dump(self.json_data, file, indent=2)

class ScraperThread(QThread):
    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, url, prompt, api_key):
        super().__init__()
        self.url = url
        self.prompt = prompt
        self.api_key = api_key

    def run(self):
        graph_config = {
            "llm": {
                "api_key": self.api_key,
                "model": "gpt-4-turbo-2024-04-09",
            },
        }

        try:
            smart_scraper_graph = SmartScraperGraph(
                prompt=self.prompt,
                source=self.url,
                config=graph_config
            )
            result = smart_scraper_graph.run()
            self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))

class ScraperWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI-Powered Website Scraper")
        self.setGeometry(100, 100, 1200, 800)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #1c1c1c;
            }
            QLabel {
                color: #ffffff;
                font-size: 16px;
            }
            QPushButton {
                background-color: #e74c3c;
                color: #ffffff;
                border: none;
                padding: 10px 20px;
                font-size: 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QTextEdit, QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #e74c3c;
                padding: 10px;
                font-size: 16px;
                border-radius: 5px;
            }
            QFrame {
                background-color: #2d2d2d;
                border-radius: 5px;
            }
            QProgressBar {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #e74c3c;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #e74c3c;
                border-radius: 4px;
            }
        """)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        input_frame = QFrame()
        input_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(20, 20, 20, 20)
        input_layout.setSpacing(10)

        url_label = QLabel("Website URL")
        input_layout.addWidget(url_label)
        self.url_input = QLineEdit()
        input_layout.addWidget(self.url_input)

        prompt_label = QLabel("Scraping Instructions")
        input_layout.addWidget(prompt_label)
        self.prompt_input = QTextEdit()
        self.prompt_input.setMinimumHeight(200)
        input_layout.addWidget(self.prompt_input)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.scrape_button = QPushButton("Start Scraping")
        self.scrape_button.clicked.connect(self.scrape_website)
        button_layout.addWidget(self.scrape_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_inputs)
        button_layout.addWidget(self.reset_button)

        button_layout.addStretch()
        input_layout.addLayout(button_layout)

        main_layout.addWidget(input_frame)

        result_frame = QFrame()
        result_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        result_layout = QVBoxLayout(result_frame)
        result_layout.setContentsMargins(20, 20, 20, 20)
        result_layout.setSpacing(10)

        result_label = QLabel("Scraping Result")
        result_layout.addWidget(result_label)

        settings_button = QPushButton("Settings")
        settings_button.clicked.connect(self.open_settings)
        button_layout.addWidget(settings_button)

        self.result_tabs = QTabWidget()
        self.result_tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.result_tabs.setDocumentMode(True)
        self.result_tabs.setTabsClosable(False)
        self.result_tabs.setMovable(False)

        self.json_tab = QWidget()
        json_tab_layout = QVBoxLayout(self.json_tab)
        json_tab_layout.setContentsMargins(0, 0, 0, 0)

        self.json_text_edit = QTextEdit()
        self.json_text_edit.setReadOnly(True)
        self.json_text_edit.setFont(QFont("Fira Code", 10))
        json_syntax_highlighter = JsonSyntaxHighlighter(self.json_text_edit.document())
        json_tab_layout.addWidget(self.json_text_edit)

        self.result_tabs.addTab(self.json_tab, "JSON")

        result_layout.addWidget(self.result_tabs)

        view_json_button_layout = QHBoxLayout()
        view_json_button_layout.addStretch()
        self.view_json_button = QPushButton("View JSON")
        self.view_json_button.clicked.connect(self.view_json)
        self.view_json_button.setEnabled(False)
        view_json_button_layout.addWidget(self.view_json_button)
        view_json_button_layout.addStretch()
        result_layout.addLayout(view_json_button_layout)

        main_layout.addWidget(result_frame)

        footer_layout = QHBoxLayout()
        company_label = QLabel("Knightsbridge Engineering © 2024")
        company_label.setStyleSheet("font-size: 12px; color: #999999;")
        footer_layout.addWidget(company_label, alignment=Qt.AlignmentFlag.AlignRight)
        input_layout.addLayout(footer_layout)

        self.json_data = None
        self.json_viewer_dialog = None
        self.config = load_config()

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #2d2d2d;
                border: none;
                border-radius: 5px;
            }
            QProgressBar::chunk {
                background-color: #e74c3c;
                border-radius: 5px;
            }
        """)
        self.progress_bar.hide()
        input_layout.addWidget(self.progress_bar)


    def scrape_website(self):
        url = self.url_input.text()
        prompt = self.prompt_input.toPlainText()

        if not url or not prompt:
            QMessageBox.warning(self, "Warning", "Please enter both the website URL and scraping instructions.")
            return

        if not self.config["openai_api_key"]:
            QMessageBox.warning(self, "Warning", "Please enter your OpenAI API key in the settings.")
            return

        self.scrape_button.setEnabled(False)
        self.reset_button.setEnabled(False)
        self.json_text_edit.clear()
        self.view_json_button.setEnabled(False)
        self.progress_bar.setMaximum(0)
        self.progress_bar.show()

        self.scraper_thread = ScraperThread(url, prompt, self.config["openai_api_key"])
        self.scraper_thread.result_ready.connect(self.display_result)
        self.scraper_thread.error_occurred.connect(self.display_error)
        self.scraper_thread.finished.connect(self.scraping_finished)
        self.scraper_thread.start()

    def display_result(self, result):
        self.json_data = result
        self.json_text_edit.setText(json.dumps(self.json_data, indent=2))
        self.view_json_button.setEnabled(True)

    def display_error(self, error_message):
        QMessageBox.critical(self, "Error", error_message)

    def scraping_finished(self):
        self.scrape_button.setEnabled(True)
        self.reset_button.setEnabled(True)
        self.progress_bar.setMaximum(100)
        self.progress_bar.hide()

    def view_json(self):
        if self.json_data:
            if self.json_viewer_dialog is None:
                self.json_viewer_dialog = JsonViewerDialog(self.json_data)
            self.json_viewer_dialog.json_data = self.json_data
            self.json_viewer_dialog.show()

    def reset_inputs(self):
        self.url_input.clear()
        self.prompt_input.clear()
        self.json_text_edit.clear()
        self.view_json_button.setEnabled(False)
        self.json_data = None

    def open_settings(self):
        settings_dialog = SettingsDialog(self.config)
        settings_dialog.exec()
        self.config = load_config()


class SettingsDialog(QDialog):
    def __init__(self, config):
        super().__init__()
        self.setWindowTitle("Settings")
        self.setGeometry(100, 100, 400, 200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        form_group_box = QGroupBox("OpenAI API Settings")
        form_layout = QFormLayout()

        self.api_key_input = QLineEdit(config["openai_api_key"])
        form_layout.addRow("API Key:", self.api_key_input)

        form_group_box.setLayout(form_layout)
        layout.addWidget(form_group_box)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def save_settings(self):
        config = {
            "openai_api_key": self.api_key_input.text()
        }
        save_config(config)
        self.close()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScraperWindow()
    window.show()
    sys.exit(app.exec())