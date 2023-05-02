import os
import pickle


class PrintColor:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class PersistentUtility:
    @staticmethod
    def load_data_from_file(filename, on_empty=None) -> dict:
        filename = f'Data/{filename}'
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                data = pickle.load(f)
                return data
        else:
            return on_empty

    @staticmethod
    def save_data_to_file(filename, data):
        PersistentUtility.__make_data_folder_if_not_exists()
        filename = f'Data/{filename}'
        with open(filename, 'wb') as f:
            pickle.dump(data, f)

    @staticmethod
    def __make_data_folder_if_not_exists():
        if not os.path.exists('Data'):
            os.makedirs('Data')


class StringUtility:
    @staticmethod
    def WordCount(text: str) -> int:
        return sum(1 for c in text if c in ' \t\n')
