#######
Install
#######

*******************
System Requirements
*******************

Some system level depenencies may be required for `ledgereth` to communicate with your Ledger.  These are the same `dependencies for ledgerblue`_. Python >= 3.8 is required.

.. _`dependencies for ledgerblue`: https://github.com/LedgerHQ/blue-loader-python#installation-pre-requisites

=====
Linux
=====

-------------------
Common Connectivity
-------------------

.. note::

    You can skip this part if you already have Ledger Live working, or some other way of communicating with your Ledger on your system.

Common for every distro, is that you'll need to create some udev rules to grant your user permissions to access your Ledger device.  You will need the vendor and product ID.  You can get them like this:

.. code:: bash

    $ lsusb | grep Ledger
    Bus 001 Device 010: ID 2c97:1015 Ledger Nano S

Right before the device name you'll see the product and vendor ID (in this case, ``2c97:1015``).  Then you should create a file like `/etc/udev/rules.d/20-hw1.rules` and add a specific rule like this:

.. code::

    SUBSYSTEMS=="usb", ATTRS{idVendor}=="2c97", ATTRS{idProduct}=="1015", MODE="0660", TAG+="uaccess", TAG+="udev-acl" OWNER="<UNIX username>"

Then either reboot or trigger udev to reload the rules like this:

.. code:: bash

    $ udevadm control --reload-rules
    $ udevadm trigger

Ledger also created a `useful script and rules file`_ that you can use.  For more information, see the `Ledger support site for connectivity issues`_.

.. _`useful script and rules file`: https://github.com/LedgerHQ/udev-rules
.. _`Ledger support site for connectivity issues`: https://support.ledger.com/hc/en-us/articles/115005165269-Connection-issues-with-Windows-or-Linux?support=true

------
Ubuntu
------

Ubuntu is just about good out of the box, the only thing you'll might want to install is pip and virtualenv tools.

.. code:: bash

    $ apt install python3-venv python3-pip 

The ``python3-venv`` package is optional but it's generally a good idea.  Your call.

----------
Arch Linux
----------

.. code:: bash

    $ pacman -S base-devel python

-----------
REHL/CentOS
-----------

The group "Development Tools" and package `python3-devel` must be installed to be able to compile some of the dependencies. 

.. code:: bash

    $ dnf groupinstall "Development Tools"
    $ dnf install python3-devel

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

.. code:: bash

    $ pip install --user ledgereth

Or, with a virtual environment:

.. code:: bash

    $ python -m venv ~/virtualenvs/ledgereth
    $ source ~/virtualenvs/ledgereth/bin/activate
    $ pip install ledgereth
