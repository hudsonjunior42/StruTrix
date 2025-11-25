import json

class FileManager:
    @staticmethod
    def save_file(filepath, data_dict):
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, ensure_ascii=False, indent=4)
            return True, "Arquivo salvo com sucesso!"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def load_file(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return True, data
        except Exception as e:
            return False, str(e)