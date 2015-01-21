"""
Questa classe si occupa di calcolare l'hash dei file del filesystem usando l'algoritmo MD5
"""
from HashCalculator import HashCalculator

class HashCalculatorMD5(HashCalculator):

    def __init__(self):
        import hashlib
        self._hash_calculator = hashlib.md5()

    def create_hash_calculator(self):
        import hashlib
        self._hash_calculator = hashlib.md5()