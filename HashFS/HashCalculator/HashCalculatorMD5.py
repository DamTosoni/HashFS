"""
Questa classe si occupa di calcolare l'hash dei file
del filesystem usando l'algoritmo MD5
"""
from HashCalculator import HashCalculator
class HashCalculatorMD5(HashCalculator):

    def __init__(self, fs_file_path=""):
        import hashlib
        self. _hash_calculator = hashlib.md5()

    """
    Calcolo l'hash di un singolo file
    """
    def calculateFileHash(self, file_path, blocksize=65536):
        open_file = open(file_path, 'rb')
        buf = open_file.read(blocksize)
        while len(buf) > 0:
            self._hash_calculator.update(buf)
            buf = open_file.read(blocksize)

        # Aggiungo il nome del file all'hash
        self._hash_calculator.update(file_path.encode(encoding='UTF-8'))

        return self._hash_calculator.hexdigest()
