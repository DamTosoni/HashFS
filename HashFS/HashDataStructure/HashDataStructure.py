from threading import Lock
# from HashFs import hash_calculator
class HashDataStructure(object):

    __INSTANCE = None
    __dataMap = None
    __fs_root = None
    __upToDate = True

    __structureLock = None  # Semaforo per accedere alla struttura

    __DATAPATH = '.hashFSDataFile'  # Path del file degli hash

    def __init__(self, fs_root=""):
        self.__fs_root = fs_root  # Root del filsesystem
        if self.__INSTANCE is not None:
            raise ValueError("La classe HashDataStructure e' gia' stata inizializzata")

    """
    Restituisco l'istanza della mappa contentente gli hash
    Attenzione: con questo metodo si acquisisce l'istanza in modo
    esclusivo bloccando un semaforo. Si lascia al metodo chiamante
    l'onere di sbloccarlo chiamando l'apposito metodo release_data_structure
    """
    @classmethod
    def get_data_structure_instance(cls):
        if cls.__INSTANCE is None:
            from os.path import expanduser
            home = expanduser("~")
            root_directory = home + "/HashFS"

            cls.__INSTANCE = HashDataStructure(root_directory)
            cls.__structureLock = Lock()
            cls.__structureLock.acquire()
            # Inizializzo la struttura dati
            HashDataStructure.__inizialize_data_map(HashDataStructure.__INSTANCE)
        else:
            cls.__structureLock.acquire()
        return cls.__dataMap

    """
    Rilascio l'istanza della struttura precedentemente bloccata
    """
    def release_data_structure(self):
        HashDataStructure.__structureLock.release()

    """
    Restituisco una copia dell'istanza della struttura
    (comoda se voglio solo leggere e voglio evitare lock molto lunghe)
    """
    def get_structure_snapshot(self):
        data = self.get_data_structure_instance()
        from copy import deepcopy
        result = deepcopy(data)
        self.release_data_structure()
        return result

    """
    Questo metodo inizializza la mappa contenente gli
    hash dei file caricandoli da .hashFSDataFile
    """
    def __inizialize_data_map(self):
        'Controllo se esiste il file degli hash'
        import os.path
        if os.path.isfile(self.__fs_root + self.__DATAPATH):
            self.__load_data_map_from_file()
        else:
            out_file = open(self.__fs_root + self.__DATAPATH, "w")
            out_file.close()
            self.__upToDate = True
            HashDataStructure.__dataMap = dict()

    """
    Questo metodo carica dal file .hashFSDataFile la mappa degli hash
    """
    def __load_data_map_from_file(self):
        HashDataStructure.__dataMap = dict()
        in_file = open(self.__fs_root + self.__DATAPATH, "r")

        ' Nella prima riga memorizzo un booleano che indica se '
        ' il filesystem e\' corrotto e serve quindi ricalcolare '
        ' tutti gli hash '

        #FIXME: Devo cambiare il file!!!!!!!!!!
        self.__upToDate = in_file.readline()
        upToDate = False

        if(not upToDate):
            self.__reloadAllHashes()
        else:
            'Carico gli hash da file'
            for line in in_file:
                l = line.split(":")
                HashDataStructure.__dataMap[l[0]] = l[1][:-1]
            in_file.close()

    """
    Ricalcolo tutti gli hash dal filesystem
    """
    def __reloadAllHashes(self):
        HashDataStructure.__structureLock.release()
        import os
        child_list = os.listdir(self.__fs_root)
        for child in child_list:
            if child != self.__DATAPATH:
                from HashCalculator.HashCalculatorMD5 import HashCalculatorMD5
                hashCalculator = HashCalculatorMD5()
                if os.path.isfile("./" + child):
                    child_hash = hashCalculator.calculateFileHash("./" + child)
                else:
                    child_hash = hashCalculator.calculateDirectoryHash("./" + child, self.__fs_root, HashDataStructure.__dataMap)
                HashDataStructure.__dataMap[self.__fs_root + "/" + child] = child_hash
        HashDataStructure.__structureLock.acquire()

    """
    Questo metodo salva su file la mappa degli hash
    """
    def write_data_structure(self):
        dataStructure = self.get_data_structure_instance()
        if HashDataStructure.__dataMap is None:
            raise RuntimeError("La struttura non e' stata inizializzata")

        'Se sono sicuro che la struttura sia presente la posso scrivere su file'

        out_file = open(self.__fs_root + "/" + self.__DATAPATH, "w")
        self.__upToDate = True
        data = "" + self.__upToDate + "\n"
        for item in dataStructure:
            data = data + item + ":" + dataStructure[item] + "\n"
        out_file.write(data)
        out_file.close()
        self.release_data_structure()

    """
    Questo metodo prende solo l'hash del file a cui sono interessato. Se non
    e' presente nella struttura restituisce None
    """
    def get_file_hash(self, fileName):
        data = self.get_data_structure_instance()
        try:
            result = data[fileName]
        except Exception:
            result = None
        self.release_data_structure()  # Rilascio la struttura
        return result

    """
    Questo metodo inserisce un nuovo hash all'interno della struttura
    o ne modifica uno preesistente
    """
    def insert_hash(self, fileName, content):
        data = self.get_data_structure_instance()
        self.__upToDate = False
        data[fileName] = content
        self.release_data_structure()

    """
    Questo metodo elimina un hash dalla struttura modificando
    anche il file su cui e' memorizzato
    """
    def remove_hash(self, fileName):
        data = self.get_data_structure_instance()
        self.__upToDate = False
        data.pop(fileName, None)
        self.release_data_structure()
