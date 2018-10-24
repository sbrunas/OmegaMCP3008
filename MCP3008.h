#ifndef MCP3008_H_
#define MCP3008_H_

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

bool MCP3008_Startup(int miso, int mosi, int sclk, int cs);
int MCP3008_ReadChannel(int channel);
int MCP3008_ReadChannelDifferential(int differential);

#endif /* MCP3008_H_ */