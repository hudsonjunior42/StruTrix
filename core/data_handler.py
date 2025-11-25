import pandas as pd

class DataHandler:
    def __init__(self):
        self.init_data()

    def init_data(self):
        """Inicializa ou reseta os DataFrames e resultados."""
        # Definição das colunas
        self.node_cols = [
            "X", "Y", "Fx", "Fy", "Mz", 
            "Restr_X", "Restr_Y", "Restr_Rz", "Restr_Rot", 
            "Disp_X", "Disp_Y", "Disp_Rz"
        ]
        
        self.bar_cols = [
            "node_i", "node_j", "E", "A", "I", 
            "Q", "rot_i", "rot_j"
        ]
        
        # Criação dos DataFrames vazios
        self.nodes_df = pd.DataFrame(columns=self.node_cols)
        self.bars_df = pd.DataFrame(columns=self.bar_cols)
        
        # Resultados da análise ficam aqui
        self.analysis_results = None 

    def _reset_results(self):
        """Método interno para invalidar resultados quando algo muda."""
        self.analysis_results = None

    # --- MÉTODOS PARA NÓS ---

    def add_node(self, x, y):
        """Adiciona um novo nó se não houver duplicata na posição."""
        # Verifica se já existe um nó nestas coordenadas
        for _, row in self.nodes_df.iterrows():
            if x == row["X"] and y == row["Y"]:
                return False, "Já existe um Nó na posição selecionada."
        
        # Cria dicionário com valores padrão zerados/False
        new_node = {col: 0 for col in self.node_cols} 
        new_node["X"] = x
        new_node["Y"] = y
        # Ajuste explícito de booleanos para garantir tipo correto
        new_node["Restr_X"] = False
        new_node["Restr_Y"] = False
        new_node["Restr_Rz"] = False
        
        self.nodes_df.loc[len(self.nodes_df)] = new_node
        self._reset_results()
        return True, "Nó adicionado com sucesso."

    def update_node_coords(self, index, x, y):
        """Atualiza as coordenadas X, Y de um nó existente."""
        if 0 <= index < len(self.nodes_df):
            # Verifica colisão com outros nós (exceto ele mesmo)
            for i, row in self.nodes_df.iterrows():
                if i != index and x == row["X"] and y == row["Y"]:
                     return False, "Já existe outro Nó nesta posição."

            self.nodes_df.loc[index, "X"] = x
            self.nodes_df.loc[index, "Y"] = y
            self._reset_results()
            return True, "Nó atualizado."
        return False, "Índice inválido."

    def delete_node(self, index):
        """Deleta um nó e reseta o índice."""
        if 0 <= index < len(self.nodes_df):
            self.nodes_df = self.nodes_df.drop(index=index).reset_index(drop=True)
            self._reset_results()
            return True, "Nó deletado."
        return False, "Índice inválido."

    def update_nodal_loads(self, index, fx, fy, mz):
        """Atualiza cargas nodais."""
        if 0 <= index < len(self.nodes_df):
            self.nodes_df.loc[index, ["Fx", "Fy", "Mz"]] = [fx, fy, mz]
            self._reset_results()
            return True
        return False

    def update_supports(self, index, restr_x, restr_y, restr_rz, restr_rot):
        """Atualiza condições de apoio (restrições e rotação)."""
        if 0 <= index < len(self.nodes_df):
            self.nodes_df.loc[index, ["Restr_X", "Restr_Y", "Restr_Rz", "Restr_Rot"]] = [restr_x, restr_y, restr_rz, restr_rot]
            self._reset_results()
            return True
        return False

    def update_prescribed_displacements(self, index, dx, dy, drz):
        """Atualiza deslocamentos prescritos."""
        if 0 <= index < len(self.nodes_df):
            self.nodes_df.loc[index, ["Disp_X", "Disp_Y", "Disp_Rz"]] = [dx, dy, drz]
            self._reset_results()
            return True
        return False

    # --- MÉTODOS PARA BARRAS ---

    def add_bar(self, data_dict):
        """Adiciona uma nova barra a partir de um dicionário de dados."""
        # Validação simples
        if data_dict['node_i'] == data_dict['node_j']:
            return False, "A barra deve conectar nós diferentes."
        
        # Garante que as chaves batam com as colunas
        new_row = {k: data_dict.get(k, 0) for k in self.bar_cols}
        
        self.bars_df.loc[len(self.bars_df)] = new_row
        self._reset_results()
        return True, "Barra adicionada."

    def update_bar(self, index, data_dict):
        """Atualiza propriedades físicas e conectividade da barra."""
        if 0 <= index < len(self.bars_df):
             if data_dict['node_i'] == data_dict['node_j']:
                return False, "A barra deve conectar nós diferentes."
             
             for key, value in data_dict.items():
                 if key in self.bar_cols:
                     self.bars_df.loc[index, key] = value
             
             self._reset_results()
             return True, "Barra atualizada."
        return False, "Índice inválido."

    def delete_bar(self, index):
        """Deleta uma barra."""
        if 0 <= index < len(self.bars_df):
            self.bars_df = self.bars_df.drop(index=index).reset_index(drop=True)
            self._reset_results()
            return True
        return False

    def update_bar_load(self, index, q):
        """Atualiza carga distribuída da barra."""
        if 0 <= index < len(self.bars_df):
            self.bars_df.loc[index, "Q"] = q
            self._reset_results()
            return True
        return False

    # --- MÉTODOS DE ARQUIVO (IO) ---

    def get_dict_data(self):
        """Retorna estrutura pronta para salvar em JSON."""
        return {
            "nodes": self.nodes_df.to_dict(orient='records'),
            "bars": self.bars_df.to_dict(orient='records')
        }

    def load_from_dict(self, data):
        """Carrega DataFrames a partir de dicionário (JSON carregado)."""
        try:
            self.nodes_df = pd.DataFrame.from_records(data['nodes'], columns=self.node_cols)
            self.bars_df = pd.DataFrame.from_records(data['bars'], columns=self.bar_cols)
            self._reset_results()
            return True, "Dados carregados com sucesso."
        except Exception as e:
            return False, str(e)