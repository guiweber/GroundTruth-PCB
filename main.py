import sys
import os
import argparse
from PyQt6.QtWidgets import QApplication

from app.main_window import MainWindow


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("images", nargs="*", help="0-2 image paths")

    args = parser.parse_args()

    if len(args.images) > 2:
        parser.error("At most two images may be specified")

    app = QApplication(sys.argv)
    #
    if len(args.images):
        win = MainWindow(args.images)
    else:
        win = MainWindow([os.path.expanduser(r'~/Downloads/front.jpg'), os.path.expanduser(r'~/Downloads/back.jpg')])

    win.show()

    sys.exit(app.exec())
