from PyQt6.QtWidgets import QMessageBox, QApplication


def error_info(title: str, message: str):
    """
    Show a modal error dialog to the user.
    """
    app = QApplication.instance()
    if app is None:
        # Fallback for very early errors (CLI / startup)
        print(f"[ERROR] {title}: {message}")
        return

    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.exec()