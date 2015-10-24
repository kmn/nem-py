NEM-py
======

NEM-py is collection of useful python scripts, that may be used
to create and send transactions in nem network.

As of now, the tools require trusted/local NIS server, but it might change if
binary serialization will be added to the tools.

Most important elements are:
 * Account.py - that wraps (private, public, address) triplet, and that is able to sign binary data
 * NemConnect.py - connector to nem network, that wraps data needed to send to nis server in a more convenient api
 * nickel.py - command line testing tool using the two above

nickel
------

Tools provided in this package should be considered **TEST ONLY**.

We've spared no effort to make nickel compatible with NEM software, nevertheles
nickel might produce incorrect results, NEM development team does NOT take ANY responsibility for any damages.

That being said, nickel passes all the tests from nem-test-vectors (https://github.com/NewEconomyMovement/nem-test-vectors),
see nem\_test\_vectors.py for details.

Keep in mind ed25519 implementation used is sample only and must NOT be used in security-related applications.


nickel example usage (node must be BOOTED to execute any nickel commands):

```
# node info
nickel.py info

# start harvesting
nickel.py harvest --unlock PRIVKEY

# send 123 NEMs to gimre
# (private key, recipient address, amount)
nickel.py transfer 3029c55412442244defb01deef360db9b6ddf4779479e1436e67028dc44ca5f7 \
  TDGIMREMR5NSRFUOMPI5OOHLDATCABNPC5ID2SVA 123000000

# associate delegated harvesting account
# (private key, delegated harvesting account public key)
nickel.py remote 3029c55412442244defb01deef360db9b6ddf4779479e1436e67028dc44ca5f7 \
  629c2364f119c7d1e07ba4461938b23dabc65726d60b57a09c67d3c8609ad599

# create multisig account
# (multisig priv key, cosigners public keys....)
nickel.py multisig-create e8da26bf835b3caca4712b8ca7cf893dce6e1cd1e00fe8601a392fea043f69df \
  --add d034e5ce0a58c0dbf6c2e4d353e08c6b41e35fc5f60d65983969210d66a3620c \
        42b5284ee010c94670abfe90f7defcdb8b79e28dc358a2bfea6d0d13d6510548

# create multisig transfer
# (--multisig multisig public key, cosigner priv key, recipient address, amount)
nickel.py transfer --multisig 2bc0a27779d30862e0ec54de2951a6506ca913165a1bc28f3ce51c7fecfe443f \
  3029c55412442244defb01deef360db9b6ddf4779479e1436e67028dc44ca5f7 \
  TDPATMAMYAICKQ7SPFFE3TRTHYW2XF773VTTHYUI 1234

# co-sign multisig transaction
# (cosigners priv key, inner transaction hash)
nickel.py multisig-signature 823541e7e0a9e61387bcc66dabf3e0b9257ca168437a01907f82c6012ecc896f \
  7aa836f43db9a0ef29e6ee4e49642522c49a0b702a982cea6b9918ec6c570c95
```


```
# testing vectors
nem_test_vectors.py --test-sha3-256-file ..\nem-test-vectors\0.test-sha3-256.dat
test: 1984
2000 PASSED

nem_test_vectors.py --test-keys-file ..\nem-test-vectors\1.test-keys.dat
test: 9982
10000 PASSED

nem_test_vectors.py --test-sign-file ..\nem-test-vectors\2.test-sign.dat
test: 9982
10000 PASSED
```


mosaics
=======

```
# create namespace fizz
nickel.py namespace <PRIVATE-KEY> fizz

# create sub-namespace buzz inside fizz
nickel.py namespace <PRIVATE-KEY> fizz.buzz

# create mosaic Fizzier inside owned namespace with description
# created mosaic has following 'default' properties:
#   {'divisibility':2, 'initialSupply':1000000, 'supplyMutable':True, 'transferable':True}
nickel.py mosaic <PRIVATE-KEY> fizz.buzz.Fizzier "Fizzier is very advanced fizz buzz implementation"

# add or remove some mosaics:
nickel.py mosaic-supply --create <PRIVATE-KEY> fizz.buzz.Fizzier 1000
nickel.py mosaic-supply --destroy <PRIVATE-KEY> fizz.buzz.Fizzier 2000

# transfer mosaics
nickel.py transfer --mosaic fizz.buzz.Fizzier:1000:100 <PRIVATE-KEY> TBLOODPLWOWMZ2TARX4RFPOSOWLULHXMROBN2WXI 1000000

# this requires some explanation, this will send 10 mosaics (cause divisibility == 2), to bloody rookie,
# the third argument is additional transfer fee, unfortunatelly nickel right now is unable to calculate
# that fee, so if too small fee will be passed, error will be returned, i.e
#

nickel.py transfer --mosaic games.pong.Paddles:1000:50 <PRIV KEY> TBLOODPLWOWMZ2TARX4RFPOSOWLULHXMROBN2WXI 1000000
 [+] PREPARING TRANSACTION
Attached mosaic: [{'quantity': 1000, 'mosaicId': {'namespaceId': 'games.pong', 'name': 'Paddles'}}]
 [!] prepare failed:
{
  "status": 400,
  "timeStamp": 11964270,
  "message": "FAILURE_INSUFFICIENT_FEE",
  "error": "Bad Request"
}

# last argument in transfer is amount, and it specifies how many "parts" should be send, (it must be multiple of 1 XEM == 1000000 uXem)

```
