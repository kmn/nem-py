import json
import requests
import base64
import datetime
from binascii import hexlify, unhexlify
from math import floor, ceil, log, atan


def MAIN_NET_VERSION(ver):
    return (0x68000000 | ver)


def TEST_NET_VERSION(ver):
    return (0x98000000 | ver)


CURRENT_MOSAIC_SINK = 'TBMOSAICOD4F54EE5CDMR23CCBGOAM2XSJBR5OLC'
CURRENT_NAMESPACE_SINK = 'TAMESPACEWH4MKFMBCVFERDPOOP4FK7MTDJEYP35'
CURRENT_NETWORK_VERSION = TEST_NET_VERSION

#CURRENT_MOSAIC_SINK = 'MBMOSAICOD4F54EE5CDMR23CCBGOAM2XSKYHTOJD'
#CURRENT_NAMESPACE_SINK = 'MAMESPACEWH4MKFMBCVFERDPOOP4FK7MTCZTG5E7'
#def CURRENT_NETWORK_VERSION(ver):
#    return (0x60000000 | ver)


class NemConnect:
    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.nemEpoch = datetime.datetime(2015, 3, 29, 0, 6, 25, 0, None)

    def getTimeStamp(self):
        now = datetime.datetime.utcnow()
        return int((now - self.nemEpoch).total_seconds())

    def testnetNodeInfo(self):
        r = self.sendGet('node/info', None)
        if r.ok:
            j = r.json()
            return j
        return None

    def nodeInfo(self):
        r = self.sendGet('node/info', None)
        if r.ok:
            j = r.json()
            print(j)
            if j['metaData']['application'] == 'NIS':
                return j
        return None

    def blockAt(self, h):
        data = {'height': h}
        r = self.sendPost('block/at/public', data)
        return r.json()

    def blocksAfter(self, height):
        data = {'height': height}
        r = self.sendPost('local/chain/blocks-after', data)
        return r.json()

    def chainHeight(self):
        r = self.sendGet('chain/height', None)
        if r.ok:
            return True, r.json()
        return False, r.json()

    def accountGet(self, address):
        data = {'address': address}
        r = self.sendGet('account/get', data)
        if r.ok:
            return True, r.json()
        return False, r.json()

    def accountOwnedMosaicsGet(self, address):
        data = {'address': address}
        r = self.sendGet('account/mosaic/owned', data)
        if r.ok:
            return True, r.json()
        return False, r.json()

    def accountUnlock(self, privatekey):
        data = {'value': privatekey}
        r = self.sendPost('account/unlock', data)
        if r.ok:
            return True, None
        return False, r.json()

    def accountIsUnlocked(self, privatekey):
        data = {'value': privatekey}
        r = self.sendPost('local/account/isunlocked', data)
        if r.ok:
            return True, None
        return False, r.json()

    def accountLock(self, privatekey):
        data = {'value': privatekey}
        r = self.sendPost('account/lock', data)
        if r.ok:
            return True, None
        return False, r.json()

    def namespaceGet(self, namespace):
        data = {'namespace': namespace}
        r = self.sendGet('namespace', data)
        if r.ok:
            return True, r.json()
        return False, r.json()

    def mosaicDefinition(self, mosaicFqdn):
        r = self.sendGet('mosaic/definition', {'mosaicId': mosaicFqdn})
        if r.ok:
            return True, r.json()
        return False, r.json()

    def mosaicSupply(self, mosaicFqdn):
        r = self.sendGet('mosaic/supply', {'mosaicId': mosaicFqdn})
        if r.ok:
            return True, r.json()
        return False, r.json()

    @staticmethod
    def createData(txtype, senderPublicKey, timeStamp, version=CURRENT_NETWORK_VERSION(1)):
        return {'type': txtype,
                'version': version,
                'signer': senderPublicKey,
                'timeStamp': timeStamp,
                'deadline': timeStamp + 60 * 60
                }

    @staticmethod
    def calcMinFee(numNem):
        '''
        calcurate transfer fee
        https://forum.nem.io/t/nem-update-0-6-82-lower-fees-and-new-api/2979
        '''
        if numNem < 20000:
            fee = 1;
        elif numNem > 250000:
            fee = 25;
        else:
            fee = floor(numNem / 1000);
        return fee

    def calcMessageFee(numNem):
        return floor(len(message) / 32) + 1

    def _constructTransfer(self, senderPublicKey, recipientCompressedKey, amount, message, mosaics, mosaicsFee):
        timeStamp = self.getTimeStamp()
        version = CURRENT_NETWORK_VERSION(2) if mosaics else CURRENT_NETWORK_VERSION(1)
        data = NemConnect.createData(0x101, senderPublicKey, timeStamp, version)
        msgFee = 0 if len(message) == 0 else max(1, len(message) / 16) * 2
        fee = mosaicsFee if mosaics else NemConnect.calcMinFee(amount / 1000000)
        totalFee = (msgFee + fee)
        totalFee *= 1000000
        custom = {
            'recipient': recipientCompressedKey.replace('-', ''),
            'amount': amount,
            'fee': totalFee,
            'message': {'type': 1, 'payload': hexlify(message)}
        }
        if mosaics:
            custom['mosaics'] = mosaics
            print "Attached mosaic:", custom['mosaics']
        entity = dict(data.items() + custom.items())
        return entity

    def _constructImportanceTransfer(self, senderPublicKey, remotePublicKey, doAssign):
        timeStamp = self.getTimeStamp()
        data = NemConnect.createData(0x801, senderPublicKey, timeStamp)
        custom = {
            'mode': 1 if doAssign else 2,
            'remoteAccount': remotePublicKey,
            'fee': 8000000,
        }
        entity = dict(data.items() + custom.items())
        return entity

    def _constructModification(self, senderPublicKey, cosignatories):
        timeStamp = self.getTimeStamp()
        data = NemConnect.createData(0x1001, senderPublicKey, timeStamp)
        custom = {
            'fee': 2 * (5000000 + 3000000 * (len(cosignatories))),
            'modifications': [
                {'modificationType': 2, 'cosignatoryAccount': publicKey}
                for publicKey in cosignatories
                ]
        }
        entity = dict(data.items() + custom.items())
        return entity

    def _constructNamespace(self, senderPublicKey, namespaceFqn):
        timeStamp = self.getTimeStamp()
        data = NemConnect.createData(0x2001, senderPublicKey, timeStamp)
        parts = namespaceFqn.split('.')
        rental = 50000 if len(parts) == 1 else 5000
        custom = {
            'rentalFeeSink': CURRENT_NAMESPACE_SINK,
            'fee': 2 * 3 * 18 * 1000000,
            'rentalFee': rental * 1000000,
            'newPart': parts[-1],
        }
        if len(parts) > 1:
            custom['parent'] = '.'.join(parts[:-1])
        entity = dict(data.items() + custom.items())
        return entity

    @staticmethod
    def parseMosaicFqn(mosaicFqn):
        if " * " in mosaicFqn:
            return mosaicFqn.split(" * ")
        else:
            parts = mosaicFqn.split('.')
            return ('.'.join(parts[:-1]), parts[-1])

    def _constructMosaic(self, senderPublicKey, mosaicFqn, description, props):
        timeStamp = self.getTimeStamp()
        data = NemConnect.createData(0x4001, senderPublicKey, timeStamp)

        namespaceFqn,mosaicName = NemConnect.parseMosaicFqn(mosaicFqn)
        custom = {
            'mosaicDefinition': {
                'creator': senderPublicKey,
                'id': {
                    'namespaceId': namespaceFqn,
                    'name': mosaicName
                },
                'description': description,
                'properties': [
                    {'name': 'divisibility', 'value': str(props['divisibility'])},
                    {'name': 'initialSupply', 'value': str(props['initialSupply'])},
                    {'name': 'supplyMutable', 'value': str(props['supplyMutable'])},
                    {'name': 'transferable', 'value': str(props['transferable'])}
                ],
            },
            'creationFeeSink': CURRENT_MOSAIC_SINK,
            'creationFee': 50000 * 1000000,
            'fee': 2 * 3 * 18 * 1000000
        }
        if 'levy' in props:
            levyFqn = props['levy']['mosaicFqn']
            namespaceFqn,mosaicName = NemConnect.parseMosaicFqn(levyFqn)

            custom['mosaicDefinition']['levy'] = {
                "type": props['levy']['type'],
                "recipient": props['levy']['recipient'].replace('-', ''),
                "mosaicId": {
                    'namespaceId': namespaceFqn,
                    'name': mosaicName
                },
                "fee": props['levy']['fee']
            }
        entity = dict(data.items() + custom.items())
        return entity

    def _constructMosaicSupply(self, senderPublicKey, mosaicFqn, supplyType, supplyDelta):
        timeStamp = self.getTimeStamp()
        data = NemConnect.createData(0x4002, senderPublicKey, timeStamp)

        namespaceFqn,mosaicName = NemConnect.parseMosaicFqn(mosaicFqn)
        custom = {
            'mosaicId': {
                'namespaceId': namespaceFqn,
                'name': mosaicName
            },
            'supplyType': supplyType,
            'delta': int(supplyDelta),
            'fee': 2 * 3 * 18 * 1000000
        }
        entity = dict(data.items() + custom.items())
        return entity

    def _prepare(self, entity):
        r = self.sendPost('transaction/prepare', entity)
        return r.ok, r.json()

    def _multisigWrapper(self, senderPublicKey, entity):
        timeStamp = self.getTimeStamp()
        data = NemConnect.createData(0x1004, senderPublicKey, timeStamp)
        custom = {
            'fee': 18000000,
            'otherTrans': entity
        }
        entity = dict(data.items() + custom.items())
        print " {+} multisig wrapped"
        return entity

    @staticmethod
    def calcXemEquivalent(amount, q, sup, divi):
        if sup == 0:
            return 0

        multiplier = amount  # int(self.transferAmount.get()) * 1000000
        equivalent = 8999999999 * q * multiplier / sup / (10 ** (divi + 6))
        return equivalent

    def calculateMosaicsFee(self, amount, mosaics):
        data = {'fee': 0, 'mosaics': []}
        for m in mosaics:
            quantity = m[1]
            mosaicFqn = m[0]
            namespaceFqn,mosaicName = NemConnect.parseMosaicFqn(mosaicFqn)
            ok, j = self.mosaicDefinition(namespaceFqn + ' * ' + mosaicName)
            if not ok:
                return ok, j
            divisibility = int((x for x in j['properties'] if x['name'] == 'divisibility').next()['value'])

            ok, j = self.mosaicSupply(namespaceFqn + ' * ' + mosaicName)
            if not ok:
                return ok, j

            supply = int(j['supply'])

            numNem = NemConnect.calcXemEquivalent(amount, quantity, supply, divisibility)
            data['fee'] += NemConnect.calcMinFee(numNem)
            data['mosaics'].append(
                {
                    'mosaicId': {
                        'namespaceId': namespaceFqn,
                        'name': mosaicName
                    },
                    'quantity': quantity
                }
            )
        data['fee'] = data['fee'] * 5 / 4
        return True, data

    def prepareTransfer(self, senderPublicKey, multisigPublicKey, recipientCompressedKey, amount, message, mosaics):
        mosaicsFee = 0
        if mosaics:
            ok, j = self.calculateMosaicsFee(amount, mosaics)
            if not ok:
                return ok, j
            mosaicsFee = j['fee']
            mosaics = j['mosaics']

        actualSender = multisigPublicKey or senderPublicKey
        entity = self._constructTransfer(actualSender, recipientCompressedKey, amount, message, mosaics, mosaicsFee)
        if multisigPublicKey:
            entity = self._multisigWrapper(senderPublicKey, entity)
        return self._prepare(entity)

    def prepareImportanceTransfer(self, senderPublicKey, multisigPublicKey, remotePublicKey, doAssign):
        actualSender = multisigPublicKey or senderPublicKey
        entity = self._constructImportanceTransfer(actualSender, remotePublicKey, doAssign)
        if multisigPublicKey:
            entity = self._multisigWrapper(senderPublicKey, entity)
        return self._prepare(entity)

    def prepareProvisionNamespace(self, senderPublicKey, multisigPublicKey, namespaceFqn):
        actualSender = multisigPublicKey or senderPublicKey
        entity = self._constructNamespace(actualSender, namespaceFqn)
        if multisigPublicKey:
            entity = self._multisigWrapper(senderPublicKey, entity)
        return self._prepare(entity)

    def prepareMosaicCreation(self, senderPublicKey, multisigPublicKey, mosaicFqn, description, props):
        actualSender = multisigPublicKey or senderPublicKey
        entity = self._constructMosaic(actualSender, mosaicFqn, description, props)
        if multisigPublicKey:
            entity = self._multisigWrapper(senderPublicKey, entity)
        return self._prepare(entity)

    def prepareMosaicSupply(self, senderPublicKey, multisigPublicKey, mosaicFqn, supplyType, quantity):
        actualSender = multisigPublicKey or senderPublicKey
        entity = self._constructMosaicSupply(actualSender, mosaicFqn, supplyType, quantity)
        if multisigPublicKey:
            entity = self._multisigWrapper(senderPublicKey, entity)
        return self._prepare(entity)

    def multisigCreatePrepare(self, senderPublicKey, cosignatories):
        timeStamp = self.getTimeStamp()
        data = NemConnect.createData(0x1001, senderPublicKey, timeStamp)
        custom = {
            'fee': 2 * (5000000 + 3000000 * (len(cosignatories))),
            'modifications': [
                {'modificationType': 1, 'cosignatoryAccount': publicKey}
                for publicKey in cosignatories
                ]
        }
        entity = dict(data.items() + custom.items())
        r = self.sendPost('transaction/prepare', entity)
        return r.ok, r.json()

    def multisigModificationPrepare(self, senderPublicKey, multisig, cosignatories):
        timeStamp = self.getTimeStamp()
        data = NemConnect.createData(0x1004, senderPublicKey, timeStamp)
        transfer = self.constructModification(multisig, cosignatories)
        custom = {
            'fee': 6000000 * (len(cosignatories) + 1),
            'otherTrans': transfer
        }
        entity = dict(data.items() + custom.items())
        r = self.sendPost('transaction/prepare', entity)
        return r.ok, r.json()

    def multisigSignaturePrepare(self, senderPublicKey, multisigAddress, txHash):
        timeStamp = self.getTimeStamp()
        data = NemConnect.createData(0x1002, senderPublicKey, timeStamp)
        custom = {
            'fee': 2 * 3000000,
            'otherHash': {'data': txHash},
            'otherAccount': multisigAddress
        }
        entity = dict(data.items() + custom.items())
        r = self.sendPost('transaction/prepare', entity)
        return r.ok, r.json()

    def transferAnnounce(self, transferData, transferSignature):
        data = {'data': transferData,
                'signature': transferSignature
                }
        r = self.sendPost('transaction/announce', data)
        return r.ok, r.json()

    def sendGet(self, callName, data):
        headers = {'Content-type': 'application/json'}
        uri = 'http://' + self.address + ':' + str(self.port) + '/' + callName
        return requests.get(uri, params=data, headers=headers, timeout=10)

    def sendPost(self, callName, data):
        headers = {'Content-type': 'application/json'}
        uri = 'http://' + self.address + ':' + str(self.port) + '/' + callName
        return requests.post(uri, data=json.dumps(data), headers=headers, timeout=10)
