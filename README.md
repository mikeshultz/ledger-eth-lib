# ledger-eth-lib

**This is a WIP.  Consider it alpha**

This is a library to interact with [ledger-app-eth](https://github.com/LedgerHQ/ledger-app-eth), the
Ethereum app for the [Ledger hardware wallets](https://www.ledger.com/).  It's goal is to make
interfacing with the Ledger nice and simple with well known Ethereum+Python tools.

## Web3.py Integration

ledger-eth-lib provides a Web3.py middleware.  It will automatically intercept the relevant JSON-RPC
calls and respond with data from your Ledger device.

    from web3.auto import w3
    from ledgereth.web3 import LedgerSignerMiddleware
    w3.middleware_onion.add(LedgerSignerMiddleware)

### Intercepted JSON-RPC methods:

- `eth_sendTransaction`
- `eth_accounts`

## Quickstart

### Get Accounts

Fetch the availible accounts (currently only default).

    from ledgereth import get_accounts
    accounts = get_accounts()
    my_account = accounts[0]

### Create and Sign a Transaction

Create a transaction object and sign it.

    from ledgereth import create_transaction
    tx = create_transaction(
        '0xb78f53524ae9d465279e7c3495f71d5db2419e13',  # to
        '0x4dae53ee778a324bd317bd270d6227406b6bd4ec',  # from
        int(1e18),  # value
        int(1e5),  # gas limit
        int(1e9),  # gas price
        1  # nonce
    )
    # TODO: Double check this
    signature = '0x{}{}{}'.format(
        hex(tx.v)[2:],
        hex(tx.r)[2:],
        hex(tx.s)[2:],
    )

### Sign an Existing Transaction Object

Sign a `Transaction` object from pyethereum(or similar RLP serializable):

    from ledgereth import sign_transaction
    tx = sign_transaction(tx)
    # TODO: Double check this
    signature = '0x{}{}{}'.format(
        hex(tx.v)[2:],
        hex(tx.r)[2:],
        hex(tx.s)[2:],
    )

## API

### `get_accounts(dongle: Any = None)`

Fetch a `List` of accounts.

**NOTE**: This will currently only return the default/primary account from the device.

### `sign_transaction(tx: Serializable, dongle: Any = None)`

Sign a `rlp.Serializable` transaction.

### `create_transaction(to: bytes, sender: bytes, value: int, gas: int, gas_price: int, nonce: int, data: bytes, dongle: Any = None)`

Create and sign an `rlp.Serializable` transaction from provided params

## TODO

- Add fake dongle support to pytest suite so tests can be run without a real Ledger and human interaction
- Fill out tests
- Add messaging signing support
- Add support for multiple accounts(different derivations?)
