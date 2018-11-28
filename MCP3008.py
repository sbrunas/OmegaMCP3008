#!/usr/bin/env python

import onionSpi
import time
import struct

def printSettings(obj):
	print "SPI Device Settings:"
	print "  bus:    %d"%(obj.bus)
	print "  device: %d"%(obj.device)
	print "  speed:    %d Hz (%d kHz)"%(obj.speed, obj.speed/1000)
	print "  delay:    %d us"%(obj.delay)
	print "  bpw:      %d"%(obj.bitsPerWord)
	print "  mode:     %d (0x%02x)"%(obj.mode, obj.modeBits)
	print "     3wire:    %d"%(obj.threewire)
	print "     lsb:      %d"%(obj.lsbfirst)
	print "     loop:     %d"%(obj.loop)
	print "     no-cs:    %d"%(obj.noCs)
	print "     cs-high:  %d"%(obj.csHigh)
	print ""
	print "GPIO Settings:"
	print "  sck:      %d"%(obj.sck)
	print "  mosi:     %d"%(obj.mosi)
	print "  miso:     %d"%(obj.miso)
	print "  cs:       %d"%(obj.cs)
	print ""

#Returns a correctly configured SPI device
def initADC(miso, mosi, sclk, cs):
	spiDev  = onionSpi.OnionSpi(1, 32766)
	#objects members
	#----------------------------------------
	spiDev.delay = 10
	spiDev.mode = 0
	spiDev.sck = sclk
	spiDev.mosi = mosi
	spiDev.miso = miso
	spiDev.cs = cs
	spiDev.speed = 1350000 # for 3.3V supply
	#----------------------------------------
	spiDev.setVerbosity(0)
	# check the device
	#return 0 if the device adapter is alredy mapped, 1 if the device adapter is NOT mapped
	print 'Checking if device exists...'
	ret = spiDev.checkDevice()
	print '   Device does not exist: %d'%(ret)

	# register the device
	print 'Registering the device...'
	ret = spiDev.registerDevice()
	print '   registerDevice returned: %d'%(ret)

	# initialize the device parameters
	print 'Initializing the device parameters...'
	ret = spiDev.setupDevice()
	print '   setupDevice returned: %d'%(ret)

	# check the device again
	print '\nChecking if device exists...'
	ret = spiDev.checkDevice()
	print '   Device does not exist: %d'%(ret)
	return spiDev
	
#reads an ADC channel 
def readADC(spiDev, channel):
	#sanity check
	if channel < 0 or channel > 7:
		return -1
	return SPIxADC(spiDev, channel, False)

def readADCDiff(spiDev, differential):
	if differential < 0 or differential > 7:
		return -1		
	return SPIxADC(spiDev, differential, True);

def SPIxADC(spiDev, channel, differential):
	command = 0
	sgldiff = 0

	if differential:
		sgldiff = 0
	else:
		sgldiff = 1
	
	# start bit + single or differential + channel number 
	command = ((0x01 << 7) | (sgldiff << 6) | ((channel & 0x07) << 3) )
	
	# This function will transmit 3 bytes.
	# TX buffer of 3 bytes is only populated with 1 byte (command)
	# rest is filled with random data (due to malloc), but thankfully that doesn't matter.
	# we just need some dummy bytes there.
	# 3 bytes will be read into the RX buffer.
	# see https://github.com/OnionIoT/spi-gpio-driver/blob/master/src/python/python-onion-spi.c#L131
	# we CANNOT use 3 different .readBytes() calls because the delay between them would be 
	# too big. Thus we'll only read 0xff.. 
	spiResp = spiDev.readBytes(command, 3)

	b0 = spiResp[0]
	b1 = spiResp[1]
	b2 = spiResp[2]
	
	#print(b0,b1,b2)
	#reconstruct 10-bit ADC value
	return 0x3FF & ((b0 & 0x01) << 9 | (b1 & 0xFF) << 1 | (b2 & 0x80) >> 7 )
	
	
# MAIN PROGRAM

spi = initADC(12,8,7,6)
printSettings(spi)

try:
	for i in range(30):

		adcValues = []
		for chan in range(0, 8):
			adcValues.append(readADC(spi, chan))

		line = ','.join(str(v) for v in adcValues)		
		print(line)
	
		time.sleep(0.3)
		
except KeyboardInterrupt:
	print("Operation cancelled")