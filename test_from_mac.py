#!/usr/bin/env python

# Trying the irtoy on the mac.  Testing disable of Python's GC to see if that makes any difference.

import serial
import irtoy

class SerialSniffer(serial.Serial):

    def write(self, *args, **kawrgs):
        print '  writing', args
        return super(SerialSniffer, self).write(*args, **kawrgs)

    def read(self, *args, **kawrgs):
        response = super(SerialSniffer, self).read(*args, **kawrgs)
        print '    read', response
        return response

def main():
    with SerialSniffer('/dev/tty.usbmodem00000001', timeout=100) as serialDevice:
    
        # create a new instance of the IrToy class
        print 'creating instance'
        toy = irtoy.IrToy(serialDevice)
        
        irCode = [x for x in range(254)] + [255,255]
        
        # transmit the recorded signal back to the IR Toy
        print 'writing', irCode
        toy.transmit(irCode)
        print 'report', toy.byteCount, toy.complete

if __name__ == '__main__':
    main()