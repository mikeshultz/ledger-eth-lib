# ledger-eth-lib

**This is a WIP.  Consider it alpha**

This is a library to interact with [ledger-app-eth](https://github.com/LedgerHQ/ledger-app-eth), the
Ethereum app for the [Ledger hardware wallets](https://www.ledger.com/).  It's goal is to make
interfacing with the Ledger nice and simple with well known Ethereum+Python tools.

**NOTE**: Tested to work on Ledger Nano S and Nano X.  Will probalby work with Ledger Blue

**WARNING**: The Ledger apps have changed the way accounts are derived with the release of Ledger
Live.  If you created your Ledger account(s) with the older Chrome app and want to use those
account(s) with this library, you will need to set the `LEDGER_LEGACY_ACCOUNTS` env var. You can
only use one or the other at a time.  See [the notes in source for more
information](https://github.com/mikeshultz/ledger-eth-lib/blob/master/ledgereth/web3.py#L8-L34).

## Environment Configuration

There are a couple of environment variables that can affect the behavior of ledger-eth-lib,
documented below:

- `MAX_ACCOUNTS_FETCH`[default: `5`]: The maximum accounts that will be fetched when looking up by
address. If you created more than 5 accounts on your Ledger device, you may want to adjust this.
- `LEDGER_LEGACY_ACCOUNTS`: If set (to anything), ledger-eth-lib will use the legacy Ledger bip32
derivation that was used to create accounts **before Ledger Live**.

## CLI Usage

    python -m ledgereth [command]

### Get Accounts

To get the available accounts from your Ledger:

    python -m ledgereth accounts

### Create and Sign Transaction

You can use the CLI util to create and sign a transaction as well.

    python -m ledgereth send FROM_ADDRESS TO_ADDRESS VALUE_WEI -n NONCE -p GAS_PRICE_WEI -c CHAIN_ID

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

Fetch the availible accounts.

    from ledgereth import get_accounts
    accounts = get_accounts()
    my_account = accounts[0].address

### Create and Sign a Transaction

Create a transaction object and sign it with the default account.

    from ledgereth import create_transaction
    tx = create_transaction(
        '0xb78f53524ae9d465279e7c3495f71d5db2419e13',  # to
        int(1e18),  # value
        int(1e5),   # gas limit
        1,          # nonce
        int(1e9),   # gas price
    )
    signature = '0x{}{}{}'.format(
        hex(tx.v)[2:],
        hex(tx.r)[2:],
        hex(tx.s)[2:],
    )

### Sign an Existing Transaction Object

Sign a `Transaction` object from pyethereum(or similar RLP serializable):

    from ledgereth import sign_transaction
    tx = sign_transaction(tx)
    signature = '0x{}{}{}'.format(
        hex(tx.v)[2:],
        hex(tx.r)[2:],
        hex(tx.s)[2:],
    )

## TODO

- Add fake dongle support to pytest suite so tests can be run without a real Ledger and human interaction
- Fill out tests
- Add messaging signing support
- Add ERC-712 messaging signing support
- Add type 1 transactions (EIP-2930 access list)
