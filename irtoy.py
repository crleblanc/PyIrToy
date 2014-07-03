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

__author__ = 'Chris LeBlanc'
__version__ = '0.2.6'
__email__ = 'crleblanc@gmail.com'

class FirmwareVersionError(Exception):
    pass

class IRTransmitError(Exception):
    pass


class IrToy(object):

    def __init__(self, serialDevice):
        '''Create a new IrToy instance using the serial device for the USB IR Toy'''
        self.toy = serialDevice

        self.sleepTime = 0.05
        self.checkHandshake = False
        self.checkTransmitNotify = False
        self.checkByteCount = False
        self.handshake = None
        self.byteCount = None

        self.requiredVersion = 22
        hardware, revision = self.firmware_revision()
        if self.firmware_revision()[1] < self.requiredVersion:
            raise FirmwareVersionError("pyirtoy will only work with firmware version %d or greater, current=%d"
                                        % (self.requiredVersion, revision))

        # always use sampling mode
        self._setSamplingMode()

        self.transmitMode = False


    def firmware_revision(self):
        '''Return the hardware and firmware revision returned as a tuple'''
        self.reset()
        self.toy.write(b'v')
        self._sleep()

        versionString = self.toy.read(4)
        hardwareVersion = int(versionString[1:2])
        firmwareVersion = int(versionString[2:4])

        return hardwareVersion, firmwareVersion

    def _sleep(self):
        time.sleep(self.sleepTime)

    def _writeList(self, code, check_handshake=False):
        '''write a list like object of integer values, if check_handshake is true it returns that code,
        otherwise returns None'''

        self._sleep()

        byteCode = bytearray(code)
        bytesWritten = 0
        handshake = None

        # 31 * 2 bytes = max of 62 bytes in the buffer.  31 hangs so using 32, strange.
        maxWriteSize = 32
        for idx in range(0, len(code), maxWriteSize):
            segmentWritten = self.toy.write(byteCode[idx:idx+maxWriteSize])
            bytesWritten += segmentWritten

            if check_handshake:
                handshake = ord(self.toy.read(1))

        if bytesWritten != len(code):
            raise IOError("incorrect number of bytes written to serial device, expected %d" % len(code))
            
        return handshake

    def _checkTransmitReport(self):
        '''get the byteCount and completion status from the IR Toy'''

        if self.checkByteCount:
            hexBytes = binascii.b2a_hex(self.toy.read(3)[1:])
            self.byteCount = int(hexBytes, 16)

        if self.checkTransmitNotify:
            complete = self.toy.read(1)

            if complete not in [b'c', b'C']:
                raise IRTransmitError("Failed to transmit IR code, report=%s" % complete)

    def _setSamplingMode(self):
        '''set the IR Toy to use sampling mode, which we use exclusively'''
        self.reset()

        self.toy.write(b'S')

        self._sleep()

        self.protocolVersion = self.toy.read(3)

        self._sleep()

    def _setTransmitMode(self):
        '''set the IR Toy to use transmit mode.  Used by the transmit method'''

        self._sleep()

        if self.checkHandshake:
            # Enable transmit handshake
            self._writeList([0x26])

        if self.checkTransmitNotify:
            # Enable transmit notify on complete
            self._writeList([0x25])

        if self.checkByteCount:
            # Enable transmit byte count report
            self._writeList([0x24])

        # TODO: look into check_handshake here, not 100% sure what this expects in this case
        handshake = self._writeList([0x03], check_handshake=self.checkHandshake) #Expect to receive packets to transmit

        self.transmitMode = True

    def receive(self):
        '''Read a signal from the toy, returns a list of IR Codes converted from hex to ints.  See
        http://dangerousprototypes.com/docs/USB_IR_Toy:_Sampling_mode for more information on the
        sample format.  Reading starts when an IR signal is received and stops after 1.7 seconds of
        inactivity'''

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

        self._sleep()

        return irCode

    def reset(self):
        '''Reset the IR Toy to sampling mode and clear the Toy's 62 byte buffer'''

        self._sleep()
        self._writeList([0x00]*5)
        self.transmitMode = False
        self._sleep()

    def transmit(self, code, check_handshake=False, check_complete=False, check_byte_count=False):
        '''switch to transmit mode and write the list (or list-like) set of ints to the toy for transmission,
        Must be an even number of elements.  The list created by read() can be used for transmitting.  If the
        last two elements of the list are not 0xff these will be appended.'''

        # TODO: add docstrings for kwargs

        if len(code) < 2:
            raise ValueError("Length of code argument must be greater than or equal to two")

        if len(code) % 2 != 0:
            raise ValueError("Length of code argument must be an even number")

        # ensure the last two codes are always 0xff (255) to tell the IR Toy it's the end of the signal
        if code[-2:] != [0xff, 0xff]:
            code.extend([0xff, 0xff])

        self.checkHandshake = check_handshake
        self.checkTransmitNotify = check_complete
        self.checkByteCount = check_byte_count

        try:
            self._sleep()
            self._setTransmitMode()
            # Currently not using the handshake response
            handshake = self._writeList(code, check_handshake=self.checkHandshake)
            self._sleep()
            self._checkTransmitReport()
        except:
            # if anything went wrong then sheepishly try to reset state and raise the exception,
            # surprisingly common on a weak CPU like the raspberry pi
            self.reset()
            self._setSamplingMode()
            raise

        # experimentation shows that returning to sampling mode is needed to avoid 
        # dropping the serial connection on Linux
        self._setSamplingMode()
