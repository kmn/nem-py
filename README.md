Nickel tools
============

Tools provided in this package should be considered **TEST ONLY**.

They might produce incorrect results, NEM development team does NOT take ANY responsibility for any damages.

Keep in mind ed25519 implementation used is sample only and must NOT be used in security-related applications.


nickel example usage (node must be BOOTED to execute any nickel commands):

```
# node info
nickel.py info

#start harvesting
nickel.py harvest --unlock PRIVKEY

#send 123 NEMs to gimre
nickel.py send PRIVKEY TDGIMREMR5NSRFUOMPI5OOHLDATCABNPC5ID2SVA 123000000
```
