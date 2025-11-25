import sys
import ctypes
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from gui.main_window import StruTrixMainWindow

def main():
    # Configuração para o ícone aparecer corretamente na barra de tarefas do Windows
    try:
        myappid = u"StruTrix.App.0.86"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except:
        pass

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.png"))
    
    window = StruTrixMainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()