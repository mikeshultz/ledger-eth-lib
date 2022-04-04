######################
Command Line Interface
######################

ledgereth provides a pretty limited CLI to use for quick one-off tasks and testing.

.. code-block:: bash

    python -m ledgereth [command]

************
Get Accounts
************

.. code-block:: bash

    python -m ledgereth accounts

***************************
Create and Sign Transaction
***************************

.. code-block:: bash

    python -m ledgereth send FROM_ADDRESS TO_ADDRESS VALUE_WEI -n NONCE -p GAS_PRICE_WEI -c CHAIN_ID

**************
Sign a Message
**************

.. code-block:: bash

    python -m ledgereth sign SIGNER_ADDRESS "I'm a little teapot"

***************
Sign Typed Data
***************

This command, similar to the library, only takes hashes of the domain and message.  That's because the Ledger Ethereum app itself only deals with these hashes rather than the data/message iteself.  For more details on how you might generate these hashes, see the `typed data signing implementation in the tests`_.

.. code-block:: bash

    python -m ledgereth signtyped SIGNER_ADDRESS DOMAIN_HASH MESSAGE_HASH

.. _`typed data signing implementation in the tests`: https://github.com/mikeshultz/ledger-eth-lib/blob/fce09508ab8d37a59c18617c68edc00cdcbb1261/tests/test_message_signing.py#L55-L74
