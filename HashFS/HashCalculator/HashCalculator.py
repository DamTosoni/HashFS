"""
Questa classe astratta si occupa di calcolare l'hash dei file del filesystem
"""
# from HashDataStructure.HashDataStructure import HashDataStructure
class HashCalculator(object):

    _hash_calculator = None

    """
    Calcolo l'hash di un singolo file
    """
    def calculateFileHash(self, file_path, blocksize=65536):
        self.create_hash_calculator()
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
    def calculateDirectoryHash(self, directory_path, root_directory, hash_data_structure):
        from os import listdir
        from os.path import isfile, join

        self.create_hash_calculator()

        self._hash_calculator.update(directory_path.encode(encoding='UTF-8'))

        # Prendo la lista dei figli
        children = listdir(directory_path)

        # Calcolo l'hash dei figli in maniera efficiente, prendendoli
        # dalla struttura se gia' presenti
        for child in children:
            child_path = join(directory_path, child)
            if (root_directory + child_path[1:]) in hash_data_structure:
                self._hash_calculator.update(hash_data_structure[root_directory + child_path[1:]])
            else:
                # Nell'eventualita' che il valore non sia presente lo ricalcolo
                # e lo aggiungo alla struttura
                if isfile(child_path):
                    childrenHash = self.calculateFileHash(child_path)
                else:
                    childrenHash = self.calculateDirectoryHash(child_path, root_directory, hash_data_structure)
                self._hash_calculator.update(childrenHash)
                
                # Aggiungo l'hash mancante alla struttura
                hash_data_structure[root_directory + child_path[1:]] = childrenHash

        return self._hash_calculator.hexdigest()

    def create_hash_calculator(self):
        raise NotImplementedError("Funzione non implementata")
