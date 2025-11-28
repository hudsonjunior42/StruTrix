import os
import sys
import pandas as pd
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QFormLayout, QLabel, QLineEdit, QPushButton, QComboBox,
    QCheckBox, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView,
    QDoubleSpinBox, QAction, QFileDialog,
)
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

# IMPORTA OS MÓDULOS
from core.solver import StructuralSolver    # Importa o programa de calculo
from core.data_handler import DataHandler   # Importa o gerenciador de dados
from core.file_manager import FileManager   # Importa o gerenciador de arquivos
from graphics.plotter import StructuralPlotter, MatplotlibCanvas    # Importa o criador de diagramas

# Retorna o caminho absoluto do arquivo para acesso a recursos.
def resource_path(relative_path):
    try:
        # Pega o caminho de onde o PyInstaller extraiu os arquivos temporariamente
        base_path = sys._MEIPASS
    except Exception:
        # Pega o caminho base do arquivo (modo de desenvolvimento)
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Classe da janela do progama
class StruTrixMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Configurações da janela
        self.title = "StruTrix"
        self.setWindowTitle(self.title)
        self.setGeometry(100, 100, 1000, 600)                                                       # Tamanho da janela (x, y, largura, altura)
        self.setWindowIcon(QIcon(resource_path('icon.png')))
        self.setWindowFlags(Qt.Window)

        # INICIALIZA CLASSES AUXILIARES
        self.data_handler = DataHandler()  # Instância dos dados
        self.solver = StructuralSolver()
        self.plotter = None

        # --- INICIALIZAÇÃO DOS ATRIBUTOS DE ESTADO ---
        self.current_view = "Visualização"  # Valor padrão
        self.show_grid = True               # Valor padrão
        self.count_nodes = True          # Valor padrão
        self.count_bars = True           # Valor padrão
        self.show_reactions = True           # Valor padrão
        self.data_handler.analysis_results = None        # Sem resultados inicialmente
        
        self.init_ui()
        self.update_all_widgets()
        self.update_plot()

    def init_ui(self):
        
        # Barra de Menu
        self.create_menubar()

        # Layout Principal
        main_layout = QHBoxLayout()                                                                 # Layout horizontal
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Painel esquerdo (Manipulação dos dados de entrada)
        left_panel = QVBoxLayout()
        
        self.tabs = QTabWidget()                                                                    # Abas
        self.create_tabs()
        left_panel.addWidget(self.tabs)                                                             # Adiciona as abas ao painel esquerdo

        self.run_analysis_button = QPushButton("Calcular")                                          # Botão Calcular
        self.run_analysis_button.setFont(QFont('Arial', 12, QFont.Bold))
        self.run_analysis_button.clicked.connect(self.run_analysis)                                 # Roda a análise quando clicado
        left_panel.addWidget(self.run_analysis_button)

        # Painel direito (Plotagem)
        right_panel_widget = QWidget()
        right_panel_layout = QVBoxLayout(right_panel_widget)

        ## Grupo Janelas de visualização
        view_buttons_group = QGroupBox("Controle de Visualização")
        view_buttons_layout = QHBoxLayout()
        view_buttons_layout.setContentsMargins(2, 2, 2, 2)
        view_buttons_layout.setSpacing(5)

        ## Janelas de visualização
        views =["Visualização", 
                "Diagrama de Esforços Normais",
                "Diagrama de Esforços Cisalhantes",
                "Diagrama de Momento Fletor",
                "Deformação"]
        
        ### Cria os botões de visualização
        for view in views:
            btn = QPushButton(view)
            btn.clicked.connect(lambda checked, v=view: self.switch_view(v))                        # Altera o diagrama quando clicado
            view_buttons_layout.addWidget(btn)

        view_buttons_group.setLayout(view_buttons_layout)
        view_buttons_group.setMaximumHeight(50)                                                     # Altura máxima da caixa
        right_panel_layout.addWidget(view_buttons_group)
        
        # Na parte do Canvas:
        self.canvas = MatplotlibCanvas(self, width=8, height=6, dpi=100)
        self.plotter = StructuralPlotter(self.canvas) # Cria o plotter
        
        right_panel_layout.addWidget(self.canvas)

        # Adiciona os paineis esquerdo e direito para a janela principal
        main_layout.addLayout(left_panel, stretch=1)
        main_layout.addWidget(right_panel_widget, stretch=2)

    # --- Menu ---
    def create_menubar(self):
        menu_bar = self.menuBar()

        # Menu File
        file_menu = menu_bar.addMenu("&Arquivo")

        ## Sobre
        about_action = QAction("Sobre", self)
        about_action.triggered.connect(self.about_dialog)
        file_menu.addAction(about_action)

        ## -
        file_menu.addSeparator()
        
        ## Novo
        new_action = QAction("&Novo", self)
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        ## Abrir
        open_action = QAction("&Abrir", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        ## Salvar
        save_action = QAction("&Salvar", self)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        ## Salvar como
        save_as_action = QAction("Salvar &Como...", self)
        save_as_action.triggered.connect(self._save_to_path)
        file_menu.addAction(save_as_action)

        ## -
        file_menu.addSeparator()

        ## Exportar reações nos nós
        export_values_action = QAction("Salvar Reações", self)
        export_values_action.triggered.connect(self.export_values)
        file_menu.addAction(export_values_action)
        
        ## -
        file_menu.addSeparator()

        ## Sair
        exit_action = QAction("&Sair", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menu View
        view_menu = menu_bar.addMenu("&Visualização")

        ## Numerar Nós
        count_nodes_action = QAction("Numerar Nós", self, checkable=True, checked = True)
        count_nodes_action.triggered.connect(self.count_nodes_toggle)
        view_menu.addAction(count_nodes_action)
        
        ## Numerar Barras
        count_bars_action = QAction("Numerar Barras", self, checkable=True, checked = True)
        count_bars_action.triggered.connect(self.count_bars_toggle)
        view_menu.addAction(count_bars_action)

        ## Mostrar Grid
        show_grid_action = QAction("Mostrar Grid", self, checkable=True, checked = True)
        show_grid_action.triggered.connect(self.show_grid_toggle)
        view_menu.addAction(show_grid_action)

        ## Mostrar Reações de apoio
        show_reactions_action = QAction("Mostrar Reações de Apoio", self, checkable=True, checked = True)
        show_reactions_action.triggered.connect(self.show_reactions_toggle)
        view_menu.addAction(show_reactions_action)

        ## -
        view_menu.addSeparator()
        
        ## Resetar visuazlização
        resetview_action = QAction("&Resetar", self)
        resetview_action.triggered.connect(self.update_plot)
        view_menu.addAction(resetview_action)
        
        ### Pan / Zoom group
        
        ## Pan
        self.panview_action = QAction("&Pan", self, checkable=True, checked = True)
        self.panview_action.triggered.connect(self.pan_view)
        view_menu.addAction(self.panview_action)

        ## Zoom
        self.zoomview_action = QAction("&Zoom", self, checkable=True, checked = False)
        self.zoomview_action.triggered.connect(self.zoom_view)
        view_menu.addAction(self.zoomview_action)

        ## Salvar Diagrama
        saveview_action = QAction("Salvar &Diagrama", self)
        saveview_action.triggered.connect(self.save_view)
        view_menu.addAction(saveview_action)

        # Menu Options
        options_menu = menu_bar.addMenu("&Opções")
    
    # --- Abas ---
    def create_tabs(self):                                                                          # Cria todas as abas
        # Nós
        self.tab_nodes = QWidget()
        self.tabs.addTab(self.tab_nodes, "Nós")
        self.create_nodes_tab()

        # Barras
        self.tab_bars = QWidget()
        self.tabs.addTab(self.tab_bars, "Barras")
        self.create_bars_tab()

        # Apoios
        self.tab_supports = QWidget()
        self.tabs.addTab(self.tab_supports, "Apoios")
        self.create_supports_tab()

        # Cargas Nodais
        self.tab_nodal_loads = QWidget()
        self.tabs.addTab(self.tab_nodal_loads, "Cargas Nodais")
        self.create_nodal_loads_tab()

        # Cargas Distribuidas
        self.tab_bar_loads = QWidget()
        self.tabs.addTab(self.tab_bar_loads, "Cargas Distribuidas")
        self.create_bar_loads_tab()

        # Deslocamentos
        self.tab_prescribed_disp = QWidget()
        self.tabs.addTab(self.tab_prescribed_disp, "Desloc. Prescritos")
        self.create_prescribed_disp_tab()

    ## Aba Nós
    def create_nodes_tab(self):
        layout = QVBoxLayout(self.tab_nodes)
        form_group = QGroupBox("Adicionar / Modificar Nó")
        form_layout = QFormLayout()
        form_group.setLayout(form_layout)

        # Seletor de Nó
        self.node_selector = QComboBox()
        self.node_selector.addItem("Novo Nó")
        self.node_selector.currentIndexChanged.connect(self.on_node_select)
        
        # Coordenada X
        self.node_x = QDoubleSpinBox()
        self.node_x.setRange(-1000, 1000)
        self.node_x.setDecimals(2)

        # Coordenada Y
        self.node_y = QDoubleSpinBox()
        self.node_y.setRange(-1000, 1000)
        self.node_y.setDecimals(2)
        
        # Adicionar itens ao grupo 
        form_layout.addRow("Selecionar Nó:", self.node_selector)
        form_layout.addRow("Coordenada X (m):", self.node_x)
        form_layout.addRow("Coordenada Y (m)", self.node_y)
        
        # Botão Adicionar / Modificar Nó
        self.add_node_button = QPushButton("Adicionar / Modificar Nó")
        self.add_node_button.clicked.connect(self.add_update_node)
        
        # Botão Deletar Nó
        self.delete_node_button = QPushButton("Deletar Nó")
        self.delete_node_button.clicked.connect(self.delete_node)

        # Tabela de Nós
        self.nodes_table = QTableWidget()
        self.nodes_table.setColumnCount(3)
        self.nodes_table.setHorizontalHeaderLabels(['Nó', 
                                                    'X (m)', 
                                                    'Y(m)'])
        self.nodes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.nodes_table.verticalHeader().setVisible(False)

        # Adiciona Widgets para a aba
        layout.addWidget(form_group)
        layout.addWidget(self.add_node_button)
        layout.addWidget(self.delete_node_button)
        layout.addWidget(QLabel("Nós Existentes:"))
        layout.addWidget(self.nodes_table)

    ## Aba Barras
    def create_bars_tab(self):
        layout = QVBoxLayout(self.tab_bars)
        form_group = QGroupBox("Adicionar / Modificar Barra")
        form_layout = QFormLayout()
        form_group.setLayout(form_layout)

        # Seletor de Barra
        self.bar_selector = QComboBox()
        self.bar_selector.addItem("Nova Barra")
        self.bar_selector.currentIndexChanged.connect(self.on_bar_select)

        # Nó inicial e final
        self.inital_node_selector = QComboBox()
        self.final_node_selector = QComboBox()

        # Propriedades
        self.bar_E = QLineEdit('200e6')
        self.bar_A = QLineEdit('0.01')
        self.bar_I = QLineEdit('8e-5')
        self.rot_i = QCheckBox('Liberar Rotação (Nó i)')
        self.rot_j = QCheckBox('Liberar Rotação (Nó j)')

        # Adicionar itens ao grupo 
        form_layout.addRow("Selecionar Barra:", self.bar_selector)
        form_layout.addRow("Nó inicial (i):", self.inital_node_selector)
        form_layout.addRow("Nó final (j)", self.final_node_selector)
        form_layout.addRow("Elasticidade E (kN/m²)", self.bar_E)
        form_layout.addRow("Área A (m²)", self.bar_A)
        form_layout.addRow("Inércia I (m⁴)", self.bar_I)
        form_layout.addRow(self.rot_i)
        form_layout.addRow(self.rot_j)

        # Botão Adicionar / Modificar Barra
        self.add_bar_button = QPushButton("Adicionar / Modificar Barra")
        self.add_bar_button.clicked.connect(self.add_update_bar)
        
        # Botão Deletar Nó
        self.delete_bar_button = QPushButton("Deletar Barra")
        self.delete_bar_button.clicked.connect(self.delete_bar)

        # Tabela de barras
        self.bars_table = QTableWidget()
        self.bars_table.setColumnCount(8)
        self.bars_table.setHorizontalHeaderLabels(['Barra', 
                                                   'Nó i', 
                                                   'Nó j', 
                                                   'E (kPa)', 
                                                   'A (m²)', 
                                                   'I (m⁴)', 
                                                   'Rot i', 
                                                   'Rot j'])
        self.bars_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)  
        self.bars_table.verticalHeader().setVisible(False)

        # Adiciona Widgets para a aba
        layout.addWidget(form_group)
        layout.addWidget(self.add_bar_button)
        layout.addWidget(self.delete_bar_button)
        layout.addWidget(QLabel("Barras Existentes:"))
        layout.addWidget(self.bars_table)              

    ## Aba Apoios
    def create_supports_tab(self):
        layout = QVBoxLayout(self.tab_supports)
        form_group = QGroupBox("Adicionar / Modificar Apoio")
        form_layout = QFormLayout()
        form_group.setLayout(form_layout)

        # Seletor de Nó
        self.support_node_selector = QComboBox()
        self.support_node_selector.currentIndexChanged.connect(self.on_support_node_select)

        # Restrição em X
        self.support_restr_x = QCheckBox("Restrição em X")

        # Restrição em Y
        self.support_restr_y = QCheckBox("Restrição em Y")

        # Restrição em Rz
        self.support_restr_rz = QCheckBox("Restrição na Rotação em Z")

        # Rotação
        self.support_rotation = QComboBox()
        self.support_rotation.addItems(["0°", 
                                        "90°", 
                                        "180°", 
                                        "270°"])

        # Adicionar itens ao grupo
        form_layout.addRow("Selecionar Nó:", self.support_node_selector)
        form_layout.addRow(self.support_restr_x)
        form_layout.addRow(self.support_restr_y)
        form_layout.addRow(self.support_restr_rz)
        form_layout.addRow("Rotação:", self.support_rotation)

        # Botão Aplicar / Atualizar Apoio
        self.apply_support_button = QPushButton("Aplicar / Atualizar Apoio")
        self.apply_support_button.clicked.connect(self.apply_support_load)  
        
        # Tabela de Apoios
        self.support_table = QTableWidget()
        self.support_table.setColumnCount(5)
        self.support_table.setHorizontalHeaderLabels(["Nó", 
                                                      "Restr. X", 
                                                      "Restr. Y", 
                                                      "Restr. Rz", 
                                                      "Rotação"])
        self.support_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.support_table.verticalHeader().setVisible(False)

        # Adicionar Widgets para a aba
        layout.addWidget(form_group)
        layout.addWidget(self.apply_support_button)
        layout.addWidget(QLabel("Apoios Existentes:"))
        layout.addWidget(self.support_table)
    
    ## Cargas Nodais
    def create_nodal_loads_tab(self):
        layout = QVBoxLayout(self.tab_nodal_loads)
        form_group = QGroupBox("Aplicar Carga em Nó")
        form_layout = QFormLayout()
        form_group.setLayout(form_layout)

        # Seletor de Nó
        self.load_node_selector = QComboBox()
        self.load_node_selector.currentIndexChanged.connect(self.on_nodal_load_select)

        # Carga Fx
        self.nodal_load_fx = QDoubleSpinBox()
        self.nodal_load_fx.setRange(-1e6, 1e6)
        self.nodal_load_fx.setDecimals(2)     

        # Carga Fy
        self.nodal_load_fy = QDoubleSpinBox()
        self.nodal_load_fy.setRange(-1e6, 1e6)
        self.nodal_load_fy.setDecimals(2)      

        # Carga Mz
        self.nodal_load_mz = QDoubleSpinBox()
        self.nodal_load_mz.setRange(-1e6, 1e6)
        self.nodal_load_mz.setDecimals(2)      

        # Adicionar itens ao grupo 
        form_layout.addRow("Selecionar Nó:", self.load_node_selector)
        form_layout.addRow("Carga Fx (kN):", self.nodal_load_fx)
        form_layout.addRow("Carga Fy (kN)", self.nodal_load_fy)         
        form_layout.addRow("Momento Mz (kN.m)", self.nodal_load_mz)

        # Botão Aplicar / Atualizar Carga
        self.apply_nodal_load_button = QPushButton("Aplicar / Atualizar Carga")
        self.apply_nodal_load_button.clicked.connect(self.apply_nodal_load)           

        # Tabela de Carregamentos Nodais
        self.nodal_load_table = QTableWidget()
        self.nodal_load_table.setColumnCount(4)
        self.nodal_load_table.setHorizontalHeaderLabels(['Nó', 
                                                         'Fx (kN)', 
                                                         'Fy (kN)', 
                                                         'Mz (kN.m)'])
        self.nodal_load_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.nodal_load_table.verticalHeader().setVisible(False)

        # Adiciona Widgets para a aba
        layout.addWidget(form_group)
        layout.addWidget(self.apply_nodal_load_button)
        layout.addWidget(QLabel("Cargas Existentes:"))
        layout.addWidget(self.nodal_load_table)

    ## Aba Cargas Distribuidas
    def create_bar_loads_tab(self):
        layout = QVBoxLayout(self.tab_bar_loads)
        form_group = QGroupBox("Aplicar Carga Distribuída na Barra (Perpendicular)")
        form_layout = QFormLayout()
        form_group.setLayout(form_layout)

        # Seletor de Barra
        self.load_bar_selector = QComboBox()
        self.load_bar_selector.currentIndexChanged.connect(self.on_bar_loads_select)

        # Carga Q
        self.load_bar_q = QDoubleSpinBox()
        self.load_bar_q.setRange(-1e6, 1e6)
        self.load_bar_q.setDecimals(2) 

        # Adicionar itens ao grupo
        form_layout.addRow("Selecionar Barra:", self.load_bar_selector)
        form_layout.addRow("Carga 'Q' (kN/m):", self.load_bar_q)

        # Botão Aplicar / Atualizar Carga
        self.apply_bar_load_button = QPushButton("Aplicar / Atualizar Carga")
        self.apply_bar_load_button.clicked.connect(self.apply_bar_load)

        # Tabela de Carregamentos Distribuídos
        self.bar_load_table = QTableWidget()
        self.bar_load_table.setColumnCount(2)
        self.bar_load_table.setHorizontalHeaderLabels(['Barra', 'Carga Q (kN/m)'])
        self.bar_load_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.bar_load_table.verticalHeader().setVisible(False)

        # Adicionar Widgets para a aba
        layout.addWidget(form_group)
        layout.addWidget(self.apply_bar_load_button)
        layout.addWidget(self.bar_load_table)

    ## Aba Desloc. Prescritos
    def create_prescribed_disp_tab(self):
        layout = QVBoxLayout(self.tab_prescribed_disp)
        form_group = QGroupBox("Aplicar Deslocamento Prescrito")
        form_layout = QFormLayout()
        form_group.setLayout(form_layout)

        # Seletor de Nó
        self.disp_node_selector = QComboBox()
        self.disp_node_selector.currentIndexChanged.connect(self.on_disp_node_select)

        # Deslocamento X
        self.disp_x = QDoubleSpinBox()
        self.disp_x.setRange(-1e6, 1e6)
        self.disp_x.setDecimals(5)     

        # Deslocamento Y
        self.disp_y = QDoubleSpinBox()
        self.disp_y.setRange(-1e6, 1e6)
        self.disp_y.setDecimals(5)      

        # Deslocamento Rz
        self.disp_rz = QDoubleSpinBox()
        self.disp_rz.setRange(-1e6, 1e6)
        self.disp_rz.setDecimals(5)     

        # Adicionar itens ao grupo 
        form_layout.addRow("Selecionar Nó:", self.disp_node_selector)
        form_layout.addRow("Desloc. X (m):", self.disp_x)
        form_layout.addRow("Desloc. Y (m)", self.disp_y)         
        form_layout.addRow("Rotação Rz (rad)", self.disp_rz)

        # Botão Aplicar / Atualizar Deslocamento
        self.apply_disp_button = QPushButton("Aplicar / Atualizar Deslocamento")
        self.apply_disp_button.clicked.connect(self.apply_prescribed_disp)           

        # Tabela de Deslocamentos
        self.disp_table = QTableWidget()
        self.disp_table.setColumnCount(4)
        self.disp_table.setHorizontalHeaderLabels(['Nó', 
                                                   'X (m)', 
                                                   'Y (m)', 
                                                   'Rz (rad)'])
        self.disp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.disp_table.verticalHeader().setVisible(False)

        # Adiciona Widgets para a aba
        layout.addWidget(form_group)
        layout.addWidget(self.apply_disp_button)
        layout.addWidget(QLabel("Deslocamentos Existentes:"))
        layout.addWidget(self.disp_table)

    # --- Funções de Manipulação de Arquivos e Dados ---
    
    # Inicia os dados
    def init_data(self):
        # Dados de um Nó
        self.node_cols = ["X", 
                     "Y", 
                     "Fx", 
                     "Fy", 
                     "Mz", 
                     "Restr_X", 
                     "Restr_Y", 
                     "Restr_Rz", 
                     "Restr_Rot", 
                     "Disp_X", 
                     "Disp_Y", 
                     "Disp_Rz"]
        self.data_handler.nodes_df = pd.DataFrame(columns=self.node_cols)

        # Dados de uma Barra
        self.bar_cols = ["node_i", 
                        "node_j", 
                        "E", 
                        "A", 
                        "I", 
                        "Q", 
                        "rot_i", 
                        "rot_j"]
        self.data_handler.bars_df = pd.DataFrame(columns=self.bar_cols)

        # Sem análise e sem local do arquivo
        self.data_handler.analysis_results = None
        self.current_filepath = None

    def about_dialog(self):
        github_url = "https://github.com/hudsonjunior42/StruTrix"
        message = (
        "<h2>StruTrix - Análise Estrutural Matricial</h2>"
        "<p>Software desenvolvido como Trabalho de Conclusão de Curso (TCC) de Engenharia Civil.</p>"
        "<hr>"
        f"<p>Método de Análise: Método da Rigidez (FEM) para pórticos planos.</p>"
        f"<p>Tecnologias: Python, PyQt5, Numpy, Pandas, Matplotlib.</p>"
        "<hr>"
        f"<p>Autor: Hudson Santos Menezes Júnior</p>"
        f"<p>Instituição: Instituto Federal de Sergipe</p>"
        f"<p>Código-Fonte (GitHub): <a href='{github_url}'>Acessar Repositório</a></p>"
        f"<p>Versão Atual: v0.76.1-alpha</p>"
    )
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText(message)
        msg.setWindowTitle("Sobre")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        retval = msg.exec()
        
    
    def new_file(self):
        self.data_handler.init_data()
        self.update_all_widgets()
        self.update_plot()
        self.switch_view("Visualização")
        self.openfilepath = None

    # Transformar os dados de entrada (nodes_df e bars_df) em um único dicionário
    def data_to_save(self):
        self.data_dict = {
            "nodes": self.data_handler.nodes_df.to_dict(orient='records'),
            "bars": self.data_handler.bars_df.to_dict(orient='records')
        }
    
    def open_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Abrir", "", "StruTrix (*.stx)")
        if filepath:
            # 1. FileManager lê o arquivo do disco
            success_file, file_data = FileManager.load_file(filepath)
            
            if success_file:
                # 2. DataHandler carrega os dados brutos para os DataFrames
                success_data, msg = self.data_handler.load_from_dict(file_data)
                
                if success_data:
                    self.openfilepath = filepath
                    self.update_all_widgets()
                    self.update_plot()
                    self.switch_view("Visualização")
                else:
                     QMessageBox.critical(self, "Erro nos Dados", msg)
            else:
                QMessageBox.critical(self, "Erro ao Abrir", file_data)

    def save_file(self):
        filepath = self.openfilepath
        if filepath:
           self.save_as_file(filepath)
        else:
           self._save_to_path()

    def save_as_file(self, filepath):
        # 1. Pega os dados formatados do DataHandler
        data_to_save = self.data_handler.get_dict_data()
        
        # 2. Manda o FileManager salvar no disco
        success, msg = FileManager.save_file(filepath, data_to_save)
        
        if not success:
             QMessageBox.critical(self, "Erro", msg)

    def _save_to_path(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Salvar Arquivo", "", "StruTrix File (*.stx)")
        if filepath:
            self.save_as_file(filepath)
            self.openfilepath = filepath


    def export_values(self, filepath):
        print()

    # --- Funções da Toolbox de Visualização ---

    # Permitir arrastar com mouse
    def pan_view(self):
        if hasattr(self.canvas, 'toolbar'):
            self.canvas.toolbar.pan()
            self.zoomview_action.setChecked(False)

    # Habilita zoom (botão direito do mouse)
    def zoom_view(self):
        if hasattr(self.canvas, 'toolbar'):
            self.canvas.toolbar.zoom()
            self.panview_action.setChecked(False)

    # Salva visualização atual como imagem
    def save_view(self):
        if hasattr(self.canvas, 'toolbar'):
            self.canvas.toolbar.save_figure()

    # Alterar Numeração de nós
    def count_nodes_toggle(self):
        if self.count_nodes:
            self.count_nodes = False
        else:
            self.count_nodes = True
        
        self.update_plot()

    # Alterar Numeração de barras
    def count_bars_toggle(self):
        if self.count_bars:
            self.count_bars = False
        else:
            self.count_bars = True

        self.update_plot()

    # Alterar Exibição de Grid
    def show_grid_toggle(self):
        if self.show_grid:
            self.show_grid = False
        else:
            self.show_grid = True

        self.update_plot()

    # Alterar Exibição das reações de apoio
    def show_reactions_toggle(self):
        if self.show_reactions:
            self.show_reactions = False
        else:
            self.show_reactions = True

        self.update_plot()

    # --- Funções de população de tabelas

    def update_all_widgets(self):
        # Definição da numeração dos nós e barrras
        node_id = [f"Nó {i+1}" for i in self.data_handler.nodes_df.index]
        bar_id = [f"Barra {i+1}" for i in self.data_handler.bars_df.index]

        # Seletores
        ## Seletores de nós
        node_selectors = [self.node_selector,
                          self.inital_node_selector,
                          self.final_node_selector,
                          self.load_node_selector, 
                          self.support_node_selector, 
                          self.disp_node_selector]
        for selector in node_selectors:
            selector.blockSignals(True)                     # Desativa a funcionalidade ao selecionar o item
            current_text = selector.currentText()
            selector.clear()
            
            # Opção de novo nó somente na aba nós
            if selector is self.node_selector:
                selector.addItem("Novo Nó")
            
            # Adiciona a numeração dos nós
            selector.addItems([str(i) for i in node_id])
            index = selector.findText(current_text)
            
            # Desativa seleção se não houver mais o item
            if index != -1:
                selector.setCurrentIndex(index)
            else:
                selector.setCurrentIndex(-1)
            
            selector.blockSignals(False)                    # Ativa a funcionalidade ao selecionar o item

        ## Seletores de barras
        bar_selector = [self.bar_selector, self.load_bar_selector]
        for selector in bar_selector:
            selector.blockSignals(True)                     # Desativa a funcionalidade ao selecionar o item
            current_text = selector.currentText()
            selector.clear()

            # Opção de nova barra somente na aba barra
            if selector is self.bar_selector:
                selector.addItem("Nova Barra")
            
            # Adiciona a numeração dos nós
            selector.addItems([str(i) for i in bar_id])
            index = selector.findText(current_text)
            
            # Desativa seleção se não houver mais o item
            if index != -1:
                selector.setCurrentIndex(index)
            else:
                selector.setCurrentIndex(-1)
            
            selector.blockSignals(False)                    # Ativa a funcionalidade ao selecionar o item

        # Chama as funções de seleção para o item selecionado
        self.on_node_select(self.node_selector.currentIndex())
        self.on_bar_select(self.bar_selector.currentIndex())
        self.on_support_node_select(self.support_node_selector.currentIndex())

        # Chama as funções individuais de população de tabelas para atualiza-las
        self.populate_nodes_table()
        self.populate_bars_table()
        self.populate_nodal_loads_table()
        self.populate_bar_load_table()
        self.populate_supports_table()
        self.populate_disp_table()

    # Popular tabela de nós
    def populate_nodes_table(self):
        df = self.data_handler.nodes_df 
        self.nodes_table.setRowCount(len(df))
        for i, row in df.iterrows():
            self.nodes_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.nodes_table.setItem(i, 1, QTableWidgetItem(f"{row['X']:.2f}"))
            self.nodes_table.setItem(i, 2, QTableWidgetItem(f"{row['Y']:.2f}"))
            pass

    # Popular tabela de barras
    def populate_bars_table(self):
        df = self.data_handler.bars_df 
        self.bars_table.setRowCount(len(df))
        for i, row in df.iterrows():
            self.bars_table.setItem(i, 0, QTableWidgetItem(str(i+1)))
            self.bars_table.setItem(i, 1, QTableWidgetItem(f"{row['node_i']+1}"))
            self.bars_table.setItem(i, 2, QTableWidgetItem(f"{row['node_j']+1}"))
            self.bars_table.setItem(i, 3, QTableWidgetItem(f"{row['E']:.2e}"))
            self.bars_table.setItem(i, 4, QTableWidgetItem(f"{row['A']:.5f}"))
            self.bars_table.setItem(i, 5, QTableWidgetItem(f"{row['I']:.2e}"))
            self.bars_table.setItem(i, 6, QTableWidgetItem("\U00002714" if row['rot_i'] else "\U0000274C"))
            self.bars_table.setItem(i, 7, QTableWidgetItem("\U00002714" if row['rot_j'] else "\U0000274C"))

    # Popular tabela de carregamentos nodais
    def populate_nodal_loads_table(self):
        df = self.data_handler.nodes_df 
        self.nodal_load_table.setRowCount(len(df))
        for i, row in df.iterrows():
            self.nodal_load_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.nodal_load_table.setItem(i, 1, QTableWidgetItem(f"{row['Fx']:.2f}"))
            self.nodal_load_table.setItem(i, 2, QTableWidgetItem(f"{row['Fy']:.2f}"))
            self.nodal_load_table.setItem(i, 3, QTableWidgetItem(f"{row['Mz']:.2f}"))

    # Popular tabela de carregamentos distribuidos
    def populate_bar_load_table(self):
        df = self.data_handler.bars_df 
        self.bar_load_table.setRowCount(len(df))
        for i, row in df.iterrows():
            self.bar_load_table.setItem(i, 0, QTableWidgetItem(str(i+1)))
            self.bar_load_table.setItem(i, 1, QTableWidgetItem(f"{row['Q']:.2f}"))

    # Popular tabela de apoios
    def populate_supports_table(self):
        df = self.data_handler.nodes_df 
        self.support_table.setRowCount(len(df))
        for i, row in df.iterrows():
            self.support_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.support_table.setItem(i, 1, QTableWidgetItem("\U00002714" if row['Restr_X'] else "\U0000274C"))
            self.support_table.setItem(i, 2, QTableWidgetItem("\U00002714" if row['Restr_Y'] else "\U0000274C"))
            self.support_table.setItem(i, 3, QTableWidgetItem("\U00002714" if row['Restr_Rz'] else "\U0000274C"))
            self.support_table.setItem(i, 4, QTableWidgetItem(f"{row['Restr_Rot']}°"))


            "\U00002714" if row['Restr_X'] else "\U0000274C"

    # Popular tabela de deslocamentos prescritos
    def populate_disp_table(self):
        df = self.data_handler.nodes_df 
        self.disp_table.setRowCount(len(df))
        for i, row in df.iterrows():
            self.disp_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.disp_table.setItem(i, 1, QTableWidgetItem(f"{row['Disp_X']}"))
            self.disp_table.setItem(i, 2, QTableWidgetItem(f"{row['Disp_Y']}"))
            self.disp_table.setItem(i, 3, QTableWidgetItem(f"{row['Disp_Rz']}"))

    # --- Funções de Callback

    # Ao selecionar o nó (Aba Nós)
    # Usar valores do dataframe
    def on_node_select(self, index):
        if index >= 1:
            node_idx = index - 1
            node_data = self.data_handler.nodes_df.iloc[node_idx]
            self.node_x.setValue(node_data['X'])
            self.node_y.setValue(node_data['Y'])
        else:
            self.node_x.setValue(0)
            self.node_y.setValue(0)

    # Ao selecionar a barra (Aba Barra)
    # Usar valores do dataframe
    def on_bar_select(self, index):
        if index >= 1:
            bar_idx = index-1
            bar_data = self.data_handler.bars_df.iloc[bar_idx]
            self.inital_node_selector.setCurrentIndex(bar_data['node_i'])
            self.final_node_selector.setCurrentIndex(bar_data['node_j'])
            self.bar_E.setText(str(f"{bar_data['E']:.2e}"))
            self.bar_A.setText(str(f"{bar_data['A']:.2e}"))
            self.bar_I.setText(str(f"{bar_data['I']:.2e}"))
            self.rot_i.setChecked(bool(bar_data['rot_i']))
            self.rot_j.setChecked(bool(bar_data['rot_j']))
        else:
            self.inital_node_selector.setCurrentIndex(-1)
            self.final_node_selector.setCurrentIndex(-1)
            self.bar_E.setText('200e6')
            self.bar_A.setText('0.01')
            self.bar_I.setText('8e-5')
            self.rot_i.setChecked(False)
            self.rot_j.setChecked(False)

    # Ao selecionar o nó (Aba Cargas Nodais)
    # Usar valores do dataframe
    def on_nodal_load_select(self, index):
        if index >= 0:
            node_idx = index
            node_data = self.data_handler.nodes_df.iloc[node_idx]
            self.nodal_load_fx.setValue(node_data['Fx'])
            self.nodal_load_fy.setValue(node_data['Fy'])
            self.nodal_load_mz.setValue(node_data['Mz'])
        else:
            self.nodal_load_fx.setValue(0)
            self.nodal_load_fy.setValue(0)
            self.nodal_load_mz.setValue(0)

    # Ao selecionar a barra (Aba Cargas Distribuidas)
    # Usar valores do dataframe
    def on_bar_loads_select(self, index):
        if index >= 0:
            bar_idx = index
            bar_data = self.data_handler.bars_df.iloc[bar_idx]
            self.load_bar_q.setValue(bar_data['Q'])
        else:
            self.load_bar_q.setValue(0)

    # Ao selecionar o nó (Aba Apoios)
    # Usar valores do dataframe
    def on_support_node_select(self, index):
        if index >= 0:
            node_idx = index
            node_data = self.data_handler.nodes_df.iloc[node_idx]
            self.support_restr_x.setChecked(bool(node_data['Restr_X']))
            self.support_restr_y.setChecked(bool(node_data['Restr_Y']))
            self.support_restr_rz.setChecked(bool(node_data['Restr_Rz']))
            rotation = node_data.get('Restr_Rot', 0)
            if rotation in [0, 90, 180, 270]:
                self.support_rotation.setCurrentIndex(int(rotation / 90))
        else:
            self.support_restr_x.setChecked(False)
            self.support_restr_y.setChecked(False)
            self.support_restr_rz.setChecked(False)
            self.support_rotation.setCurrentIndex(0)

    # Ao selecionar o nó (Aba Deslocamentos Prescritos)
    # Usar valores do dataframe
    def on_disp_node_select(self, index):
        if index >= 0:
            node_idx = index
            node_data = self.data_handler.nodes_df.iloc[node_idx]
            self.disp_x.setValue(node_data['Disp_X'])
            self.disp_y.setValue(node_data['Disp_Y'])
            self.disp_rz.setValue(node_data['Disp_Rz'])
        else:
            self.disp_x.setValue(0)
            self.disp_y.setValue(0)
            self.disp_rz.setValue(0)

    # --- Modificações dos dados ---

    # Adicionar / Atualizar nó
    def add_update_node(self):
        current_index = self.node_selector.currentIndex()
        x = self.node_x.value()
        y = self.node_y.value()
        
        # Caso 1: Novo Nó (Índice 0 no combobox)
        if current_index == 0:
            success, msg = self.data_handler.add_node(x, y)
        # Caso 2: Atualizar Nó existente (Índice no combobox - 1 = Índice no DataFrame)
        else:
            success, msg = self.data_handler.update_node_coords(current_index - 1, x, y)

        if not success:
            QMessageBox.warning(self, "Aviso", msg)
            return

        self.update_all_widgets()
        self.update_plot()
    
    # Deletar Nó
    def delete_node(self):
        current_index = self.node_selector.currentIndex()
        
        if current_index == 0:
            return # Nada selecionado para deletar

        success, msg = self.data_handler.delete_node(current_index - 1)
        
        if not success:
            QMessageBox.warning(self, "Erro", msg)

        # Reseta a seleção para "Novo Nó"
        self.node_selector.setCurrentIndex(0)
        self.update_all_widgets()
        self.update_plot()

    # Adicionar / Atualizar Barra
    def add_update_bar(self):
        current_index = self.bar_selector.currentIndex()

        # Prepara os dados do formulário
        bar_data = {
            "node_i": self.inital_node_selector.currentIndex(),
            "node_j": self.final_node_selector.currentIndex(),
            "E": float(self.bar_E.text()),
            "A": float(self.bar_A.text()),
            "I": float(self.bar_I.text()),
            "rot_i": self.rot_i.isChecked(),
            "rot_j": self.rot_j.isChecked(),
            "Q": 0 # Mantém zero na criação/edição geométrica
        }

        # Caso 1: Nova Barra
        if current_index == 0:
            success, msg = self.data_handler.add_bar(bar_data)
        # Caso 2: Atualizar Barra
        else:
            success, msg = self.data_handler.update_bar(current_index - 1, bar_data)

        if not success:
            QMessageBox.warning(self, "Aviso", msg)
            return

        self.update_all_widgets()
        self.update_plot()

    # Deletar Barra
    def delete_bar(self):
        current_index = self.bar_selector.currentIndex()
        
        if current_index == 0:
            return

        success = self.data_handler.delete_bar(current_index - 1)
        
        self.bar_selector.setCurrentIndex(0)
        self.update_all_widgets()
        self.update_plot()      
    
    # Aplicar / Atualizar Carregamentos nodais
    def apply_nodal_load(self):
        current_index = self.load_node_selector.currentIndex()
        if current_index == -1: return
        
        fx = self.nodal_load_fx.value()
        fy = self.nodal_load_fy.value()
        mz = self.nodal_load_mz.value()

        # Chama o DataHandler
        self.data_handler.update_nodal_loads(current_index, fx, fy, mz)

        self.update_all_widgets()
        self.update_plot() 

    # Aplicar / Atualizar Carregamentos distribuidos nas barras
    def apply_bar_load(self):
        current_index = self.load_bar_selector.currentIndex()
        if current_index == -1: return

        q = self.load_bar_q.value()

        # Chama o DataHandler
        self.data_handler.update_bar_load(current_index, q)

        self.update_all_widgets()
        self.update_plot()

    # Aplicar / Atualizar Apoios
    def apply_support_load(self):
        current_index = self.support_node_selector.currentIndex()
        if current_index == -1: return

        restr_x = self.support_restr_x.isChecked()
        restr_y = self.support_restr_y.isChecked()
        restr_rz = self.support_restr_rz.isChecked()
        restr_rot = self.support_rotation.currentIndex() * 90

        # Chama o DataHandler
        self.data_handler.update_supports(current_index, restr_x, restr_y, restr_rz, restr_rot)

        self.update_all_widgets()
        self.update_plot()

    # Aplica Deslocamento prescrito
    def apply_prescribed_disp(self):
        current_index = self.disp_node_selector.currentIndex()
        if current_index == -1: return

        dx = self.disp_x.value()
        dy = self.disp_y.value()
        drz = self.disp_rz.value()

        # Chama o DataHandler
        self.data_handler.update_prescribed_displacements(current_index, dx, dy, drz)

        self.update_all_widgets()
        self.update_plot()

    def run_analysis(self):
        try:
            # Passa os dataframes limpos do handler para o solver
            results = self.solver.run_analysis(
                self.data_handler.nodes_df, 
                self.data_handler.bars_df
            )
            
            # Armazena resultados no handler
            self.data_handler.analysis_results = results
            
            self.update_all_widgets()
            QMessageBox.information(self, "Sucesso", "Cálculo realizado!")

        except ValueError as ve:
            QMessageBox.warning(self, "Aviso de Cálculo", str(ve))
        except Exception as e:
            QMessageBox.critical(self, "Erro Crítico", f"Erro na análise: {str(e)}")

    # --- Funções de Plotagem e Visualização ---

    def switch_view(self, view_name):
        if view_name != 'Visualização' and self.data_handler.analysis_results is None:
            QMessageBox.information(self, "Aviso", "Execute a análise primeiro para visualizar os resultados.")
            return
        self.current_view = view_name
        self.update_plot()

    # Plotagem
    def update_plot(self):
        # DELEGA O DESENHO PARA O PLOTTER
        self.plotter.draw_structure(
            self.data_handler.nodes_df, 
            self.data_handler.bars_df, 
            self.data_handler.analysis_results, 
            self.current_view,
            self.show_grid,
            self.count_nodes,
            self.count_bars,
            self.show_reactions
        )
