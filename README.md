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

# Important Note

This project relies on the IR Toy for transmitting and receiving IR signals.
Unfortunately this hardware seems to suffer from a firmware bug described
here https://github.com/crleblanc/PyIrToy/issues/2, which seems especially
bad on the Raspberry Pi. I haven't been able to find a workaround for this
stability problem, so cannot recommend using this project for long running
tasks.

Examples
========

## Transmitting a custom IR code.

This uses the IR code mentioned here http://dangerousprototypes.com/docs/USB_IR_Toy:_Sampling_mode.

```python
#!/usr/bin/env python
import serial
import irtoy

with serial.Serial('/dev/ttyACM0') as serial_device:

    # create a new instance of the IrToy class
    toy = irtoy.IrToy(serial_device)

    # this list of ints represents the IR code, a sequence of on, off times followed
    # by 255, 255 to mark the end of the code.  If these are not present they will be appended.
    ir_code = [10, 10, 5, 20, 255, 255]

    # transmit the recorded signal back to the IR Toy
    toy.transmit(ir_code)
```


## Recording and transmitting an IR code

This example records an IR code from some device, such as a TV remote.  The then transmits
this code on the IR Toy.


```python
#!/usr/bin/env python
from __future__ import print_function
import serial
import irtoy

with serial.Serial('/dev/ttyACM0') as serial_device:

    # create a new instance of the IrToy class
    toy = irtoy.IrToy(serial_device)

    # receive an IR signal from the IR Toy, stored in a list.
    # Note: this call will block (hang) until an IR code has been received.
    print('waiting to record an IR signal')
    ir_code = toy.receive()

    print('received IR signal:', ir_code)

    # transmit the recorded signal back to the IR Toy
    toy.transmit(ir_code)
```
