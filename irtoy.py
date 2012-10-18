#!/usr/bin/env python
#
# Class for simplifying the reading and transmitting of IR signals from the IR Toy.
# This only works for firmware revision 22 or greater.
# see https://github.com/crleblanc/PyIrToy and
# http://dangerousprototypes.com/docs/USB_Infrared_Toy for more info.
#
# Chris LeBlanc, 2012
#
#--
#
# This work is free: you can redistribute it and/or modify it under the terms 
# of Creative Commons Attribution ShareAlike license v3.0
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the License for more details. You should have received a copy of the License along 
# with this program. If not, see <http://creativecommons.org/licenses/by-sa/3.0/>.

import time
import binascii

class IrToy(object):

    def __init__(self, serialDevice):
        '''Create a new IrToy instance using the serial device for the USB IR Toy'''
        self.toy = serialDevice

        self.sleepTime = 0.05
        self.closed = False
        self.handshake = None
        self.byteCount = None
        self.complete = None

        # always use sampling mode
        self._setSamplingMode()

        self.transmitMode = False

    def _sleep(self):
        time.sleep(self.sleepTime)

    def _setSamplingMode(self):
        '''set the IR Toy to sampling mode, pretty much all the time'''
        self.reset()

        self.toy.write(b'S')

        self._sleep()

        self.protocolVersion = self.toy.read(3)

    def _writeList(self, code, check_handshake=False):
        '''write a list like object of integer values'''

        self._sleep()

        byteCode = bytearray(code)
        bytesWritten = 0

        # 31 * 2 bytes = max of 62 bytes in the buffer.  31 hangs so using 32, strange.
        maxWriteSize = 32
        for idx in range(0, len(code), maxWriteSize):
            segmentWritten = self.toy.write(byteCode[idx:idx+maxWriteSize])
            bytesWritten += segmentWritten

            if check_handshake:
                self.handshake = ord(self.toy.read(1))

        if bytesWritten != len(code):
            raise IOError('incorrect number of bytes written to serial device, expected %d' % len(code))

    def _getTransmitReport(self):
        '''get the byteCount and completion status from the IR Toy, so far we are always setting these to be used
        but could have that as an option'''

        hexBytes = binascii.b2a_hex(self.toy.read(3)[1:])
        self.byteCount = int(hexBytes, 16)
        self.complete = self.toy.read(1)

    def _setTransmit(self):
        self._sleep()
        self._writeList([0x26]) #Enable transmit handshake
        self._writeList([0x25]) #Enable transmit notify on complete
        self._writeList([0x24]) #Enable transmit byte count report
        self._writeList([0x03], check_handshake=True) #Expect to receive packets to transmit

        self.transmitMode = True

    def receive(self):
        '''Read a signal from the toy, returns a list of IR Codes converted from hex to ints.  See 
        http://dangerousprototypes.com/docs/USB_IR_Toy:_Sampling_mode for more information on the
        sample format'''

        self._sleep()

        # reset and put back in receive mode in case it was in transmit mode or there was junk in the buffer
        self._setSamplingMode()

        bytesToRead=1
        readCount=0
        irCode = []

        while(True):
            readVal = self.toy.read(bytesToRead)
            hexVal = binascii.b2a_hex(readVal)
            intVal = int(hexVal, 16)

            irCode.append(intVal)

            if readCount >= 2 and intVal == 255 and irCode[-2] == 255:
                break

            readCount += 1

        return irCode

    def reset(self):
        '''Reset the IR Toy to sampling mode with nothing in the buffer'''

        self._sleep()
        self._writeList([0x00]*5)

    def transmit(self, code):
        '''switch to transmit mode and write the list (or list-like) set of ints to the toy for transmission,
        Must be an even number of elements.  The list created by read() can be used for transmitting.  If the
        last two elements of the list are not 0xff these will be appended.'''

        if len(code) < 2:
            raise ValueError("Length of code argument must be greater than or equal to two")

        if len(code) % 2 != 0:
            raise ValueError("Length of code argument must be an even number")

        # ensure the last two codes are always 0xff (255) to tell the IR Toy it's the end of the signal
        if code[-2:] != [0xff, 0xff]:
            code.extend([0xff, 0xff])

        self._sleep()
        self._setTransmit()
        self._writeList(code, check_handshake=True)
        self._getTransmitReport()

    def close(self):
        '''reset and close the serial connection'''

        self.reset()

        # sleeps are important, otherwise we risk losing the serial interface from Linux
        self._sleep()
        self.closed = True

    def __del__(self):

        if not self.closed:
            self._sleep()
            self.close()
