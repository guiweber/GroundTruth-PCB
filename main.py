import sys
import argparse
from PyQt6.QtWidgets import QApplication

from app.main_window import MainWindow


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*", help="Optional paths to one ground truth document (.gtd) or 1-2 images")

    args = parser.parse_args()

    if len(args.files) > 2:
        parser.error("At most two images or one .gtd file may be specified")

    app = QApplication(sys.argv)

    win = MainWindow(args.files)
    win.show()

    sys.exit(app.exec())
