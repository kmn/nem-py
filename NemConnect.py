import json
import requests
import base64
import datetime
from binascii import hexlify, unhexlify

class NemConnect:
	def __init__(self, address, port):
		self.address = address
		self.port = port
		self.nemEpoch = datetime.datetime(2014, 8, 4, 0, 0, 0, 0, None)

	def nodeInfo(self):
		r = self.sendGet('node/info', None)
		if r.ok:
			j = r.json()
			if j['metaData']['application'] == 'NIS':
				return j
		return None

	def blockAt(self, h):
		data = { 'height': h }
		r = self.sendPost('block/at', data)

	def blocksAfter(self, height):
		data = { 'height': height }
		r = self.sendPost('local/chain/blocks-after', data)
		return r.json()

	def accountUnlock(self, privatekey):
		data = { 'value': privatekey }
		r = self.sendPost('account/unlock', data)
		if r.ok:
			return True, None
		return False, r.json()

	def accountLock(self, privatekey):
		data = { 'value': privatekey }
		r = self.sendPost('account/lock', data)
		if r.ok:
			return True, None
		return False, r.json()

	def transferPrepare(self, senderPublicKey, recipientCompressedKey, amount, message):
		now = datetime.datetime.utcnow()

		timeStamp = int((now - self.nemEpoch).total_seconds())
		data = {'type' : 0x101,
				'version' : 1,
				'signer' : senderPublicKey,
				'recipient' : recipientCompressedKey,
				'amount' : amount,
				'timeStamp' : timeStamp,
				'deadline' : timeStamp + 60*10,
				'fee': (amount/100 + 5),
				'message' : { 'type': 1, 'payload':hexlify(message) }
				}
		r = self.sendPost('transaction/prepare', data)
		return r.ok, r.json()

	def importanceTransferPrepare(self, senderPublicKey, remotePublicKey, doAssign):
		now = datetime.datetime.utcnow()

		timeStamp = int((now - self.nemEpoch).total_seconds())
		data = {'type' : 0x801,
				'version' : 1,
				'signer' : senderPublicKey,
				'mode' : 1 if doAssign else 2,
				'remoteAccount' : remotePublicKey,
				'timeStamp' : timeStamp,
				'deadline' : timeStamp + 60*10,
				'fee': 1000000,
				}
		r = self.sendPost('transaction/prepare', data)
		return r.ok, r.json()

	def transferAnnounce(self, transferData, transferSignature):
		data = { 'data': transferData,
				 'signature': transferSignature
				 }
		r = self.sendPost('transaction/announce', data)
		return r.ok, r.json()

	def sendGet(self, callName, data):
		headers = {'Content-type': 'application/json' }
		uri = 'http://' + self.address + ':' + str(self.port) + '/' + callName
		return requests.get(uri, data=json.dumps(data), headers=headers, timeout=10)

	def sendPost(self, callName, data):
		headers = {'Content-type': 'application/json' }
		uri = 'http://' + self.address + ':' + str(self.port) + '/' + callName
		return requests.post(uri, data=json.dumps(data), headers=headers, timeout=10)

