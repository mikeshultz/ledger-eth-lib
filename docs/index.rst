#########
ledgereth
#########

`ledgereth <https://github.com/mikeshultz/ledger-eth-lib/>`_ is a library to make interacting with a Ledger hardware wallet easy.

==========
Quickstart
==========

Here's the quickest way to get started.

.. code-block:: bash

    pip install ledgereth

You may want to setup a `Python virtual environment`_ and your system may
require some installed dependencies.  For full installation instructions, see
:doc:`install`.

=============
Configuration
=============

Generally this library does not have any configuration but there are a couple of
places where environment variables alter the behavior of the library.  Most
people will probably not need these, but for some they may be critical.

- ``MAX_ACCOUNTS_FETCH`` (default: `3`): The maximum accounts that will be fetched when looking up by address. If you created more than 3 accounts on your Ledger device, you may want to adjust this.  The more accounts fetched the slower operations may take.

- ``LEDGER_LEGACY_ACCOUNTS``: If set (to anything), ledger-eth-lib will use the legacy Ledger `BIP-44`_ derivation that was used to create accounts **before Ledger Live**.


.. toctree::
   :maxdepth: 2
   :caption: Contents

   install
   cli
   accounts
   transaction_signing
   message_signing
   web3


==================
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _`BIP-44`: https://en.bitcoin.it/wiki/BIP_0044
.. _`Python virtual environment`: https://docs.python.org/3/tutorial/venv.html
