from NemConnect import NemConnect
from Account import Account

from binascii import hexlify, unhexlify
import json
from math import atan
from Tkinter import *
import ttk
import tkFont
from ConfigParser import SafeConfigParser
import traceback


class NickelUi:
    def __init__(self, root, conf):
        self.root = root
        self.conf = conf

        self.main = ttk.Panedwindow(root, orient=VERTICAL)
        f1 = ttk.Labelframe(self.main, text='Common')
        f2 = ttk.Labelframe(self.main, text='Specific')
        f3 = ttk.Labelframe(self.main, text='Results')
        self.main.add(f1)
        self.main.add(f2)
        self.main.add(f3)
        self.main.grid()

        Label(f1, text="Host:") \
            .grid(row=0, column=1, padx=2, pady=2)
        self.host = Entry(f1, width=20)
        self.host.grid(row=0, column=2, padx=2, pady=2)
        self.host.insert(0, self.conf.get('server', 'host'))

        Label(f1, text="Port:") \
            .grid(row=0, column=3, padx=2, pady=2)
        self.port = Entry(f1, width=6)
        self.port.grid(row=0, column=4, padx=2, pady=2)
        self.port.insert(0, self.conf.get('server', 'port'))

        # row1
        Label(f1, text="Signer's private key") \
            .grid(row=1, column=0, columnspan=1, padx=2, pady=2)
        self.privKeyEntry = Entry(f1, width=64)
        self.privKeyEntry.grid(row=1, column=1, columnspan=4, padx=2, pady=2)
        self.privKeyEntry.insert(0, self.conf.get('common', 'privkey'))

        # row2
        self.multisigEnabled = IntVar()
        temp = Checkbutton(f1, text='Multisig transaction', variable=self.multisigEnabled, command=self.toggleMultisigPubKeyEntry)
        temp.grid(row=2, column=0, columnspan=5, padx=2, pady=2, sticky=W)

        # row3
        Label(f1, text="Multisig public key") \
            .grid(row=3, column=0, columnspan=1, padx=2, pady=2)
        self.multisigPubKeyEntry = Entry(f1, width=64)
        self.multisigPubKeyEntry.grid(row=3, column=1, columnspan=4, padx=2, pady=2)
        self.multisigPubKeyEntry.insert(0, self.conf.get('common', 'multisig'))
        self.multisigPubKeyEntry.configure(state='disabled')

        self.namespaceTab()
        self.mosaicTab()
        self.mosaicSupplyTab()
        self.transferTab()

        # add tabs
        self.n = ttk.Notebook(f2)
        self.n.add(self.ns, text="namespace")
        self.n.add(self.mc, text="mosaic create")
        self.n.add(self.ms, text="mosaic supply")
        self.n.add(self.tr, text="transfer")
        self.n.select(self.tr)
        self.n.grid(row=1)

        self.result = Text(f3, width=120, height=15)
        self.result.grid(row=2)

        boldFont = tkFont.Font(self.result, self.result.cget("font"))
        boldFont.configure(weight="bold")
        self.result.tag_configure("bt", font=boldFont)

    def focus_window(self, event, direction):
        if direction == 1:
            event.widget.tk_focusNext().focus()
        else:
            event.widget.tk_focusPrev().focus()
        return ("break")

    def toggleMultisigPubKeyEntry(self):
        if self.multisigEnabled.get():
            self.multisigPubKeyEntry.configure(state='normal')
        else:
            self.multisigPubKeyEntry.configure(state='disabled')

    def report(self, reason, a):
        self.result.configure(state=NORMAL)
        self.result.delete("1.0", END)
        for line in iter(reason.splitlines()):
            self.result.insert(INSERT, line + "\n")
        self.result.insert(INSERT, "\n")
        for line in iter(a.splitlines()):
            self.result.insert(INSERT, line + "\n")
        self.result.tag_add('bt', "1.0", "1." + str(len(reason)))
        self.result.configure(state=DISABLED)

    def commonHandle(self, connector, account, ok, j):
        if not ok:
            self.report("ERROR", json.dumps(j, indent=2))
            return

        data = unhexlify(j['data'])
        sig = account.sign(data)

        ok, j = connector.transferAnnounce(j['data'], hexlify(sig))
        if ok:
            self.report("ANNOUNCED", json.dumps(j, indent=2))
        else:
            self.report("ERROR: announce failed", json.dumps(j, indent=2))

    # first tab
    def namespaceTab(self):
        self.ns = Frame(self.root, width=800, height=400)
        self.ns.grid(row=0)

        Label(self.ns, text="Namespace name") \
            .grid(row=0, column=0, padx=2, pady=2)
        self.namespaceNameEntry = Entry(self.ns, width=64 * 2 + 16 + 2)
        self.namespaceNameEntry.grid(row=0, column=1, padx=2, pady=2)
        Button(self.ns, text="Send 'Provision Namespace'", command=self.namespaceClick) \
            .grid(row=1, column=1, sticky=W)

    def namespaceClick(self):
        c = NemConnect(self.host.get(), int(self.port.get()))

        privkey = self.privKeyEntry.get()
        fqn = self.namespaceNameEntry.get()
        multisig = self.multisigPubKeyEntry.get() if self.multisigEnabled.get() else None
        try:
            a = Account(privkey)
            ok, j = c.prepareProvisionNamespace(a.getHexPublicKey(), multisig, fqn)
            self.commonHandle(c, a, ok, j)

        except Exception as e:
            self.report(str(e), traceback.format_exc())

    # second tab
    def mosaicTab(self):
        self.mc = Frame(self.root, width=800, height=400)
        self.mc.grid(row=0)

        Label(self.mc, text="Namespace + mosaic name:") \
            .grid(row=0, column=0, padx=2, pady=2, sticky=W)
        self.create_namespaceNameEntry = Entry(self.mc)
        self.create_namespaceNameEntry.grid(row=0, column=1, padx=2, pady=2, sticky=W+E)
        self.create_mosaicNameEntry = Entry(self.mc, width=32)
        self.create_mosaicNameEntry.grid(row=0, column=2, padx=2, pady=2, sticky=W)

        Label(self.mc, text="Mosaic description:") \
            .grid(row=1, column=0, padx=2, pady=2, sticky=W)
        self.mosaicDescText = Text(self.mc, width=80, height=3)
        self.mosaicDescText.grid(row=1, column=1, columnspan=2, padx=2, pady=2, sticky=W)
        self.mosaicDescText.insert(INSERT, self.conf.get('mosaic', 'mosaic_text'))
        self.mosaicDescText.bind("<Tab>", lambda x: self.focus_window(x, 1))
        self.mosaicDescText.bind("<Shift-Tab>", lambda x: self.focus_window(x, -1))

        f1 = ttk.Labelframe(self.mc, text='Mosaic Properties')
        f1.grid(row=3, column=1, columnspan=2, sticky=W)
        if 1:
            Label(f1, text="Initial supply:") \
                .grid(row=0, column=0, padx=2, pady=2, sticky=W)
            self.m_is = Entry(f1, width=40)
            self.m_is.grid(row=0, column=1, padx=2, pady=2)
            self.m_is.insert(0, self.conf.get('mosaic', 'mosaic_initial_supply'))

            Label(f1, text="Divisibility:") \
                .grid(row=1, column=0, padx=2, pady=2, sticky=W)
            self.m_d = Entry(f1, width=40)
            self.m_d.grid(row=1, column=1, padx=2, pady=2)
            self.m_d.insert(0, self.conf.get('mosaic', 'mosaic_divisibility'))

            self.m_ms = BooleanVar()
            self.m_ms.set(self.conf.getboolean('mosaic', 'mosaic_mutable_supply'))
            Checkbutton(f1, variable=self.m_ms, text="Mutable supply") \
                .grid(row=2, column=1, padx=2, pady=2, sticky=W)

            self.m_t = BooleanVar()
            self.m_t.set(self.conf.getboolean('mosaic', 'mosaic_transferable'))
            Checkbutton(f1, variable=self.m_t, text="Transferable:") \
                .grid(row=3, column=1, padx=2, pady=2, sticky=W)

        self.m_hasLevy = BooleanVar()
        self.m_hasLevy.set(self.conf.getboolean('mosaic', 'mosaic_hasLevy'))
        Checkbutton(self.mc, variable=self.m_hasLevy, text="Has levy", command=self.toggleMosaicLevyClick) \
            .grid(row=4, column=1, columnspan=2, padx=2, pady=2, sticky=W)

        f2 = ttk.Labelframe(self.mc, text='Levy settings')
        f2.grid(row=5, column=1, columnspan=2, sticky=W)
        if 1:
            self.m_levy_type = IntVar()
            self.m_levy_type.set(1)
            Radiobutton(f2, text="Absolute", variable=self.m_levy_type, value=1) \
                .grid(row=0, column=1, padx=2, pady=2, sticky=W)
            Radiobutton(f2, text="Percentile", variable=self.m_levy_type, value=2) \
                .grid(row=0, column=2, padx=2, pady=2, sticky=W)

            Label(f2, text="Levy Recipient's address:") \
                .grid(row=1, column=0, padx=2, pady=2, sticky=W)
            self.m_levy_recipient = Entry(f2, width=64)
            self.m_levy_recipient.grid(row=1, column=1, columnspan=2, padx=2, pady=2, sticky=W)
            self.m_levy_recipient.insert(0, self.conf.get('mosaic', 'mosaic_levy_recipient'))

            Label(f2, text="Mosaic Levy full name:") \
                .grid(row=2, column=0, padx=2, pady=2, sticky=W)
            self.m_levy_namespace = Entry(f2)
            self.m_levy_namespace.grid(row=2, column=1, columnspan=1, padx=2, pady=2, sticky=W+E)
            self.m_levy_namespace.insert(0, self.conf.get('mosaic', 'mosaic_levy_ns'))

            self.m_levy_mosaic = Entry(f2, width=16)
            self.m_levy_mosaic.grid(row=2, column=2, columnspan=1, padx=2, pady=2, sticky=W)
            self.m_levy_mosaic.insert(0, self.conf.get('mosaic', 'mosaic_levy_mosaic'))

            Label(f2, text="Mosaic Levy fee:") \
                .grid(row=3, column=0, padx=2, pady=2, sticky=W)

            self.m_levy_fee = Entry(f2, width=10)
            self.m_levy_fee.grid(row=3, column=1, columnspan=2, padx=2, pady=2, sticky=W)
            self.m_levy_fee.insert(0, self.conf.get('mosaic', 'mosaic_levy_fee'))

        self.m_levy_settings = f2
        self.toggleMosaicLevyClick()

        Button(self.mc, text="Send 'Create Mosaic'", command=self.mosaicClick) \
            .grid(row=6, column=1, sticky=W)

    def mosaicClick(self):
        c = NemConnect(self.host.get(), int(self.port.get()))

        privkey = self.privKeyEntry.get()
        fqn = self.create_namespaceNameEntry.get() + '.' + self.create_mosaicNameEntry.get()
        desc = self.mosaicDescText.get("1.0", END)
        defaultProps = {
            'divisibility': int(self.m_d.get()),
            'initialSupply': int(self.m_is.get()),
            'supplyMutable': True if self.m_ms.get() else False,
            'transferable': True if self.m_t.get() else False
        }
        multisig = self.multisigPubKeyEntry.get() if self.multisigEnabled.get() else None

        if self.m_hasLevy.get():
            defaultProps['levy'] = {
                "type": int(self.m_levy_type.get()),
                "recipient": self.m_levy_recipient.get(),
                "mosaicFqn": self.m_levy_namespace.get() + '.' + self.m_levy_mosaic.get(),
                "fee": int(self.m_levy_fee.get())
            }
        try:
            a = Account(privkey)
            ok, j = c.prepareMosaicCreation(a.getHexPublicKey(), multisig, fqn, desc, defaultProps)
            self.commonHandle(c, a, ok, j)

        except Exception as e:
            self.report(str(e), traceback.format_exc())

    def toggleMosaicLevyClick(self):
        f2 = self.m_levy_settings
        if self.m_hasLevy.get():
            for child in f2.winfo_children():
                child.configure(state='normal')
        else:
            for child in f2.winfo_children():
                child.configure(state='disabled')

    def mosaicSupplyTab(self):
        self.ms = Frame(self.root, width=800, height=400)
        self.ms.grid(row=0)

        Label(self.ms, text="Namespace + mosaic name") \
            .grid(row=0, column=0, padx=2, pady=2, sticky=W)
        self.mosaicSupply_namespace = Entry(self.ms)
        self.mosaicSupply_namespace.grid(row=0, column=1, padx=2, pady=2, sticky=W+E)
        self.mosaicSupply_namespace.insert(0, self.conf.get('supply', 'supply_ns'))

        self.mosaicSupply_mosaic = Entry(self.ms, width=16)
        self.mosaicSupply_mosaic.grid(row=0, column=2, padx=2, pady=2, sticky=W)
        self.mosaicSupply_mosaic.insert(0, self.conf.get('supply', 'supply_mosaic'))

        Label(self.ms, text="Supply Change") \
            .grid(row=1, column=0, padx=2, pady=2, sticky=W)
        self.ms_supplyChange = Entry(self.ms, width=40)
        self.ms_supplyChange.grid(row=1, column=1, padx=2, pady=2, sticky=W)
        self.ms_supplyChange.insert(0, "0")

        self.ms_mode = IntVar()
        self.ms_mode.set(1)
        Radiobutton(self.ms, text="Create", variable=self.ms_mode, value=1) \
            .grid(row=2, column=1, padx=2, pady=2, sticky=W)
        Radiobutton(self.ms, text="Destroy", variable=self.ms_mode, value=2) \
            .grid(row=3, column=1, padx=2, pady=2, sticky=W)

        Button(self.ms, text="Send 'Mosaic Supply'", command=self.mosaicSupplyClick) \
            .grid(row=4, column=1, sticky=W)

    def mosaicSupplyClick(self):
        c = NemConnect(self.host.get(), int(self.port.get()))

        privkey = self.privKeyEntry.get()
        fqn = self.mosaicSupply_namespace.get() + '.' + self.mosaicSupply_mosaic.get()
        supplyDelta = int(self.ms_supplyChange.get())
        supplyMode = self.ms_mode.get()

        multisig = self.multisigPubKeyEntry.get() if self.multisigEnabled.get() else None
        try:
            a = Account(privkey)
            ok, j = c.prepareMosaicSupply(a.getHexPublicKey(), multisig, fqn, supplyMode, supplyDelta)
            self.commonHandle(c, a, ok, j)
        except Exception as e:
            self.report(str(e), traceback.format_exc())

    def transferTab(self):
        # third tab
        self.tr = Frame(self.root, width=800, height=400)
        self.tr.grid(row=0)

        Label(self.tr, text="Recipient's address") \
            .grid(row=0, column=0, padx=2, pady=2, sticky=W)
        self.transferRecipient = Entry(self.tr, width=64)
        self.transferRecipient.grid(row=0, column=1, columnspan=3, padx=2, pady=2, sticky=W)
        self.transferRecipient.insert(0, self.conf.get('transfer', 'recipient'))

        Label(self.tr, text="Message") \
            .grid(row=1, column=0, padx=2, pady=2, sticky=W)
        self.transferMessage = Text(self.tr, width=80, height=2)
        self.transferMessage.grid(row=1, column=1, columnspan=3, padx=2, pady=2, sticky=W)
        self.transferMessage.insert(INSERT, self.conf.get('transfer', 'message'))

        self.attachments = []
        Button(self.tr, text="Add Attachment (Mosaic)", command=self.transferAddAttachment) \
            .grid(row=2, column=1, columnspan=3, sticky=W)

        self.labelAmount = StringVar()
        Label(self.tr, textvariable=self.labelAmount) \
            .grid(row=101, column=0, padx=2, pady=2, sticky=W)
        self.labelAmount.set("Amount")

        self.transferAmount = Entry(self.tr, width=10)
        self.transferAmount.grid(row=101, column=1, columnspan=3, padx=2, pady=2, sticky=W)
        self.transferAmount.insert(INSERT, self.conf.get('transfer', 'amount'))

        # loop requires self.transferAmount, as it's modified in transferAddAttachment
        for i in xrange(self.conf.getint('transfer', 'attached_mosaics')):
            self.transferAddAttachment()
            self.attachments[-1]['t'].insert(0, self.conf.get('transfer', 'mosaic_' + str(i) + '_ns'))
            self.attachments[-1]['m'].insert(0, self.conf.get('transfer', 'mosaic_' + str(i) + '_mosaic'))
            self.attachments[-1]['q'].insert(0, self.conf.get('transfer', 'mosaic_' + str(i) + '_amount'))

        Button(self.tr, text="Send Transfer Transaction", command=self.transferClick) \
            .grid(row=102, column=2, sticky=W)

    def transferAddAttachment(self):
        rowNo = 2 * len(self.attachments) + 3
        Label(self.tr, text="Namespace + mosaic name") \
            .grid(row=rowNo, column=0, padx=2, pady=2, sticky=W)

        t = Entry(self.tr)
        t.grid(row=rowNo, column=1, columnspan=2, padx=2, pady=2, sticky=W+E)
        
        m = Entry(self.tr, width=16)
        m.grid(row=rowNo, column=3, columnspan=1, padx=2, pady=2, sticky=W)

        Label(self.tr, text="quantity") \
            .grid(row=rowNo + 1, column=0, padx=2, pady=2, sticky=W)

        q = Entry(self.tr, width=10)
        q.grid(row=rowNo + 1, column=1, columnspan=3, padx=2, pady=2, sticky=W)

        self.attachments.append({'t': t, 'm':m, 'q': q})

        if len(self.attachments) == 1:
            self.labelAmount.set('Multiplier')
            self.transferAmount.configure(width=2)
            self.transferAmount.delete(0, 'end')
            self.transferAmount.insert(0, self.conf.get('transfer', 'multiplier'))

    def transferClick(self):
        try:
            c = NemConnect(self.host.get(), int(self.port.get()))

            privkey = self.privKeyEntry.get()
            multisig = self.multisigPubKeyEntry.get() if self.multisigEnabled.get() else None
            recipient = self.transferRecipient.get()
            amount = int(self.transferAmount.get())
            message = self.transferMessage.get("1.0", END)
            mosaics = map(lambda x: (x['t'].get() + '.' + x['m'].get(), int(x['q'].get())), self.attachments)

            if len(self.attachments) > 0:
                amount *= 1000000

            a = Account(privkey)
            ok, j = c.prepareTransfer(a.getHexPublicKey(), multisig, recipient, amount, message, mosaics)
            self.commonHandle(c, a, ok, j)

        except Exception as e:
            self.report(str(e), traceback.format_exc())


def readConfig():
    cp = SafeConfigParser({
        'privkey': '',
        'multisig': '',
        'host': '',
        'port': '',
        'mosaic_text': '',
        'mosaic_initial_supply': '100',
        'mosaic_divisibility': '2',
        'mosaic_mutable_supply': '0',
        'mosaic_transferable': '0',
        'recipient': '',
        'message': '',
        'amount': '0',
        'multiplier': '1'
    })
    cp.read('config.ini')
    return cp


def basicUiLoop():
    conf = readConfig()
    root = Tk()
    root.iconbitmap('icon.ico')
    root.wm_title("Nickel - testnet tool")
    nickelUi = NickelUi(root, conf)
    root.mainloop()
