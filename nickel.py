import argparse
import json
import sys
import re
from binascii import hexlify, unhexlify
from NemConnect import NemConnect
from Account import Account

class PrivateKeyAction(argparse.Action):
	def __init__(self, option_strings, dest, nargs=None, **kwargs):
		if nargs is not None:
			raise ValueError("nargs not allowed")
		super(PrivateKeyAction, self).__init__(option_strings, dest, **kwargs)

	def __call__(self, parser, namespace, values, option_string=None):
		if (values is None) or (len(values) != 64) or not re.match(r'[0-9A-Fa-f]{64}', values):
			raise argparse.ArgumentError(self, "privkey must be 64-bytes hex string")
		setattr(namespace, self.dest, values)

parser = argparse.ArgumentParser(description='Nickel tool. To get info on subcommands try: nickel.py send --help')

sub = parser.add_subparsers(help='subcommands', dest='sub')
sub.add_parser('info', help='displys node info')

harvestParser = sub.add_parser('harvest', help='start/stop harvesting')
g = harvestParser.add_mutually_exclusive_group()
g.add_argument('--unlock', metavar='PRIVKEY', action=PrivateKeyAction, help='starts harvesting using given private key')
g.add_argument('--lock', metavar='PRIVKEY', action=PrivateKeyAction, help='STOP harvesting using given private key')

sendParser = sub.add_parser('send', help="send nem")
sendParser.add_argument("key", metavar='PRIVKEY', action=PrivateKeyAction, help="sender's private key")
sendParser.add_argument("to", metavar='ADDRESS', help="recipient's address (i.e. TDGIMREMR5NSRFUOMPI5OOHLDATCABNPC5ID2SVA)")
sendParser.add_argument("amount", metavar="AMOUNT", type=int, help="amount in microNEMs")
#sendParser.add_argument("fee", metavar="FEE", type=int, help="fee in microNEMs")

#harvestingParser = sub.add_parser('harvest', help="remote harvesting")

args = parser.parse_args()
print args

def prettyPrint(j):
	print json.dumps(j, indent=2)

c = NemConnect('127.0.0.1', 7890)

if args.sub == 'info':
	j = c.nodeInfo()
	print " [+] NODE INFO:"
	prettyPrint(j)

elif  args.sub == 'harvest':
	msg = "UNLOCK" if args.unlock else "LOCK"
	privkey = args.unlock or args.lock
	a = Account(privkey)
	print " [+] TRYING TO %s USING ACCOUNT" % msg
	print "private: %s" % a.getHexPrivateKey()
	print " public: %s" % a.getHexPublicKey()
	if args.unlock:
		ok,j = c.accountUnlock(privkey)
	else:
		ok,j = c.accountLock(privkey)

	if ok:
		print " [+] SUCCESSFULLY %sED" % msg
	else:
		prettyPrint(j)

elif args.sub == 'send':
	privkey = args.key
	recipient = args.to
	amount = args.amount
	message = 'nickel test'
	a = Account(privkey)
	print " [+] PREPARING TRANSACTION"
	ok, j = c.transferPrepare(a.getHexPublicKey(), recipient, amount, message)
	if ok and ('data' in j):
		print " [+] TRYING TO SIGN PREPARED DATA"
		data = unhexlify(j['data'])
		sig = a.sign(data)

		ok, j = c.transferAnnounce(j['data'], hexlify(sig))
		if ok:
			print " [+] ANNOUNCED"
		else:
			print " [!] announce failed"
		prettyPrint(j)
	else:
		print " [!] prepare failed: "
		prettyPrint(j)

