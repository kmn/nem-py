import sys
import ed25519
from binascii import hexlify, unhexlify

sys.path.insert(0, 'python-sha3')
from python_sha3 import *

class Account:
	def __init__(self, hexPrivKey):
		self.hexPrivKey = hexPrivKey
		self._calculateKeyPair()

	def _calculateKeyPair(self):
		self.sk = unhexlify(self.hexPrivKey)[::-1]
		self.pk = ed25519.publickey_hash_unsafe(self.sk, sha3_512)

		self.hexPublicKey = hexlify(self.pk)

	def getHexPublicKey(self):
		return self.hexPublicKey

	def getHexPrivateKey(self):
		return self.hexPrivKey

	def sign(self, binMessage):
		signature = ed25519.signature_hash_unsafe(binMessage, self.sk, self.pk, sha3_512)
		#print '  sig:', hexlify(signature)
		return signature
	
	def verify(self, hexedMessage):
		pass
