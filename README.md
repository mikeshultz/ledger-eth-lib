# ledger-eth-lib

**This is a WIP.  Consider it alpha**

This is a library to interact with [ledger-app-eth](https://github.com/LedgerHQ/ledger-app-eth), the Ethereum app for the [Ledger hardware wallets](https://www.ledger.com/).  It's goal is to make interfacing with the Ledger nice and simple with well known Ethereum+Python tools.

**NOTE**: Tested to work on Ledger Nano S and Nano X.  Will probalby work with Ledger Blue

**WARNING**: The Ledger apps have changed the way accounts are derived with the release of Ledger Live.  If you created your Ledger account(s) with the older Chrome app and want to use those account(s) with this library, you will need to set the `LEDGER_LEGACY_ACCOUNTS` env var. You can only use one or the other at a time.  See [the notes in source for more
information](https://github.com/mikeshultz/ledger-eth-lib/blob/master/ledgereth/web3.py#L8-L34).

## Environment Configuration

There are a couple of environment variables that can affect the behavior of ledger-eth-lib,
documented below:

- `MAX_ACCOUNTS_FETCH`[default: `3`]: The maximum accounts that will be fetched when looking up by address. If you created more than 5 accounts on your Ledger device, you may want to adjust this.
- `LEDGER_LEGACY_ACCOUNTS`: If set (to anything), ledger-eth-lib will use the legacy Ledger bip32 derivation that was used to create accounts **before Ledger Live**.

## CLI Usage

    python -m ledgereth [command]

### Get Accounts

To get the available accounts from your Ledger:

    python -m ledgereth accounts

### Create and Sign Transaction

You can use the CLI util to create and sign a transaction as well.

    python -m ledgereth send FROM_ADDRESS TO_ADDRESS VALUE_WEI -n NONCE -p GAS_PRICE_WEI -c CHAIN_ID

### Sign a Message

You can use the CLI util to sign simple messages.

    python -m ledgereth sign SIGNER_ADDRESS "I'm a little teapot"

### Sign Typed Data

You can use the CLI util to sign type data (EIP-712).  You must have the domain hash and message hash ahead of time.

    python -m ledgereth signtyped SIGNER_ADDRESS DOMAIN_HASH MESSAGE_HASH

## Web3.py Integration

ledger-eth-lib provides a Web3.py middleware.  It will automatically intercept the relevant JSON-RPC calls and respond with data from your Ledger device.

    >>> from web3.auto import w3
    >>> from ledgereth.web3 import LedgerSignerMiddleware
    >>> w3.middleware_onion.add(LedgerSignerMiddleware)
    >>> w3.eth.accounts
    ['0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266', '0x8C8d35429F74ec245F8Ef2f4Fd1e551cFF97d650', '0x98e503f35D0a019cB0a251aD243a4cCFCF371F46']

### Intercepted JSON-RPC methods:

- `eth_sendTransaction`
- `eth_accounts`
- `eth_sign`
- `eth_signTypedData`

## Quickstart

### Get Accounts

Fetch the availible accounts.

    >>> from ledgereth import get_accounts
    >>> accounts = get_accounts()
    >>> accounts[0].address
    '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266'

### Create and Sign a Transaction

Create a transaction object and sign it with the default account.

    >>> from ledgereth import create_transaction
    >>> tx = create_transaction(
    ...         '0xb78f53524ae9d465279e7c3495f71d5db2419e13',  # to
    ...         int(1e18),  # value
    ...         int(1e5),   # gas limit
    ...         1,          # nonce
    ...         gas_price=int(1e9),   # gas price
    ...     )
    >>> tx.rawTransaction
    '0xf86c01843b9aca00830186a094b78f53524ae9d465279e7c3495f71d5db2419e13880de0b6b3a76400008025a0d1b85bfcf83dfb83c75665cd6d794f7147059377ade47c1fb4c3f44d9eb1a718a06e6305f0d5d65e3562660c0cc25d425c4a69687c22e6cee2cbc2455be2b2e2ec'

### Sign an Existing Transaction Object

Sign a `Transaction` object from pyethereum(or similar RLP serializable):

    >>> from ledgereth import sign_transaction
    >>> signed = sign_transaction(tx)
    >>> signed.rawTransaction
    '0xf86c01843b9aca00830186a094b78f53524ae9d465279e7c3495f71d5db2419e13880de0b6b3a76400008025a0d1b85bfcf83dfb83c75665cd6d794f7147059377ade47c1fb4c3f44d9eb1a718a06e6305f0d5d65e3562660c0cc25d425c4a69687c22e6cee2cbc2455be2b2e2ec'

### Sign a message

Sign a simple text message using the EIP-191 v0 standard:

    >>> from ledgereth import sign_message
    >>> signed = sign_message("I'm a little teapot")
    >>> signed.signature
    '0x7a26c1f3eab57a600f200c9e1bbc9014f738c1b6467e241e6a50af800d9e0e1d5d973ae1c72fc2cf393685c8bf4c40ad3000604f4ce1803375025b1901cd745c1c'
