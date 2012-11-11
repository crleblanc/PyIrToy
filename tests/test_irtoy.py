#!/usr/bin/env python
#
# Unit tests for Python IR Toy module.  For more information see:
# http://dangerousprototypes.com/docs/USB_Infrared_Toy
#
# Chris LeBlanc 2012

import unittest
import os
import sys
# not sure how to get around this ugly hack:
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from irtoy import IrToy

class SerialMock(object):
    '''A serial device stand-in class used to mock out the serial object so we can 
    see what was written, and fake something to be read'''
    
    def __init__(self):
        self.writeHistory = []
        self.readCount = 0
        self.readCode = None
        
    def write(self, code):
        
        # code can be either strings or hex numbers, so convert bytearrays to ints
        # for ease of comparison
        convertedCode = None
        if isinstance(code, bytearray):
            convertedCode = [int(x) for x in code]
        else:
            convertedCode = code
            
        self.writeHistory.append(convertedCode)

        return len(code)

    def setReadCode(self, code):
        '''set the code that the read() method will emit when called.  Each 
        call to read() will return the ith element in the supplied list'''
        self.readCode = code

    def read(self, nBytes):
        
        if self.readCode:
            response = self.readCode[self.readCount]
            self.readCount += 1
        else:
            response = b'S01'
        
        return response
        

    def close(self):
        pass
        

class TestIrToy(unittest.TestCase):

    def setUp(self):

        self.serialMock = SerialMock()
        self.toy = IrToy(self.serialMock)
        self.toy.sleepTime = 0

    def testTransmit(self):

        # length of code sent must be even
        self.assertRaises(ValueError, self.toy.transmit, [10])
        
        # set the expected results from read(): protocol version, handshake ('>' converts to 62),
        # byte count transmitted, and completion code.  Not using these, so just putting junk in.
        self.serialMock.setReadCode([bytearray([62]), bytearray([62]), bytearray([0,0,0,1]), b'C'])
        
        self.toy.transmit([10,10])
        
        # when transmitting, we expect a reset (five 0x00), 'S' to enter sampling mode, 0x26 for enable handshake,
        # 0x25 to enable notify on transmit, 0x24 to enable transmit byte count, and 0x03 to start the transmission,
        # then the list of codes to transmit (always ending with 0xff, 0xff), and another reset.  See DP link at top of this file for more info.
        expectedHistory = [[0x00, 0x00, 0x00, 0x00, 0x00],
                            b'S', [0x26], [0x25], [0x24], [0x03],
                            [10, 10, 0xff, 0xff],
                            [0x00, 0x00, 0x00, 0x00, 0x00]]

        self.assertEqual(self.serialMock.writeHistory, expectedHistory)

    def testReceive(self):

        # pretend to be receiving the following signals from the IR Toy, must end with 0xff,0xff (same as 255, means no signal) 
        # or the code will keep recording indefinitely.  First element is for the protocol version, since receive() resets the toy
        self.serialMock.setReadCode([bytearray([62]), bytearray([1]), bytearray([2]), bytearray([0xff]), bytearray([0xff])])
        readSignal = self.toy.receive()

        self.assertEqual(readSignal, [1, 2, 0xff, 0xff])
        

if __name__ == '__main__':
    unittest.main()
