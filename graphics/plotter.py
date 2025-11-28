import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.patches as patches
from matplotlib.transforms import Affine2D
import numpy as np
import math

# A classe do Canvas fica aqui
class MatplotlibCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MatplotlibCanvas, self).__init__(fig)
        self.setParent(parent)
        
        # Toolbar escondida
        self.toolbar = NavigationToolbar(self, self)                                         # Cria Toolbar (Deletar e adicionar a menu bar (View))
        self.toolbar.hide()
        
        # Pan inicialmente habilitado
        self.toolbar.pan()

class StructuralPlotter:
    def __init__(self, canvas):
        self.canvas = canvas
        self.ax = canvas.axes

    def clear(self):
        self.ax.cla()

    def draw_structure(self, nodes_df, bars_df, analysis_results, view_mode, show_grid, count_nodes, count_bars, show_reactions):
        self.clear()
        
        # Chama as sub-funções
        self._plot_structure_base(nodes_df, bars_df, count_nodes, count_bars)

        if view_mode == 'Visualização':
            self._plot_loads_and_supports(nodes_df, bars_df)
        elif view_mode == 'Deformação':
            self._plot_deformed_shape(analysis_results)
        elif 'Diagrama' in view_mode:
            self._plot_reactions(nodes_df, analysis_results, show_reactions)
            self._plot_diagram(analysis_results, view_mode)

        # Configurações finais
        self.ax.set_xlabel('X (m)')
        self.ax.set_ylabel('Y (m)')
        self.ax.set_title(f'{view_mode}')
        self.ax.axis('equal')
        if show_grid: self.ax.grid(True, linestyle='--', alpha=0.6)
        self.canvas.draw()

# Plota base da estrutura (Nós e barras)
    def _plot_structure_base(self, nodes_df, bars_df, count_nodes, count_bars):        
        # Cancela se não houverem nós
        if nodes_df.empty: return
        
        # Carrega os valores das cooredadas x e y de cada nó
        coord = nodes_df[["X", "Y"]].values.astype(float)
        
        # Plota as barras ligando as posições x e y dos nós iniciais e finais e numera as barras
        if not bars_df.empty:
            M = bars_df[["node_i", "node_j"]].values.astype(int)
            for i in range(len(bars_df)):
                node_i, node_j = M[i, 0], M[i, 1]
                self.canvas.axes.plot([coord[node_i, 0], coord[node_j, 0]], [coord[node_i, 1], coord[node_j, 1]], 'k-', lw=1.5, zorder=1)       
                if count_bars:
                    self.canvas.axes.text((coord[node_j, 0] + coord[node_i, 0])/2, (coord[node_j, 1] + coord[node_i, 1])/2 , f' {i+1}', verticalalignment='top', color='blue', zorder=3) # Numeração das barras
                
        # Plota Nós nas posições x e y com numeração
        self.canvas.axes.plot(coord[:, 0], coord[:, 1], 'ko', markersize=5, zorder=2)
        for i, (x, y) in enumerate(coord):
            if count_nodes:
                self.canvas.axes.text(x, y, f' {i+1}', verticalalignment='bottom', color='purple', zorder=3) # Numeração dos nós

    def _plot_loads_and_supports(self, nodes_df, bars_df):        
        # Cancela se não houverem nós
        if nodes_df.empty: return
        
        # Carrega informações dos nós
        coord = nodes_df[["X", "Y"]].values.astype(float)
        
        x_coords = coord[:, 0]
        y_coords = coord[:, 1]
        x_min, x_max = (x_coords.min(), x_coords.max()) if len(x_coords) > 0 else (0, 1)
        y_min, y_max = (y_coords.min(), y_coords.max()) if len(y_coords) > 0 else (0, 1)
        diag = math.sqrt((x_max - x_min)**2 + (y_max - y_min)**2)
        scale = diag / 5 if diag > 0 else 0.6

        # Desenha apoios
        for i in range(len(coord)):
            restrs = nodes_df.iloc[i]
            if restrs['Restr_X'] == 1 or restrs['Restr_Y'] == 1 or restrs['Restr_Rz'] == 1:
                no = coord[i]
                angle_deg = restrs.get('Restr_Rot', 0)
                
                # Engaste (3º gênero)
                if restrs['Restr_X'] == 1 and restrs['Restr_Y'] == 1 and restrs['Restr_Rz'] == 1:
                     # Triangulo
                     l1 = plt.Line2D([no[0] - 0.15*scale, no[0] + 0.15*scale], [no[1], no[1]], color='black', lw=1, transform=Affine2D().rotate_deg_around(no[0], no[1], angle_deg) + self.canvas.axes.transData)
                     self.ax.add_line(l1)
                     
                     # Hachura abaixo do triangulo
                     base = plt.Rectangle((no[0]-0.15*scale, no[1]-0.1*scale), width=0.3*scale, height=0.1*scale, fill=False, hatch='////', edgecolor='black', lw=0)
                     base.set_transform(Affine2D().rotate_deg_around(no[0], no[1], angle_deg) + self.canvas.axes.transData)
                     self.canvas.axes.add_patch(base)
                
                # Apoio 2º gênero (com hachura e rotação)
                elif restrs['Restr_X'] == 1 and restrs['Restr_Y'] == 1 and restrs['Restr_Rz'] == 0:
                    # Triangulo
                    verts = [(no[0]-0.15*scale, no[1]-0.2*scale), (no[0]+0.15*scale, no[1]-0.2*scale), (no[0], no[1])]
                    apoio_poly = plt.Polygon(verts, closed=True, fill=False, color='black')
                    apoio_poly.set_transform(Affine2D().rotate_deg_around(no[0], no[1], angle_deg) + self.canvas.axes.transData)
                    self.canvas.axes.add_patch(apoio_poly)
                    
                    # Hachura com centro de rotação no ponto do nó (no[0], no[1])
                    base_hatch = plt.Rectangle((no[0]-0.15*scale, no[1]-0.2*scale-0.1*scale), width=0.3*scale, height=0.1*scale, fill=False, hatch='////', edgecolor='black', lw=0)
                    base_hatch.set_transform(Affine2D().rotate_deg_around(no[0], no[1], angle_deg) + self.canvas.axes.transData)
                    self.canvas.axes.add_patch(base_hatch)
                
                # Apoio 1º gênero (rolete)
                elif restrs['Restr_X'] == 1 or restrs['Restr_Y'] == 1:
                    # Rotaciona caso haja apenas restrição em X
                    if restrs['Restr_X'] == 1 and restrs['Restr_Y'] == 0:
                        angle_deg = (270)
                    
                    # Triangulo
                    verts = [(no[0]-0.15*scale, no[1]-0.2*scale), (no[0]+0.15*scale, no[1]-0.2*scale), (no[0], no[1])]
                    apoio_poly = plt.Polygon(verts, closed=True, fill=False, color='black')
                    apoio_poly.set_transform(Affine2D().rotate_deg_around(no[0], no[1], angle_deg) + self.canvas.axes.transData)
                    self.canvas.axes.add_patch(apoio_poly)
                    
                    # Linha abaixo do triangulo
                    l2 = plt.Line2D([no[0]-0.15*scale, no[0]+0.15*scale], [no[1]-0.25*scale, no[1]-0.25*scale], color='black', lw=1, transform=Affine2D().rotate_deg_around(no[0], no[1], angle_deg) + self.canvas.axes.transData)
                    self.canvas.axes.add_line(l2)

        # Desenha cargas nodais
        nodal_loads = nodes_df[["Fx", "Fy", "Mz"]].values.astype(float)
        for i in range(len(coord)):
            if nodal_loads[i, 0] != 0:
                self.canvas.axes.arrow(coord[i, 0] - np.sign(nodal_loads[i, 0])*scale, 
                                       coord[i, 1], 
                                       np.sign(nodal_loads[i, 0])*scale*0.8, 0, 
                                       head_width=scale*0.1, 
                                       color='blue', 
                                       lw=1.5, 
                                       zorder=5)
                
                self.canvas.axes.text(coord[i,0] - np.sign(nodal_loads[i, 0])*scale*1.1, 
                                      coord[i,1], 
                                      f"{nodal_loads[i,0]:.1f} kN", 
                                      color='blue')
                
            if nodal_loads[i, 1] != 0:
                self.canvas.axes.arrow(coord[i, 0], 
                                       coord[i, 1] - np.sign(nodal_loads[i, 1])*scale, 
                                       0, 
                                       np.sign(nodal_loads[i, 1])*scale*0.8, 
                                       head_width=scale*0.1, 
                                       color='blue', 
                                       lw=1.5, 
                                       zorder=5)
                
                self.canvas.axes.text(coord[i,0], 
                                      coord[i,1] - np.sign(nodal_loads[i, 1])*scale*1.1, 
                                      f"{nodal_loads[i,1]:.1f} kN", 
                                      color='blue')
                
            if nodal_loads[i, 2] != 0:

                if nodal_loads[i, 2] < 0: 
                    self.canvas.axes.add_patch(patches.FancyArrowPatch((coord[i, 0]-0.3*scale, coord[i, 1]),
                                                                   (coord[i, 0]+0.3*scale, coord[i, 1]), 
                                                                   connectionstyle="arc3,rad=-1", 
                                                                   **dict(arrowstyle="Simple, tail_width=0.5, head_width=4, head_length=8", color="green")))
                else:
                    self.canvas.axes.add_patch(patches.FancyArrowPatch((coord[i, 0]+0.3*scale, coord[i, 1]),
                                                                   (coord[i, 0]-0.3*scale, coord[i, 1]), 
                                                                   connectionstyle="arc3,rad=1", 
                                                                   **dict(arrowstyle="Simple, tail_width=0.5, head_width=4, head_length=8", color="green")))
                    
                self.canvas.axes.text(coord[i,0], coord[i,1] + scale*0.3, f" {nodal_loads[i,2]:.1f} kN.m", color='green')

        # Desenha cargas distribuídas
        if not bars_df.empty:
            for i, bar in bars_df.iterrows():
                p_val = bar.get('Q', 0)
                if abs(p_val) > 1e-6:
                    ni_idx, nj_idx = int(bar['node_i']), int(bar['node_j'])
                    xi, yi = coord[ni_idx]
                    xj, yj = coord[nj_idx]
                    
                    angle = np.arctan2(yj - yi, xj - xi)
                    
                    # Forças negativas para cima, positivas para baixo. Vetor perp. invertido para setas apontarem para a viga.
                    direction = np.sign(p_val)
                    perp_vec = np.array([-np.sin(angle), np.cos(angle)]) * - direction
                    
                    bar_length = math.sqrt((xj - xi)**2 + (yj - yi)**2)
                    num_arrows_internal = max(1, int(bar_length / 0.5))
                    
                    # Pontos para as setas: 0 (início), 1 (fim) e num_arrows_internal pontos internos
                    points_of_application = np.linspace(0, 1, num_arrows_internal + 2)
                    
                    arrow_len = scale * 0.5
                    
                    # Linha de carga (Linha sólida que as setas devem tocar)
                    # O deslocamento é exatamente o comprimento da seta (arrow_len) para que as bases (caudas) se alinhem.
                    start_line = np.array([xi, yi]) + perp_vec * arrow_len
                    end_line = np.array([xj, yj]) + perp_vec * arrow_len
                    
                    self.canvas.axes.plot([start_line[0], end_line[0]], [start_line[1], end_line[1]], color='red', lw=1)
                    
                    for t in points_of_application:
                        # Ponto na barra (ponta da seta)
                        start_pos = np.array([xi + t * (xj - xi), yi + t * (yj - yi)])
                        # Ponto da linha de carga (base/cauda da seta)
                        end_pos = start_pos + perp_vec * arrow_len
                        
                        # Setas desenhadas da base (end_pos) para a ponta (start_pos)
                        self.canvas.axes.arrow(end_pos[0], end_pos[1], (start_pos-end_pos)[0], (start_pos-end_pos)[1], 
                                               head_width=scale * 0.08, color='red', lw=1, length_includes_head=True)
                    
                    mid_point = np.array([xi + 0.5 * (xj - xi), yi + 0.5 * (yj - yi)])
                    text_pos = mid_point + perp_vec * arrow_len * 1.5 # Manter o texto afastado
                    self.canvas.axes.text(text_pos[0], text_pos[1], f'{p_val:.1f} kN/m', color='red', ha='center', va='center')

    # Desenha reações de apoio
    def _plot_reactions(self, nodes_df, analysis_results, show_reactions):
        if show_reactions and analysis_results:
            nodal_reactions = analysis_results['reactions']

            # Carrega informações dos nós
            coord = nodes_df[["X", "Y"]].values.astype(float)
            
            x_coords = coord[:, 0]
            y_coords = coord[:, 1]
            x_min, x_max = (x_coords.min(), x_coords.max()) if len(x_coords) > 0 else (0, 1)
            y_min, y_max = (y_coords.min(), y_coords.max()) if len(y_coords) > 0 else (0, 1)
            diag = math.sqrt((x_max - x_min)**2 + (y_max - y_min)**2)
            scale = diag / 5 if diag > 0 else 0.6


            for i in range(len(coord)):
                if nodal_reactions[i, 0] != 0:
                    self.canvas.axes.arrow(coord[i, 0] - np.sign(nodal_reactions[i, 0])*scale, coord[i, 1], np.sign(nodal_reactions[i, 0])*scale*0.8, 0, head_width=scale*0.1, color='brown', lw=1.5, zorder=5)
                    self.canvas.axes.text(coord[i,0] - np.sign(nodal_reactions[i, 0])*scale*1.1, coord[i,1], f"{nodal_reactions[i,0]:.1f} kN", color='brown')
                if nodal_reactions[i, 1] != 0:
                    self.canvas.axes.arrow(coord[i, 0], coord[i, 1] - np.sign(nodal_reactions[i, 1])*scale, 0, np.sign(nodal_reactions[i, 1])*scale*0.8, head_width=scale*0.1, color='brown', lw=1.5, zorder=5)
                    self.canvas.axes.text(coord[i,0], coord[i,1] - np.sign(nodal_reactions[i, 1])*scale*1.1, f"{nodal_reactions[i,1]:.1f} kN", color='brown')
                if nodal_reactions[i, 2] != 0:
                    if nodal_reactions[i, 2] < 0: 
                        self.canvas.axes.add_patch(patches.FancyArrowPatch((coord[i, 0]-0.3*scale, coord[i, 1]),
                                                                    (coord[i, 0]+0.3*scale, coord[i, 1]), 
                                                                    connectionstyle="arc3,rad=-1", 
                                                                    **dict(arrowstyle="Simple, tail_width=0.5, head_width=4, head_length=8", color="brown")))
                    else:
                        self.canvas.axes.add_patch(patches.FancyArrowPatch((coord[i, 0]+0.3*scale, coord[i, 1]),
                                                                    (coord[i, 0]-0.3*scale, coord[i, 1]), 
                                                                    connectionstyle="arc3,rad=1", 
                                                                    **dict(arrowstyle="Simple, tail_width=0.5, head_width=4, head_length=8", color="brown")))
                    self.canvas.axes.text(coord[i,0], coord[i,1] + scale*0.3, f" {nodal_reactions[i,2]:.1f} kN.m", color='brown')
    
    def _plot_diagram(self, analysis_results, current_view):        
        if analysis_results is None: return
        
        forces, coord = analysis_results['forces'], analysis_results['coord']
        M, L, p = analysis_results['connectivity'], analysis_results['lengths'], analysis_results['distributed_loads']
        
        # Ajuste de escala para visualização
        max_force_val = np.max(np.abs(forces)) if forces.size > 0 else 1.0
        if max_force_val < 1e-9: max_force_val = 1.0
        max_L = np.max(L) if len(L) > 0 else 1.0
        scale = max_L / max_force_val * 0.2

        diagram_map = {
            "Diagrama de Esforços Normais": (0, 'blue', 'N'), 
            "Diagrama de Esforços Cisalhantes": (1, 'red', 'V'), 
            "Diagrama de Momento Fletor": (2, 'green', 'M')
        }
        
        if current_view not in diagram_map: return
        idx, color, label = diagram_map[current_view]

        for i in range(len(M)):
            n1, n2 = M[i, 0], M[i, 1]
            x1, y1 = coord[n1]; x2, y2 = coord[n2]
            
            # Vetor diretor da barra e vetor perpendicular
            dx, dy = x2 - x1, y2 - y1
            angle = np.arctan2(dy, dx)
            perp_vec = np.array([-np.sin(angle), np.cos(angle)])
            
            # Discretização da barra para curvas suaves
            num_points = 50
            x_vals_global = np.linspace(0, 1, num_points)
            base_points = np.array([
                [x1 + t * dx, y1 + t * dy] for t in x_vals_global
            ])
            x_local = x_vals_global * L[i]
            
            # Nota: forces[i] = [Ni, Vi, Mi, Nj, Vj, Mj]
            
            if label == 'N': 
                # Normal constante (considerando apenas cargas nodais axiais por enquanto)
                diag_vals = np.full_like(x_local, forces[i, 0])
                plot_scale = scale # Plota normal positivo para "cima/fora"

            elif label == 'V': 
                # Cortante: V(x) = Vi + integral(q)
                # Como p é definido positivo para cima na análise: V(x) = Vi + p*x
                diag_vals = forces[i, 1] + p[i] * x_local
                plot_scale = scale

            else: 
                # Momento: M(x) = M_i + V_i*x + p*x^2/2 (onde M_i no resultado é forces[i, 2])
                diag_vals = -forces[i, 2] + forces[i, 1] * x_local + p[i] * x_local**2 / 2

                # Inversão do diagrama
                plot_scale = -scale
            
            # Calcula os pontos do diagrama deslocados da barra
            diag_points = base_points + (perp_vec * diag_vals[:, np.newaxis] * plot_scale)
            
            # 1. Desenha e preenche o diagrama
            # Cria um polígono fechado: Pontos da base (ida) -> Pontos do diagrama (volta)
            plot_poly = np.vstack([base_points, diag_points[::-1]])
            self.canvas.axes.fill(plot_poly[:, 0], plot_poly[:, 1], color=color, alpha=0.3, zorder=0)
            self.canvas.axes.plot(diag_points[:, 0], diag_points[:, 1], color=color, lw=1.5, zorder=1)
            
            # 2. Plota os valores nas extremidades
            self.canvas.axes.text(diag_points[0, 0], diag_points[0, 1], f'{diag_vals[0]:.2f}', color=color, fontsize=8)
            self.canvas.axes.text(diag_points[-1, 0], diag_points[-1, 1], f'{diag_vals[-1]:.2f}', color=color, fontsize=8)

            # 3. Plota o valor do VÉRTICE (Máximo/Mínimo) para Momento Fletor com carga distribuída
            if label == 'M' and abs(p[i]) > 1e-5:
                # O cortante é zero quando: V(x) = Vi + p*x = 0  =>  x = -Vi / p
                # Possui uma tolerancia por conta da discretização do elemento
                x_vertex = -forces[i, 1] / p[i]
                
                if 0 <= x_vertex <= L[i]:
                    # Valor do momento no vértice
                    M_vertex = forces[i, 2] + forces[i, 1] * x_vertex + p[i] * (x_vertex**2) / 2
                    
                    # Coordenada global do vértice na barra
                    t_vertex = x_vertex / L[i]
                    x_base_v = x1 + t_vertex * dx
                    y_base_v = y1 + t_vertex * dy
                    
                    # Coordenada do ponto no diagrama
                    pt_diag_v = np.array([x_base_v, y_base_v]) + perp_vec * M_vertex * plot_scale
                    
                    self.canvas.axes.text(pt_diag_v[0], pt_diag_v[1], 
                                           f'{M_vertex:.2f}', color=color, fontsize=8, fontweight='bold',
                                           ha='center', va='center', 
                                           bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=0.5), 
                                           zorder=2)

    def _plot_deformed_shape(self, analysis_results):
        if analysis_results is None: return

        # Recupera dados
        orig_coord = analysis_results['coord']
        def_coord = analysis_results['deformed_coords']
        connectivity = analysis_results['connectivity']
        
        # Plota estrutura original (cinza tracejado)
        for i in range(len(connectivity)):
            n1, n2 = connectivity[i]
            self.ax.plot([orig_coord[n1, 0], orig_coord[n2, 0]], 
                         [orig_coord[n1, 1], orig_coord[n2, 1]], 
                         'k--', lw=1, alpha=0.3)

        # Plota estrutura deformada (azul contínuo)
        for i in range(len(connectivity)):
            n1, n2 = connectivity[i]
            self.ax.plot([def_coord[n1, 0], def_coord[n2, 0]], 
                         [def_coord[n1, 1], def_coord[n2, 1]], 
                         'b-', lw=2)
            
        # Plota nós deformados
        self.ax.plot(def_coord[:, 0], def_coord[:, 1], 'bo', markersize=4)
