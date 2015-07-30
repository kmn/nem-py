import argparse
import ed25519
import inspect
import re
import sys
from binascii import hexlify, unhexlify
from Account import Account

sys.path.insert(0, 'python-sha3')
from python_sha3 import *

parser = argparse.ArgumentParser(description='nem test vectors')
g = parser.add_mutually_exclusive_group()
g.add_argument('--test-sha3-256-file', metavar='filename', help='test sha3 implementation')
g.add_argument('--test-keys-file', metavar='filename', help='test public and address generation')
g.add_argument('--test-sign-file', metavar='filename', help='test signing')

def verifySha3_256(line):
	"""^: ([0-9a-f]+) : ([0-9]{2,3}) : ([0-9a-f]+)$"""
	f = inspect.currentframe()
	rematch = f.f_back.f_globals[f.f_code.co_name].__doc__
	res = re.match(rematch, line)
	if not res:
		return False
	expectedHash = unhexlify(res.group(1))
	dataLength = int(res.group(2))
	data = unhexlify(res.group(3))
	assert(len(data) == dataLength)
	computedHash = sha3_256(data).digest()
	if computedHash == expectedHash:
		return True
	else:
		print('Failed hash:')
		print('  computed:' + hexlify(computedHash))
		print('  expected:' + hexlify(expectedHash))
		return False

def verifyKey(line):
	"""^: ([a-f0-9]+) : ([a-f0-9]+) : ([a-f0-9]+) : ([A-Z2-7]+)$"""
	f = inspect.currentframe()
	rematch = f.f_back.f_globals[f.f_code.co_name].__doc__
	res = re.match(rematch, line)
	if not res:
		return False

	privateKeyHex = res.group(1)
	expectedPublic = unhexlify(res.group(3))
	expectedAddress = res.group(4)

	account = Account(privateKeyHex)
	if account.pk == expectedPublic:
		if account.address == expectedAddress:
			return True
		else:
			print('Failed when calculating address:')
			print('  computed address:' + account.address)
			print('  expected address:' + expectedAddress)
			return False

	else:
		print('Failed public from private:')
		print('  computed public:' + hexlify(accountp.pk))
		print('  expected public:' + hexlify(expectedPublic))
		return False

def verifySign(line):
	""": ([a-f0-9]+) : ([a-f0-9]+) : ([a-f0-9]+) : ([0-9]{2}) : ([a-f0-9]+)$"""
	f = inspect.currentframe()
	rematch = f.f_back.f_globals[f.f_code.co_name].__doc__
	res = re.match(rematch, line)
	if not res:
		return False

	privateKeyHex = res.group(1)
	expectedPublic = unhexlify(res.group(2))
	expectedSignature = unhexlify(res.group(3))
	dataLength = int(res.group(4))
	data = unhexlify(res.group(5))
	assert(len(data) == dataLength)

	account = Account(privateKeyHex)
	if account.pk == expectedPublic:
		computedSignature = account.sign(data)
		if computedSignature == expectedSignature:
			return True
		else:
			print('Failed when calculating signature:')
			print('  computed signature:' + hexlify(computedSignature))
			print('  expected signature:' + hexlify(expectedSignature))
			return False

	else:
		print('Failed public from private:')
		print('  computed public:' + hexlify(account.pk))
		print('  expected public:' + hexlify(expectedPublic))
		return False


def testFile(filename, cbfun):
	with open(filename, 'r') as f:
		c = 0
		for l in f:
			line = l.strip()
			if line.startswith('#'):
				continue

			if not cbfun(line):
				c = 0
				break
			c += 1
			if (c % 31) == 0:
				print('\rtest: ' + str(c)),
		if c != 0:
			print('')
			print(str(c) + ' PASSED')

args = parser.parse_args()

if args.test_sha3_256_file:
	testFile(args.test_sha3_256_file, verifySha3_256)
elif args.test_keys_file:
	testFile(args.test_keys_file, verifyKey)
elif args.test_sign_file:
	testFile(args.test_sign_file, verifySign)
