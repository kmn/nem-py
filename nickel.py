from NemConnect import NemConnect
from Account import Account
import BasicUi

import argparse
import json
import sys
import re
from binascii import hexlify, unhexlify


class PrivateKeyAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super(PrivateKeyAction, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if not (values is None) and (len(values) == 66) and re.match(r'00[0-9A-Fa-f]{64}', values):
            raise argparse.ArgumentError(self, "nickel requires priv key without initial 00 byte")
        if (values is None) or (len(values) != 64) or not re.match(r'[0-9A-Fa-f]{64}', values):
            raise argparse.ArgumentError(self, "privkey must be 64-bytes hex string")
        setattr(namespace, self.dest, values)


parser = argparse.ArgumentParser(description='Nickel tool. To get info on subcommands try: nickel.py transfer --help')

sub = parser.add_subparsers(help='subcommands', dest='sub')
sub.add_parser('info', help='displys node info')

harvestParser = sub.add_parser('harvest', help='start/stop harvesting')
g = harvestParser.add_mutually_exclusive_group()
g.add_argument('--unlock', metavar='PRIVKEY', action=PrivateKeyAction, help='starts harvesting using given private key')
g.add_argument('--lock', metavar='PRIVKEY', action=PrivateKeyAction, help='STOP harvesting using given private key')

transferParser = sub.add_parser('transfer', help="send nem")
transferParser.add_argument("--multisig", metavar='PUBLICKEY', help="multisig sender PUBLIC key")
transferParser.add_argument("key", metavar='PRIVKEY', action=PrivateKeyAction, help="sender's private key")
transferParser.add_argument("to", metavar='ADDRESS', help="recipient's address (i.e. TDGIMREMR5NSRFUOMPI5OOHLDATCABNPC5ID2SVA)")
transferParser.add_argument("amount", metavar="AMOUNT", type=int, help="amount in microNEMs")
transferParser.add_argument("--mosaic", metavar='mosaic', nargs='*', help="attach mosaic (mosaicName:amount)")
# transferParser.add_argument("fee", metavar="FEE", type=int, help="fee in microNEMs")

remoteParser = sub.add_parser('remote', help="remote harvesting")
g = remoteParser.add_mutually_exclusive_group()
g.add_argument('--assign', action='store_true', help='associates account with remote harvesting account')
g.add_argument('--cancel', action='store_true', help='cancel association between account and remote harvesting account')
remoteParser.add_argument("--multisig", metavar='PUBLICKEY', help="multisig sender PUBLIC key")
remoteParser.add_argument("key", metavar='PRIVKEY', action=PrivateKeyAction, help="sender's private key")
remoteParser.add_argument("remote", metavar='ADDRESS', help="remote harvesting address")

provisionParser = sub.add_parser('namespace', help="namespace provision")
provisionParser.add_argument("--multisig", metavar='PUBLICKEY', help="multisig sender PUBLIC key")
provisionParser.add_argument("key", metavar='PRIVKEY', action=PrivateKeyAction, help="sender's private key")
provisionParser.add_argument("fqn", metavar='NAMESPACE', help="fully qualified namespace name")

mosaicParser = sub.add_parser('mosaic', help="mosaic creation")
mosaicParser.add_argument("--multisig", metavar='PUBLICKEY', help="multisig sender PUBLIC key")
mosaicParser.add_argument("key", metavar='PRIVKEY', action=PrivateKeyAction, help="sender's private key")
mosaicParser.add_argument("fqn", metavar='MOSAIC', help="fully qualified mosaic name")
mosaicParser.add_argument("desc", metavar='TEXT', help="mosaic description")

mosaicSupplyParser = sub.add_parser('mosaic-supply', help="mosaic supply operations")
g = mosaicSupplyParser.add_mutually_exclusive_group()
g.add_argument('--create', action='store_true', help='issues creation of a supply of a mosaic')
g.add_argument('--destroy', action='store_true', help='destroys a supply of a mosaic')
mosaicSupplyParser.add_argument("--multisig", metavar='PUBLICKEY', help="multisig sender PUBLIC key")
mosaicSupplyParser.add_argument("key", metavar='PRIVKEY', action=PrivateKeyAction, help="sender's private key")
mosaicSupplyParser.add_argument("fqn", metavar='MOSAIC', help="fully qualified mosaic name")
mosaicSupplyParser.add_argument("supplyDelta", metavar='AMOUNT', help="supply amount")

multisigCreateParser = sub.add_parser('multisig-create', help='multisig create')
multisigCreateParser.add_argument('key', metavar='PRIVKEY', action=PrivateKeyAction, help="sender's private key")
multisigCreateParser.add_argument('--add', metavar='PUBLICKEY', nargs='+', help='public keys of coisgnatories to add')

multisigSignatureParser = sub.add_parser('multisig-signature', help='multisig signature')
multisigSignatureParser.add_argument("key", metavar='PRIVKEY', action=PrivateKeyAction, help="cosigners's private key")
multisigSignatureParser.add_argument("multisig", metavar='ADDRESS', help="multisig account's address (not public-key)")
multisigSignatureParser.add_argument("hash", metavar='HASH', help="cosigned transaction hash")

multisigModificationParser = sub.add_parser('multisig-modification', help='multisig modification')
multisigModificationParser.add_argument("key", metavar='PRIVKEY', action=PrivateKeyAction, help="cosigners's private key")
multisigModificationParser.add_argument("multisig", metavar='PUBLICKEY', help="multisig sender address (i.e. TDGIMREMR5NSRFUOMPI5OOHLDATCABNPC5ID2SVA)")
multisigModificationParser.add_argument('--rem', metavar='PUBLICKEY', nargs='+', help='public keys of coisgnatories to del')

if (len(sys.argv) < 2):
    sys.exit(BasicUi.basicUiLoop())
else:
    args = parser.parse_args()


def prettyPrint(j):
    print json.dumps(j, indent=2)


def signAndAnnounceTransaction(connector, jsonData):
    print " [+] TRYING TO SIGN PREPARED DATA"
    data = unhexlify(jsonData['data'])
    sig = a.sign(data)

    ok, j = connector.transferAnnounce(jsonData['data'], hexlify(sig))
    if ok:
        print " [+] ANNOUNCED"
    else:
        print " [!] announce failed"
    prettyPrint(j)


c = NemConnect('127.0.0.1', 7890)

if args.sub == 'info':
    j = c.nodeInfo()
    print " [+] NODE INFO:"
    prettyPrint(j)
    sys.exit(0)

elif args.sub == 'harvest':
    msg = "UNLOCK" if args.unlock else "LOCK"
    privkey = args.unlock or args.lock
    a = Account(privkey)
    print " [+] TRYING TO %s USING ACCOUNT" % msg
    print "private: %s" % a.getHexPrivateKey()
    print " public: %s" % a.getHexPublicKey()
    if args.unlock:
        ok, j = c.accountUnlock(privkey)
    else:
        ok, j = c.accountLock(privkey)

    if ok:
        print " [+] SUCCESSFULLY %sED" % msg
    else:
        prettyPrint(j)
    sys.exit(0)

elif args.sub == 'transfer':
    privkey = args.key
    recipient = args.to
    amount = args.amount
    message = 'nickel test'

    if args.mosaic:
        mosaics = map(lambda p: (p[0], int(p[1])), map(lambda x: x.split(':'), args.mosaic))
        print mosaics
    else:
        mosaics = None

    a = Account(privkey)
    print " [+] PREPARING TRANSACTION"
    ok, j = c.prepareTransfer(a.getHexPublicKey(), args.multisig, recipient, amount, message, mosaics)

elif args.sub == 'remote':
    privkey = args.key
    remote = args.remote
    a = Account(privkey)
    print " [+] PREPARING IMPORTANCE TRANSFER TRANSACTION"
    ok, j = c.prepareImportanceTransfer(a.getHexPublicKey(), args.multisig, remote, False if args.cancel else True)

elif args.sub == 'multisig-create':
    privkey = args.key
    cosignatories = args.add
    a = Account(privkey)
    print " [+] PREPARING MULTISIG CREATE"
    ok, j = c.multisigCreatePrepare(a.getHexPublicKey(), cosignatories)

elif args.sub == 'multisig-signature':
    privkey = args.key
    multisig = args.multisig
    txHash = args.hash
    a = Account(privkey)
    print " [+] PREPARING MULTISIG SIGNATURE"
    ok, j = c.multisigSignaturePrepare(a.getHexPublicKey(), multisig, txHash)

elif args.sub == 'multisig-modification':
    privkey = args.key
    multisig = args.multisig
    remove = args.rem
    a = Account(privkey)
    print " [+] PREPARING MULTISIG MODIFICATION REMOVAL"
    ok, j = c.multisigModificationPrepare(a.getHexPublicKey(), multisig, remove)

elif args.sub == 'namespace':
    privkey = args.key
    fqn = args.fqn
    a = Account(privkey)
    print " [+] PREPARING PROVISION NAMESPACE TRANSACTION"
    ok, j = c.prepareProvisionNamespace(a.getHexPublicKey(), args.multisig, fqn)

elif args.sub == 'mosaic':
    privkey = args.key
    fqn = args.fqn
    desc = args.desc
    a = Account(privkey)
    print " [+] PREPARING MOSAIC TRANSACTION"
    defaultProps = {'divisibility': 2, 'initialSupply': 1000000, 'supplyMutable': True, 'transferable': True}
    ok, j = c.prepareMosaicCreation(a.getHexPublicKey(), args.multisig, fqn, desc, defaultProps)

elif args.sub == 'mosaic-supply':
    privkey = args.key
    fqn = args.fqn
    supplyDelta = args.supplyDelta
    a = Account(privkey)
    print " [+] PREPARING MOSAIC SUPPLY TRANSACTION"
    ok, j = c.prepareMosaicSupply(a.getHexPublicKey(), args.multisig, fqn, 1 if args.create else 2, supplyDelta)

if ok and ('data' in j):
    signAndAnnounceTransaction(c, j)
else:
    print " [!] prepare failed: "
    prettyPrint(j)
