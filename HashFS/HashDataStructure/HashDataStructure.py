from threading import Lock
class HashDataStructure(object):

    __INSTANCE = None
    __dataMap = None
    __fs_file_path = None

    __structureLock = None  # Semaforo per accedere alla struttura

    __DATAPATH = '.hashFSDataFile'  # Path del file degli hash

    def __init__(self, fs_file_path=""):
        self. __fs_file_path = fs_file_path  # Directory nella quale e' stato
                                            # montato il filesystem
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
            cls.__INSTANCE = HashDataStructure()
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
        if os.path.isfile(self.__fs_file_path + self.__DATAPATH):
            self.__load_data_map_from_file()
        else:
            out_file = open(self.__fs_file_path + self.__DATAPATH, "w")
            out_file.close()
            HashDataStructure.__dataMap = dict()

    """
    Questo metodo carica dal file .hashFSDataFile la mappa degli hash
    """
    def __load_data_map_from_file(self):
        HashDataStructure.__dataMap = dict()
        in_file = open(self.__fs_file_path + self.__DATAPATH, "r")
        for line in in_file:
            l = line.split(":")
            HashDataStructure.__dataMap[l[0]] = l[1][:-1]
        in_file.close()

    """
    Questo metodo salva su file la mappa degli hash
    """
    def __write_data_structure(self, dataStructure):
        if HashDataStructure.__dataMap is None:
            raise RuntimeError("La struttura non e' stata inizializzata")

        'Se sono sicuro che la struttura sia presente la posso scrivere su file'

        out_file = open(self.__fs_file_path + "/" + self.__DATAPATH, "w")
        data = ""
        for item in dataStructure:
            data = data + item + ":" + dataStructure[item] + "\n"
        out_file.write(data)
        out_file.close()

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
        data[fileName] = content
        self.__write_data_structure(data)
        self.release_data_structure()
