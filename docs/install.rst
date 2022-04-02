#######
Install
#######

*******************
System Requirements
*******************

Some system level depenencies may be required for `ledgereth` to communicate with your Ledger.  These are the same `dependencies for ledgerblue`_. Python >= 3.6 is required.

.. _`dependencies for ledgerblue`: https://github.com/LedgerHQ/blue-loader-python#installation-pre-requisites

=====
Linux
=====

------
Ubuntu
------

.. code-block:: bash

    apt install TBD

----------
Arch Linux
----------

.. code-block:: bash

    pacman -S TBD

-----------
REHL/CentOS
-----------

.. code-block:: bash

    yum install TBD

-------
Windows
-------

*TBD.  Please submit a pull request if you figure it out.*

---
OSX
---

*TBD. Please submit a pull request if you figure it out.*


********************
Installing ledgereth
********************

Install it with system python:

.. code-block:: bash

    pip install --user ledgereth

Or, with a virtual environment:

.. code-block:: bash

    python -m venv ~/virtualenvs/ledgereth
    source ~/virtualenvs/ledgereth/bin/activate
    pip install ledgereth
