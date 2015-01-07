"""
Questa classe astratta si occupa di calcolare l'hash dei file
del filesystem
"""
from HashDataStructure.HashDataStructure import HashDataStructure
class HashCalculator(object):

    _hash_calculator = None
    __hashDataStructure = HashDataStructure()

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

    """
    Calcolo l'hash di una directory.
    """
    def calculateDirectoryHash(self, directory_path):
        from os import listdir
        from os.path import isfile, join

        self._hash_calculator.update(directory_path.encode(encoding='UTF-8'))
        # Prendo la lista dei figli
        children = listdir(directory_path)
        # Calcolo l'hash dei figli in maniera efficiente, prendendoli
        # dalla struttura se gia' presenti
        data = self.__hashDataStructure.get_structure_snapshot()
        for child in children:
            child_path = join(directory_path, child)
            if child_path in data:
                self._hash_calculator.update(data[child_path])
            else:
                # Nell'eventualita' che il valore non sia presente lo ricalcolo
                if isfile(child_path):
                    # Calcolo l'hash con l'hash dei file contenuti nella cartella
                    self._hash_calculator.update(self.calculateFileHash(child_path))
                else:
                    self._hash_calculator.update(self.calculateDirectoryHash(child_path))

        return self._hash_calculator.hexdigest()
