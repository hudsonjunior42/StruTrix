import os
import sys
import ctypes
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from gui.main_window import StruTrixMainWindow

# Retorna o caminho absoluto do arquivo para acesso a recursos.
def resource_path(relative_path):
    try:
        # Pega o caminho de onde o PyInstaller extraiu os arquivos temporariamente
        base_path = sys._MEIPASS
    except Exception:
        # Pega o caminho base do arquivo (modo de desenvolvimento)
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def main():
    # Configuração para o ícone aparecer corretamente na barra de tarefas do Windows
    try:
        myappid = u"StruTrix.App.0.76"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except:
        pass

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path('icon.png')))
    
    window = StruTrixMainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()