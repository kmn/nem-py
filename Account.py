import ed25519
from python_sha3.python_sha3 import *

import base64
import hashlib
from binascii import hexlify, unhexlify


class Account:
    def __init__(self, hexPrivKey, network='mainnet'):
        self.hexPrivKey = hexPrivKey
        self.network = network
        self._calculateKeyPair()
        self._calculateAddress()

    def _calculateKeyPair(self):
        self.sk = unhexlify(self.hexPrivKey)[::-1]
        self.pk = ed25519.publickey_hash_unsafe(self.sk, sha3_512)

        self.hexPublicKey = hexlify(self.pk)

    def _calculateAddress(self):
        pubkey = self.pk

        s = sha3_256()
        s.update(pubkey)
        sha3_pubkey = s.digest()

        h = hashlib.new('ripemd160')
        h.update(sha3_pubkey)
        ripe = h.digest()

        if self.network == 'testnet':
            version = "\x98" + ripe
        else:
            version = "\x68" + ripe

        s2 = sha3_256()
        s2.update(version)
        checksum = s2.digest()[0:4]

        self.address = base64.b32encode(version + checksum)

    def getHexPublicKey(self):
        return self.hexPublicKey

    def getHexPrivateKey(self):
        return self.hexPrivKey

    def getAddress(self):
        return self.address

    def sign(self, binMessage):
        signature = ed25519.signature_hash_unsafe(binMessage, self.sk, self.pk, sha3_512)
        # print '  sig:', hexlify(signature)
        return signature

    def verify(self, hexedMessage):
        pass
