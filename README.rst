Important Note
==============
This project relies on the IR Toy for transmitting and receiving IR signals. Unfortunately this hardware seems to suffer from a firmware bug described here https://github.com/crleblanc/PyIrToy/issues/2, which seems especially bad on the Raspberry Pi. I haven't been able to find a workaround for this stability problem, so cannot recommend using the IR Toy. Unfortunately development on the IR Toy project appears to have stopped.

PyIrToy
=======

A python module for transmitting and receiving infrared signals from an IR Toy.
This requires the Dangerous Prototype USB IR Toy 
(http://dangerousprototypes.com/docs/USB_Infrared_Toy) with firmware revision 22
or higher.

This module has been tested with Python 2.7 and 3.2 on Ubuntu 12.04.  There is 
no OS specific code in this module, so it should work on Mac OS and Windows but
has not been tested.

This module is available on PyPi (http://pypi.python.org/pypi/pyirtoy) and can
be installed with the command "pip install pyirtoy" (this may require the sudo
command, if installing for all users).

This module makes it easy to transmit to and receive from an IR Toy.  The wiki
has some quick examples (https://github.com/crleblanc/PyIrToy/wiki).
