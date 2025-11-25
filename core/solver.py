import numpy as np
import math

class StructuralSolver:
    def __init__(self):
        pass

    def run_analysis(self, nodes_df, bars_df):
            # --- 1. Carregamento de Dados ---

            # Carrega os dados dos nós
            coord = nodes_df[["X", "Y"]].values.astype(float)
            nodal_forces = nodes_df[["Fx", "Fy", "Mz"]].values.astype(float)
            nodal_restraints = nodes_df[["Restr_X", "Restr_Y", "Restr_Rz"]].values.astype(float)
            prescribed_displacements = nodes_df[["Disp_X", "Disp_Y", "Disp_Rz"]].values.astype(float)
            num_nodes = len(nodes_df)

            # Carrega os dados das barras
            connectivity = bars_df[["node_i", "node_j"]].values.astype(int)  # Matriz de conectividade (0-based)
            A = bars_df["A"].values.astype(float) # Área
            I = bars_df["I"].values.astype(float) # Momento de Inércia
            E = bars_df["E"].values.astype(float) # Módulo de Elasticidade
            distributed_loads = bars_df["Q"].values.astype(float) # Carga distribuída
            releases = bars_df[["rot_i", "rot_j"]].values.astype(int)  # Rótulas (liberação de rotação)
            num_bars = len(bars_df)

            # Parâmetros fixos
            dof_per_node = 3
            big_number = 1e15  # Número grande para restrição (método do número grande)

            # --- 2. Cálculo das Matrizes de Barra (Loop Principal) ---

            # Criação de vetores / matrizes zeradas
            lengths = np.zeros(num_bars)
            fixed_end_forces_local = np.zeros(shape=(num_bars, 2 * dof_per_node))
            fixed_end_forces_local_mod = np.zeros(shape=(num_bars, 2 * dof_per_node))
            rotation_matrices = np.zeros(shape=(num_bars, 2 * dof_per_node, 2 * dof_per_node))
            stiffness_local_matrices = np.zeros(shape=(num_bars, 2 * dof_per_node, 2 * dof_per_node))
            stiffness_local_mod_matrices = np.zeros(shape=(num_bars, 2 * dof_per_node, 2 * dof_per_node))
            dof_mapping = []  # Vetor de correspondência (mapeia DOFs locais para globais)

            # Calculando para todas as barras:
            for i in range(num_bars):
                # Cálculo do comprimento e cossenos diretores
                node_i = connectivity[i, 0]
                node_j = connectivity[i, 1]
                dx = coord[node_j, 0] - coord[node_i, 0]
                dy = coord[node_j, 1] - coord[node_i, 1]
                lengths[i] = math.sqrt(dx ** 2 + dy ** 2)
                if lengths[i] < 1e-9:
                    raise ValueError(f"Barra {i+1} tem comprimento zero.")

                # Constantes da barra
                L_val = lengths[i]
                p_val = distributed_loads[i]
                EAL = E[i] * A[i] / L_val
                EIL = E[i] * I[i] / L_val
                EIL2 = EIL / L_val
                EIL3 = EIL2 / L_val

                # Forças de engastamento perfeito (CORRIGIDO)
                # Convenção: p > 0 (para cima)
                # Índices: [Ax_i, V_i, M_i, Ax_j, V_j, M_j] -> [0, 1, 2, 3, 4, 5]
                fixed_end_forces_local[i, 1] = -p_val * L_val / 2      # V_i
                fixed_end_forces_local[i, 4] = -p_val * L_val / 2      # V_j
                fixed_end_forces_local[i, 2] = -p_val * L_val**2 / 12  # M_i
                fixed_end_forces_local[i, 5] = p_val * L_val**2 / 12 # M_j

                # Matriz de rigidez local (pórtico)
                stiffness_local_matrices[i] = np.array([
                    [EAL, 0, 0, -EAL, 0, 0],
                    [0, 12*EIL3, 6*EIL2, 0, -12*EIL3, 6*EIL2],
                    [0, 6*EIL2, 4*EIL, 0, -6*EIL2, 2*EIL],
                    [-EAL, 0, 0, EAL, 0, 0],
                    [0, -12*EIL3, -6*EIL2, 0, 12*EIL3, -6*EIL2],
                    [0, 6*EIL2, 2*EIL, 0, -6*EIL2, 4*EIL]])

                # Aplicação de rótulas (modifica matriz de rigidez e vetor de Forças de Engastamento Perfeito)
                stiffness_local_mod_matrices[i] = stiffness_local_matrices[i].copy()
                fixed_end_forces_local_mod[i] = fixed_end_forces_local[i].copy()

                # Rótula no nó inicial (Condensação Estática)
                if releases[i, 0] == 1 and releases[i, 1] == 0:
                    gl = 2  # DOF do momento em i
                    pivot = stiffness_local_mod_matrices[i, gl, gl]
                    if abs(pivot) < 1e-12: pivot = 1e-12
                    K_col_orig = stiffness_local_mod_matrices[i, :, gl].copy()
                    stiffness_local_mod_matrices[i] -= np.outer(stiffness_local_mod_matrices[i, :, gl], stiffness_local_mod_matrices[i, gl, :]) / pivot
                    fixed_end_forces_local_mod[i] -= K_col_orig / pivot * fixed_end_forces_local_mod[i, gl]

                # Rótula no nó final (Condensação Estática)
                if releases[i, 1] == 1 and releases[i, 0] == 0:
                    gl = 5  # DOF do momento em j
                    pivot = stiffness_local_mod_matrices[i, gl, gl]
                    if abs(pivot) < 1e-12: pivot = 1e-12
                    K_col_orig = stiffness_local_mod_matrices[i, :, gl].copy()
                    stiffness_local_mod_matrices[i] -= np.outer(stiffness_local_mod_matrices[i, :, gl], stiffness_local_mod_matrices[i, gl, :]) / pivot
                    fixed_end_forces_local_mod[i] -= K_col_orig / pivot * fixed_end_forces_local_mod[i, gl]

                # Rótula em ambos os nós (biarrotulada) (Matriz de Treliça)
                if releases[i, 0] == 1 and releases[i, 1] == 1:
                    stiffness_local_mod_matrices[i] = np.zeros((2 * dof_per_node, 2 * dof_per_node))
                    stiffness_local_mod_matrices[i, 0, 0] = EAL
                    stiffness_local_mod_matrices[i, 3, 3] = EAL
                    stiffness_local_mod_matrices[i, 0, 3] = -EAL
                    stiffness_local_mod_matrices[i, 3, 0] = -EAL
                    fixed_end_forces_local_mod[i, :] = 0  # Forças de Engastamento Perfeito é zero para treliça

                # Matriz de rotação (Transformação de coordenadas)
                c, s = dx / L_val, dy / L_val
                rotation_matrices[i] = np.array([
                    [c, s, 0, 0, 0, 0],
                    [-s, c, 0, 0, 0, 0],
                    [0, 0, 1, 0, 0, 0],
                    [0, 0, 0, c, s, 0],
                    [0, 0, 0, -s, c, 0],
                    [0, 0, 0, 0, 0, 1]])

                # Vetor de correspondência (DOF mapping)
                qi = np.zeros(2 * dof_per_node, dtype=int)
                z = 0
                for j in range(2):  # Para nó i (j=0) e nó j (j=1)
                    for jk in range(dof_per_node):  # Para DOFs X, Y, Rz
                        qi[z] = dof_per_node * connectivity[i, j] + jk
                        z += 1
                dof_mapping.append(qi)

            # --- 3. Montagem do Sistema Global ---

            total_dofs = dof_per_node * num_nodes
            global_stiffness_matrix = np.zeros(shape=(total_dofs, total_dofs))
            equivalent_nodal_forces = np.zeros(total_dofs)

            # Loop de montagem
            for i in range(num_bars):
                # Rotaciona matriz de rigidez e vetor de forças
                ki_global = rotation_matrices[i].T @ stiffness_local_mod_matrices[i] @ rotation_matrices[i]
                forces_global = rotation_matrices[i].T @ fixed_end_forces_local_mod[i]
                
                qi = dof_mapping[i]  # Pega o mapeamento de DOFs
                
                # Soma as forças nodais equivalentes (sinal trocado)
                equivalent_nodal_forces[qi] -= forces_global
                
                # Monta a matriz de rigidez global (método de superposição)
                for r_idx, r_global in enumerate(qi):
                    for c_idx, c_global in enumerate(qi):
                        global_stiffness_matrix[r_global, c_global] += ki_global[r_idx, c_idx]

            # Vetor de forças nodais combinadas (Forças de Engastamento Perfeito + Forças aplicadas)
            total_nodal_forces = equivalent_nodal_forces.copy()
            for i in range(num_nodes):
                for j in range(dof_per_node):
                    total_nodal_forces[i * dof_per_node + j] += nodal_forces[i, j]

            # --- 4. Aplicação das Condições de Contorno (Método da Penalidade) ---

            # Aplica número grande na Matriz de Rigidez (K)
            global_stiffness_matrix_pen = global_stiffness_matrix.copy()
            for i in range(num_nodes):
                for j in range(dof_per_node):
                    if nodal_restraints[i, j] == 1:
                        global_dof_index = dof_per_node * i + j
                        global_stiffness_matrix_pen[global_dof_index, global_dof_index] += big_number

            # Aplica número grande no Vetor de Forças (F) para deslocamentos prescritos
            total_nodal_forces_pen = total_nodal_forces.copy()
            for i in range(num_nodes):
                for j in range(dof_per_node):
                    if nodal_restraints[i, j] == 1:
                        global_dof_index = dof_per_node * i + j
                        total_nodal_forces_pen[global_dof_index] += big_number * prescribed_displacements[i, j]

            # --- 5. Solução do Sistema e Pós-Processamento ---

            # Deslocamentos nodais
            global_displacements = np.linalg.solve(global_stiffness_matrix_pen, total_nodal_forces_pen)

            # Coordenadas deformadas (escala automática)
            displacements_xy = global_displacements.reshape(-1, dof_per_node)[:, :2]  # Pega apenas DOFs X e Y

            # Cálculo de escala automática
            max_desl = np.max(np.abs(displacements_xy)) if displacements_xy.size > 0 else 0
            max_dim = np.max(np.ptp(coord, axis=0)) if coord.shape[0] > 1 else 1.0
            # Define a escala como 10% da dimensão máxima da estrutura
            scale_factor = 0.1 * max_dim / max_desl if max_desl > 1e-9 else 1.0

            # deformed_coords = coord + displacements_xy * scale_factor

            # Reações de Apoio
            # R = K*d - F_total
            reactions_vector = global_stiffness_matrix @ global_displacements
            reactions_matrix = np.zeros(shape=(num_nodes, dof_per_node))
            for i in range(num_nodes):
                for j in range(dof_per_node):
                    if nodal_restraints[i, j] == 1:
                        global_dof_index = dof_per_node * i + j
                        # Reação = Força Interna (K*d) - Força Externa Total (F_equiv + F_nodal)
                        reactions_matrix[i, j] = reactions_vector[global_dof_index] - total_nodal_forces[global_dof_index]

            # Esforços de extremidade das barras (Forças Locais)
            # F_local = k_local_mod * (R * d_global) + Forças de Engastamento Perfeito_local_mod
            member_end_forces_local = np.zeros(shape=(num_bars, 2 * dof_per_node))
            for i in range(num_bars):
                qi = dof_mapping[i]
                displacements_global_bar = global_displacements[qi]
                displacements_local_bar = rotation_matrices[i] @ displacements_global_bar
                member_end_forces_local[i, :] = stiffness_local_mod_matrices[i] @ displacements_local_bar + fixed_end_forces_local_mod[i]

        
            # No final, retorne o dicionário de resultados
            results = {
                'forces': member_end_forces_local,
                'deformed_coords': coord + displacements_xy * scale_factor, # Já some aqui para facilitar
                'coord': coord,
                'connectivity': connectivity,
                'lengths': lengths,
                'distributed_loads': distributed_loads,
                'scale_factor': scale_factor
            }
            return results
        