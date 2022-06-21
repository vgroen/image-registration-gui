import sys

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import src.ui.window

def main():
    app = QApplication(sys.argv)

    dark = False
    if dark:
        app.setStyleSheet((
            ' * { color: #d4d4d4; } '
            ' *[elevation="00dp"] { background-color: #121212; } '
            ' *[elevation="01dp"] { background-color: #1d1d1d; } '
            ' *[elevation="02dp"] { background-color: #212121; } '
            ' *[elevation="03dp"] { background-color: #232323; } '
            ' *[elevation="04dp"] { background-color: #262626; } '
            ' *[elevation="06dp"] { background-color: #2c2c2c; } '
            ' *[elevation="08dp"] { background-color: #2d2d2d; } '
            ' *[elevation="12dp"] { background-color: #323232; } '
            ' *[elevation="16dp"] { background-color: #343434; } '
            ' *[elevation="24dp"] { background-color: #373737; } '
            ' *[selected="true"] { background-color: #2cfc2c } '
        ))

    window = src.ui.window.Window.getInstance()
    window.setWindowTitle("Image Alignment Tool")

    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

