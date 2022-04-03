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

.. code-block:: bash

    python -m ledgereth signtyped SIGNER_ADDRESS DOMAIN_HASH MESSAGE_HASH
