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
import gc

__author__ = 'Chris LeBlanc'
__version__ = '0.2.7'
__email__ = 'crleblanc@gmail.com'


class FirmwareVersionError(Exception):
    pass


class IRTransmitError(Exception):
    pass


class IrToy(object):

    def __init__(self, serialDevice):
        '''Create a new IrToy instance using the serial device for the USB IR Toy'''
        self.toy = serialDevice

        self.sleep_time = 0.05
        self.handshake = None
        self.byte_count = None
        self.complete = None

        self.required_version = 22
        if self.firmware_revision()[1] < self.required_version:
            raise FirmwareVersionError("pyirtoy will only work with firmware version %d or greater, current=%d"
                                        % (self.required_version, revision))
        
        # always use sampling mode
        self._set_sampling_mode()

        self.transmit_mode = False


    def firmware_revision(self):
        '''Return the hardware and firmware revision returned as a tuple'''
        self.reset()
        self.toy.write(b'v')
        self._sleep()
        
        version_string = self.toy.read(4)
        hardware_version = int(version_string[1:2])
        firmware_version = int(version_string[2:4])

        return hardware_version, firmware_version

    def _sleep(self):
        time.sleep(self.sleep_time)

    def _set_sampling_mode(self):
        '''set the IR Toy to use sampling mode, which we use exclusively'''
        self.reset()
        self.toy.write(b'S')
        
        self._sleep()
        self.protocolVersion = self.toy.read(3)
        self._sleep()

    def _write_list(self, code, check_handshake=False):
        '''write a list like object of integer values'''

        self._sleep()

        byte_code = bytearray(code)
        segment_written = 0
        bytes_written = 0

        try:
            # 31 * 2 bytes = max of 62 bytes in the buffer.  Slices are non-inclusive.
            gc.disable()
            max_write_size = 31
            for idx in range(0, len(code), max_write_size+1):
                segment_written = self.toy.write(byte_code[idx:idx+max_write_size+1])
                bytes_written += segment_written

                if check_handshake:
                    self.handshake = ord(self.toy.read(1))
        finally:
            gc.enable()

        if bytes_written != len(code):
            raise IOError("incorrect number of bytes written to serial device, expected %d" % len(code))

    def _get_transmit_report(self):
        '''get the byte_count and completion status from the IR Toy'''

        hex_bytes = binascii.b2a_hex(self.toy.read(3)[1:])
        self.byte_count = int(hex_bytes, 16)
        self.complete = self.toy.read(1)

    def _set_transmit(self):
        
        self._sleep()
        self._write_list([0x26]) #Enable transmit handshake
        self._write_list([0x25]) #Enable transmit notify on complete
        self._write_list([0x24]) #Enable transmit byte count report
        self._write_list([0x03], check_handshake=True) #Expect to receive packets to transmit
        self.transmit_mode = True

    def receive(self):
        '''Read a signal from the toy, returns a list of IR Codes converted from hex to ints.  See 
        http://dangerousprototypes.com/docs/USB_IR_Toy:_Sampling_mode for more information on the
        sample format.  Reading starts when an IR signal is received and stops after 1.7 seconds of 
        inactivity'''

        self._sleep()

        # reset and put back in receive mode in case it was in transmit mode or there was junk in the buffer
        self._set_sampling_mode()

        bytes_to_read=1
        read_count=0
        ir_code = []

        while(True):
            read_val = self.toy.read(bytes_to_read)
            hex_val = binascii.b2a_hex(read_val)
            int_val = int(hex_val, 16)

            ir_code.append(int_val)

            if read_count >= 2 and int_val == 255 and ir_code[-2] == 255:
                break

            read_count += 1

        self._sleep()

        return ir_code

    def reset(self):
        '''Reset the IR Toy to sampling mode and clear the Toy's 62 byte buffer'''

        self._sleep()
        self._write_list([0x00]*5)
        self.transmit_mode = False
        self._sleep()

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

        try:
            self._sleep()
            self._set_transmit()
            self._write_list(code, check_handshake=True)
            self._sleep()
            self._get_transmit_report()

            if self.complete not in [b'c', b'C']:
                raise IRTransmitError("Failed to transmit IR code, report=%s" % self.complete)
        except:
            # if anything went wrong then sheepishly try to reset state and raise the exception,
            # surprisingly common on a weak CPU like the raspberry pi
            #self.toy.flushOutput() # hmm, maybe this will help? Interesting: we get a crazy state until a new program is started, then fine.
            self.reset()
            self._set_sampling_mode()
            raise

        # experimentation shows that returning to sampling mode is needed to avoid dropping the serial connection on Linux
        self._set_sampling_mode()
