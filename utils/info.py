from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser
from pathlib import Path


# Displays the markdown help file inside the app
class HelpInfo(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help")
        self.resize(700, 500)

        view = QTextBrowser()
        view.setOpenExternalLinks(True)
        view.setStyleSheet("""
        QTextBrowser {
            font-size: 13pt;
        }
        """)

        md_path = Path(__file__).parent.parent / "help.md"
        view.setMarkdown(self._load_markdown(md_path))

        layout = QVBoxLayout(self)
        layout.addWidget(view)

    @staticmethod
    def _load_markdown(path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            return "### Error: Unable to load help.md"