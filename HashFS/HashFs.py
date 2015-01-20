#!/usr/bin/env python

import os, sys
import fcntl
from errno import *
from stat import *

# Importo FUSE
import fuse
from fuse import Fuse

# Importo la strutura contenente gli hash e la funzione per calcolare un hash
from HashCalculator.HashCalculatorMD5 import HashCalculatorMD5
from HashDataStructure.HashDataStructure import HashDataStructure


if not hasattr(fuse, '__version__'):
    raise RuntimeError, \
        "your fuse-py doesn't know of fuse.__version__, probably it's too old."

fuse.fuse_python_api = (0, 2)

# We use a custom file class
fuse.feature_assert('stateful_files', 'has_init')


def flag2mode(flags):
    md = {os.O_RDONLY: 'r', os.O_WRONLY: 'w', os.O_RDWR: 'w+'}
    m = md[flags & (os.O_RDONLY | os.O_WRONLY | os.O_RDWR)]

    if flags | os.O_APPEND:
        m = m.replace('w', 'a', 1)

    return m

"""
Questa funzione aggiorna l'hash di una directory e dei suoi genitori
"""
def updateDirectoryHash(path, hash_data_structure, hash_calculator):
    # Creo l'entry della cartella nella struttura degli hash
    dir_hash = hash_calculator.calculateDirectoryHash("." + path)
    hash_data_structure.insert_hash(root_directory + path, dir_hash)

    # Aggiorno gli eventuali genitori
    parent_path = os.path.abspath(os.path.join(root_directory + path, os.pardir))
    while(parent_path != root_directory):
        # Calcolo l'hash del genitore
        parent_hash = hash_calculator.calculateDirectoryHash(parent_path)
        hash_data_structure.insert_hash(parent_path, parent_hash)
        parent_path = os.path.abspath(os.path.join(parent_path, os.pardir))


'''
Costruisco la directory di root per il filesystem a partire dalla home
'''
from os.path import expanduser
home = expanduser("~")

root_directory = home + "/HashFS"
hash_data_structure = HashDataStructure(root_directory)
hash_calculator = HashCalculatorMD5()

class HashFs(Fuse): # Gestione del filesystem

    def __init__(self, *args, **kw):

        Fuse.__init__(self, *args, **kw)

        if not os.path.exists(root_directory):
            os.makedirs(root_directory)

        self.root = root_directory
        self.file_class = self.HashFSFile

        # Prendo la struttura per la memorizzazione degli hash
        self.hash_data_structure = hash_data_structure

        # Creo la classe per il calcolo dell'hash
        self.hash_calculator = hash_calculator

    def getattr(self, path):
        return os.lstat("." + path)

    def readlink(self, path):
        return os.readlink("." + path)

    def readdir(self, path, offset):
        for e in os.listdir("." + path):
            yield fuse.Direntry(e)

    def unlink(self, path):
        os.unlink("." + path)
        # Rimuovo la relativa entry dalla struttura
        self.hash_data_structure.remove_hash(root_directory + path)
        # Aggiorno le eventuali directory al livello superiore
        parent_path = os.path.abspath(os.path.join(path, os.pardir))
        if(parent_path != "/"):
            updateDirectoryHash(parent_path, self.hash_data_structure, self.hash_calculator)

    def rmdir(self, path):
        os.rmdir("." + path)
        # Rimuovo la relativa entry dalla struttura
        self.hash_data_structure.remove_hash(root_directory + path)
        # Aggiorno le eventuali directory al livello superiore
        parent_path = os.path.abspath(os.path.join(path, os.pardir))
        if(parent_path != "/"):
            updateDirectoryHash(parent_path, self.hash_data_structure, self.hash_calculator)

    def symlink(self, path, path1):
        os.symlink(path, "." + path1)
        # Aggiungo l'entry nella struttura e aggiorno i genitori
        file_hash = self.hash_calculator.calculateFileHash("." + path1)
        self.hash_data_structure.insert_hash(root_directory + path1,file_hash)
        parent_path = os.path.abspath(os.path.join(path1, os.pardir))
        if(parent_path != "/"):
            updateDirectoryHash(parent_path, self.hash_data_structure, self.hash_calculator)


    def rename(self, path, path1):
        os.rename("." + path, "." + path1)
        
        # Una volta rinominato il file o la cartella, aggiorno la struttura dati contenente gli hash
        self.hash_data_structure.remove_hash(root_directory + path)

        if os.path.isdir("." + path1):
            # Modifico i figli della directory
            self.__update_child_path(path1, path)
            updateDirectoryHash(path1, self.hash_data_structure, self.hash_calculator)
        else:
            file_hash = self.hash_calculator.calculateFileHash("." + path1)
            self.hash_data_structure.insert_hash(root_directory + path1, file_hash)
            # Aggiorno la cartella padre
            parent_path = os.path.abspath(os.path.join(path1, os.pardir))
            if(parent_path != "/"):
                updateDirectoryHash(parent_path, self.hash_data_structure, self.hash_calculator)

    """
    Questa funzione calcola in maniera ricorsiva l'hash dei figli di una cartella rinominata
    """
    def __update_child_path(self, new_path, old_path):
        if(os.path.isdir("." + new_path)):
            children = os.listdir("." + new_path)
            if(len(children)):
                # Se entro qui vuol dire che la cartella non e' vuota
                for child in children:
                    child_path = os.path.join(new_path, child)
                    if os.path.isfile(child_path):
                        # Se e' un file mi limito a cambiarne l'hash
                        self.hash_data_structure.remove_hash(root_directory + old_path)
                        file_hash = self.hash_calculator.calculateFileHash("." + child_path)
                        self.hash_data_structure.insert_hash(root_directory + new_path, file_hash)
                    else:
                        # Se e' una cartella vado ad aggiornare l'hash per i livelli inferiori
                        old_child_path = os.path.join(old_path, child)
                        self.__update_child_path(child_path, old_child_path)
            else:
                # Se sono all'ultimo livello aggiorno l'intera struttura
                updateDirectoryHash(new_path, self.hash_data_structure, self.hash_calculator)
        else:
            # All'ultimo livello vi era un file
            file_hash = self.hash_calculator.calculateFileHash("." + new_path)
            self.hash_data_structure.insert_hash(root_directory + new_path, file_hash)
            # Aggiorno la cartella padre
            parent_path = os.path.abspath(os.path.join(new_path, os.pardir))
            updateDirectoryHash(parent_path, self.hash_data_structure, self.hash_calculator)

        # Rimuovo la vecchia entry dalla struttura
        self.hash_data_structure.remove_hash(root_directory + old_path)


    def link(self, path, path1):
        os.link("." + path, "." + path1)

    def chmod(self, path, mode):
        os.chmod("." + path, mode)

    def chown(self, path, user, group):
        os.chown("." + path, user, group)

    def truncate(self, path, len):
        f = open("." + path, "a")
        f.truncate(len)
        f.close()

    def mknod(self, path, mode, dev):
        os.mknod("." + path, mode, dev)
        # Aggiungo l'entry nella struttura e aggiorno i genitori
        file_hash = self.hash_calculator.calculateFileHash("." + path)
        self.hash_data_structure.insert_hash(root_directory + path, file_hash)
        parent_path = os.path.abspath(os.path.join(path, os.pardir))
        if(parent_path != "/"):
            updateDirectoryHash(parent_path, self.hash_data_structure, self.hash_calculator)

    def mkdir(self, path, mode):
        os.mkdir("." + path, mode)
        # Aggiungo l'hash di questa directory e aggiorno i genitori
        updateDirectoryHash(path, self.hash_data_structure, self.hash_calculator)

    def utime(self, path, times):
        os.utime("." + path, times)

    def access(self, path, mode):
        if not os.access("." + path, mode):
            return -EACCES

    """
    Metodi per la gestione dell'attributo esteso (l'hash del file o cartella)
    Per vedere l'hash: getfattr -n hash nomeFileOCartella 
    """

    def getxattr(self, path, name, size):
        value = self.hash_data_structure.get_file_hash(self.root + path)
        if size == 0:
            # We are asked for size of the attr list, ie. joint size of attrs
            # plus null separators.
            return len(value)
        return value

    def listxattr(self, path, size):
        attrs = ["hash"]
        if size == 0:
            return len(attrs) + len("".join(attrs))
        return attrs

    def removexattr(self, path):
        del self._storage[path]

    def statfs(self):
        """
        Should return an object with statvfs attributes (f_bsize, f_frsize...).
        Eg., the return value of os.statvfs() is such a thing (since py 2.2).
        If you are not reusing an existing statvfs object, start with
        fuse.StatVFS(), and define the attributes.

        To provide usable information (ie., you want sensible df(1)
        output, you are suggested to specify the following attributes:

            - f_bsize - preferred size of file blocks, in bytes
            - f_frsize - fundamental size of file blcoks, in bytes
                [if you have no idea, use the same as blocksize]
            - f_blocks - total number of blocks in the filesystem
            - f_bfree - number of free blocks
            - f_files - total number of file inodes
            - f_ffree - nunber of free file inodes
        """

        return os.statvfs(".")

    def fsinit(self):
        os.chdir(self.root)

#     def fsdestroy(self, data = None):
#         import syslog
#         syslog.syslog(syslog.LOG_INFO, 'destroy %s: %s' % (self.mountpoint, data))
#         os.rmdir(self.mountpoint)


    class HashFSFile(object): # Gestione dei file

        def __init__(self, path, flags, *mode):

            # Prendo la struttura per la memorizzazione degli hash
            self.hash_data_structure = hash_data_structure

            # Creo la classe per il calcolo dell'hash
            self.hash_calculator = hash_calculator

            self.root = root_directory

            if(os.path.isfile("." + path)):
                self.file = os.fdopen(os.open("." + path, flags, *mode),
                                      flag2mode(flags))
                self.fd = self.file.fileno()
            else:
                # Se entro qui sto creando il file per la prima volta o vi
                # sto scrivendo all'interno, di conseguenza creo l'entry all'interno della struttura
                self.file = os.fdopen(os.open("." + path, flags, *mode),
                                      flag2mode(flags))
                self.fd = self.file.fileno()
                # Aggiungo l'entry nella struttura e aggiorno i genitori
                file_hash = self.hash_calculator.calculateFileHash("." + path)
                self.hash_data_structure.insert_hash(root_directory + path, file_hash)
                parent_path = os.path.abspath(os.path.join(path, os.pardir))
                if(parent_path != "/"):
                    updateDirectoryHash(parent_path, self.hash_data_structure, self.hash_calculator)

        def read(self, length, offset):
            self.file.seek(offset)
            return self.file.read(length)

        def write(self, buf, offset):
            self.file.seek(offset)
            self.file.write(buf)
            return len(buf)

        def release(self, flags):
            self.file.close()

        def _fflush(self):
            if 'w' in self.file.mode or 'a' in self.file.mode:
                self.file.flush()

        def fsync(self, isfsyncfile):
            self._fflush()
            if isfsyncfile and hasattr(os, 'fdatasync'):
                os.fdatasync(self.fd)
            else:
                os.fsync(self.fd)

        def flush(self):
            self._fflush()
            # cf. xmp_flush() in fusexmp_fh.c
            os.close(os.dup(self.fd))

        def fgetattr(self):
            return os.fstat(self.fd)

        def ftruncate(self, len):
            self.file.truncate(len)

        def lock(self, cmd, owner, **kw):
            # The code here is much rather just a demonstration of the locking
            # API than something which actually was seen to be useful.

            # Advisory file locking is pretty messy in Unix, and the Python
            # interface to this doesn't make it better.
            # We can't do fcntl(2)/F_GETLK from Python in a platfrom independent
            # way. The following implementation *might* work under Linux.
            #
            # if cmd == fcntl.F_GETLK:
            #     import struct
            #
            #     lockdata = struct.pack('hhQQi', kw['l_type'], os.SEEK_SET,
            #                            kw['l_start'], kw['l_len'], kw['l_pid'])
            #     ld2 = fcntl.fcntl(self.fd, fcntl.F_GETLK, lockdata)
            #     flockfields = ('l_type', 'l_whence', 'l_start', 'l_len', 'l_pid')
            #     uld2 = struct.unpack('hhQQi', ld2)
            #     res = {}
            #     for i in xrange(len(uld2)):
            #          res[flockfields[i]] = uld2[i]
            #
            #     return fuse.Flock(**res)

            # Convert fcntl-ish lock parameters to Python's weird
            # lockf(3)/flock(2) medley locking API...
            op = { fcntl.F_UNLCK : fcntl.LOCK_UN,
                   fcntl.F_RDLCK : fcntl.LOCK_SH,
                   fcntl.F_WRLCK : fcntl.LOCK_EX }[kw['l_type']]
            if cmd == fcntl.F_GETLK:
                return -EOPNOTSUPP
            elif cmd == fcntl.F_SETLK:
                if op != fcntl.LOCK_UN:
                    op |= fcntl.LOCK_NB
            elif cmd == fcntl.F_SETLKW:
                pass
            else:
                return -EINVAL

            fcntl.lockf(self.fd, op, kw['l_start'], kw['l_len'])



def main():

    usage = """
Userspace nullfs-alike: mirror the filesystem tree from some point on.

""" + Fuse.fusage

    server = HashFs(version="%prog " + fuse.__version__,
                 usage=usage)

    server.parser.add_option(mountopt="root", metavar="PATH", default='/',
                             help="mirror filesystem from under PATH [default: %default]")
    server.parse(values=server, errex=1)

    try:
        if server.fuse_args.mount_expected():
            os.chdir(server.root)
    except OSError:
        print >> sys.stderr, "can't enter root of underlying filesystem"
        sys.exit(1)

    server.main()


if __name__ == '__main__':
    main()
