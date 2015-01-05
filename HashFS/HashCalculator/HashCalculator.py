"""
Questa classe astratta si occupa di calcolare l'hash dei file
del filesystem
"""
class HashCalculator(object):

    _hash_calculator = None

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
    Calcolo l'hash di una directory
    """
    def calculateDirectoryHash(self, directory_path):
        from os import listdir
        from os.path import isfile, join

        self._hash_calculator.update(directory_path.encode(encoding='UTF-8'))
        # Prendo la lista dei figli
        children = listdir(directory_path)
        # Calcolo l'hash dei figli
        for child in children:
            if isfile(join(directory_path, child)):
                # Calcolo l'hash con l'hash dei file contenuti nella cartella
                self._hash_calculator.update(self.calculateFileHash(join(directory_path, child)))
            else:
                self._hash_calculator.update(self.calculateDirectoryHash(join(directory_path, child)))

        return self._hash_calculator.hexdigest()
