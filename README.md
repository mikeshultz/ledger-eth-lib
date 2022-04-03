# ledgereth

[![Documentation Status](https://readthedocs.org/projects/ledgereth/badge/?version=latest)](https://ledgereth.readthedocs.io/en/latest/?badge=latest)

**This library is beta.  Please [report any bugs](https://github.com/mikeshultz/ledger-eth-lib/issues/new) you find.**

This is a library to interact with [ledger-app-eth](https://github.com/LedgerHQ/ledger-app-eth), the Ethereum app for the [Ledger hardware wallets](https://www.ledger.com/).  It's goal is to make interfacing with the Ledger nice and simple with well known Ethereum+Python tools.

## Quickstart

Here’s the quickest way to get started.

    pip install ledgereth

Please see [the ledgereth documentation](https://ledgereth.readthedocs.io/) for more detailed information.

## Compatability

### Ledger Devices

This lib has been tested to work on Ledger Nano S and Nano X.  It will probalby work with Ledger Blue and any devices the [`ledgerblue` library](https://github.com/LedgerHQ/blue-loader-python) and [ledger-app-eth](https://github.com/LedgerHQ/ledger-app-eth) supports.

### Ledger Account Derivations

The Ledger-provided desktop apps have changed the way accounts are derived with the release of Ledger Live.  If you created your Ledger account(s) with the older Chrome app and want to use those account(s) with this library, you will need to set the `LEDGER_LEGACY_ACCOUNTS` env var. You can only use one or the other at a time.  See [the notes in source for more information](https://github.com/mikeshultz/ledger-eth-lib/blob/master/ledgereth/web3.py#L8-L34).
