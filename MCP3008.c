/* MCP3008.c
 *
 * This file contains functions for letting the Omega interact with an MCP3008,
 * a 8-channel 10 bit ADC.
 *
 * Ported by: Maximilian Gerhardt, January 2018.
 */
#include "MCP3008.h"

#include <stdio.h>
#include <stdbool.h>
#include <unistd.h> /* for slep() */
#include <onion-spi.h> /* main SPI functionality */
#include <onion-debug.h> /* debug output */

/* Global SPI object. Can only have 1 user at a time. */
static struct spiParams params;

/* Depending on the given VDD voltage, the MCP3008 supports a different maximum SPI clock speeds. */
#define MCP3008_SPI_MAX_5V  3600000
#define MCP3008_SPI_MAX_3V  1350000
#define MCP3008_SPI_MAX     MCP3008_SPI_MAX_3V /* Select the 3.3V version*/

static int SPIxADC(int channel, bool differential);

/* Initialize the SPI bus on the given GPIO pins.
 * On the MCP3008, these pins are called D_out, D_in, CLK, /CS/SHDN
 * */
bool MCP3008_Startup(int miso, int mosi, int sclk, int cs) {

	int err = 0;

	//Start initializing the SPI bus.
	spiParamInit(&params);
	params.misoGpio = miso;
	params.mosiGpio = mosi;
	params.sckGpio = sclk;
	params.csGpio = cs;
	params.speedInHz = MCP3008_SPI_MAX;
	params.modeBits = SPI_MODE_0;
	params.busNum = 1; //this comes from my local machine. no idea if it works elsewhere.. (ls /dev/spi*)
	params.deviceId = 32766;
	params.delayInUs = 10;

	//is our device already mapped?
	err = spiCheckDevice(params.busNum, params.deviceId, ONION_SEVERITY_DEBUG);
	if(err == EXIT_FAILURE) {
		printf("[-] spiCheckDevice() failed.\n");
		return false;
	}

	//register ourselves
	err = spiRegisterDevice(&params);
	if(err == EXIT_FAILURE)  {
		printf("spiRegisterDevice() failed.\n");
		return false;
	}
	printf("[+] SPI register device okay.\n");

	err = spiSetupDevice(&params);
	if(err == EXIT_FAILURE)  {
		printf("spiSetupDevice() failed.\n");
		return false;
	}

	return true;
}

int MCP3008_ReadChannel(int channel) {
	if ((channel < 0) || (channel > 7)) return -1;
	return SPIxADC(channel, false);
}

int MCP3008_ReadChannelDifferential(int differential) {
	if ((differential < 0) || (differential > 7)) return -1;
	return SPIxADC(differential, true);
}

static int SPIxADC(int channel, bool differential) {
	uint8_t command, sgldiff;

	if (differential) {
		sgldiff = 0;
	} else {
		sgldiff = 1;
	}

	command = ((0x01 << 7) |               // start bit
			(sgldiff << 6) |              // single or differential
			((channel & 0x07) << 3) );    // channel number


	uint8_t spiRequest[3] = { command, 0x00, 0x00};
	uint8_t spiResponse[3];

	spiTransfer(&params, spiRequest, spiResponse, sizeof(spiRequest));

	//Reconstruct numerical 10-bit ADC value
	uint8_t b0 = spiResponse[0], b1 = spiResponse[1], b2 = spiResponse[2];

	return 0x3FF & ((b0 & 0x01) << 9 |
			(b1 & 0xFF) << 1 |
			(b2 & 0x80) >> 7 );
}