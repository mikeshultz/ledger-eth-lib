###################
Web3.py Integration
###################

You can also integrate ledgereth directly into Web3.py to use it with your Ledger hardware wallet.

*******************
Middleware Usage
*******************

You can add the `LedgerSignerMiddleware` into web3.py and use it normally.

.. code:: python
    >>> from web3.auto import w3
    >>> from ledgereth.web3 import LedgerSignerMiddleware
    >>> w3.middleware_onion.add(LedgerSignerMiddleware)
    >>> w3.eth.accounts
    ['0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266', '0x8C8d35429F74ec245F8Ef2f4Fd1e551cFF97d650', '0x98e503f35D0a019cB0a251aD243a4cCFCF371F46']

.. automodule:: ledgereth.web3
    :members:
