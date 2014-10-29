from binascii import hexlify, unhexlify
from hashlib import sha512
import sys
import ed25519

sys.path.insert(0, 'python-sha3')
from python_sha3 import *

# unhexlify and reverse
sk = unhexlify('11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff')[::-1]

pk0 = ed25519.publickey_unsafe(sk)
pk1 = ed25519.publickey_hash_unsafe(sk, sha512)
pk2 = ed25519.publickey_hash_unsafe(sk, sha3_512)

print '          sec key:', hexlify(sk)
print 'VALID NEM pub key:', hexlify(pk2)
print '-'*80

print 'NOT valid NEM pub keys produced by original ed25519'
print 'v1:', hexlify(pk0)
print 'v2:', hexlify(pk1)

