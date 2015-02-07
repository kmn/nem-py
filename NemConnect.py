import json
import requests
import base64
import datetime
from binascii import hexlify, unhexlify
from math import ceil,log

class NemConnect:
	def __init__(self, address, port):
		self.address = address
		self.port = port
		self.nemEpoch = datetime.datetime(2015, 2, 1, 0, 0, 0, 0, None)

	def getTimeStamp(self):
		now = datetime.datetime.utcnow()
		return int((now - self.nemEpoch).total_seconds())

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

	@staticmethod
	def createData(txtype, senderPublicKey, timeStamp):
		return {'type' : txtype,
				'version' : 1,
				'signer' : senderPublicKey,
				'timeStamp' : timeStamp,
				'deadline' : timeStamp + 60*10
				}

	@staticmethod
	def minFee(amount):
		print amount
		return max(2, ceil(amount / 12500 + log(2*amount) / 5))

	def constructTransfer(self, senderPublicKey, recipientCompressedKey, amount, message):
		timeStamp = self.getTimeStamp()
		data = NemConnect.createData(0x101, senderPublicKey, timeStamp)
		fee = NemConnect.minFee(amount / 100000.0) 
		custom = {
				'recipient' : recipientCompressedKey,
				'amount' : amount,
				'fee': fee,
				'message' : { 'type': 1, 'payload':hexlify(message) }
		}
		entity = dict(data.items() + custom.items())
		return entity

	def transferPrepare(self, senderPublicKey, recipientCompressedKey, amount, message):
		entity = self.constructTransfer(senderPublicKey, recipientCompressedKey, amount, message)
		r = self.sendPost('transaction/prepare', entity)
		return r.ok, r.json()

	def importanceTransferPrepare(self, senderPublicKey, remotePublicKey, doAssign):
		timeStamp = self.getTimeStamp()
		data = NemConnect.createData(0x801, senderPublicKey, timeStamp)
		custom = {
				'mode' : 1 if doAssign else 2,
				'remoteAccount' : remotePublicKey,
				'fee': 1000000,
				}
		entity = dict(data.items() + custom.items())
		r = self.sendPost('transaction/prepare', entity)
		return r.ok, r.json()

	def multisigCreatePrepare(self, senderPublicKey, cosignatories):
		timeStamp = self.getTimeStamp()
		data = NemConnect.createData(0x1001, senderPublicKey, timeStamp)
		custom = {
				'fee' : 6000000*(len(cosignatories) + 1),
				'modifications' : [
					{'modificationType': 1, 'cosignatoryAccount' : publicKey }
					for publicKey in cosignatories
				]
		}
		entity = dict(data.items() + custom.items())
		r = self.sendPost('transaction/prepare', entity)
		return r.ok, r.json()

	def multisigTransferPrepare(self, senderPublicKey, multisig, recipientCompressedKey, amount, message):
		timeStamp = self.getTimeStamp()
		data = NemConnect.createData(0x1004, senderPublicKey, timeStamp)
		transfer = self.constructTransfer(multisig, recipientCompressedKey, amount, message)
		custom = {
				'fee' : 123,
				'otherTrans' : transfer
		}
		entity = dict(data.items() + custom.items())
		r = self.sendPost('transaction/prepare', entity)
		return r.ok, r.json()

	def multisigSignaturePrepare(self, senderPublicKey, txHash):
		timeStamp = self.getTimeStamp()
		data = NemConnect.createData(0x1002, senderPublicKey, timeStamp)
		custom = {
				'fee' : 123,
				'otherHash' : { 'data': txHash }
		}
		entity = dict(data.items() + custom.items())
		r = self.sendPost('transaction/prepare', entity)
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

