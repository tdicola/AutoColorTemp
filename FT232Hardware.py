import struct
import time

from mpsse import *

# Constants for the TCS 34725 sensor ported from Adafruit library:
#   https://github.com/adafruit/Adafruit_TCS34725
TCS34725_ADDRESS          = 0x29
TCS34725_COMMAND_BIT      = 0x80
TCS34725_ENABLE           = 0x00
TCS34725_ENABLE_AIEN      = 0x10    # RGBC Interrupt Enable
TCS34725_ENABLE_WEN       = 0x08    # Wait enable - Writing 1 activates the wait timer
TCS34725_ENABLE_AEN       = 0x02    # RGBC Enable - Writing 1 actives the ADC, 0 disables it
TCS34725_ENABLE_PON       = 0x01    # Power on - Writing 1 activates the internal oscillator, 0 disables it
TCS34725_ATIME            = 0x01    # Integration time
TCS34725_WTIME            = 0x03    # Wait time = if TCS34725_ENABLE_WEN is asserted
TCS34725_WTIME_2_4MS      = 0xFF    # WLONG0 = 2.4ms   WLONG1 = 0.029s
TCS34725_WTIME_204MS      = 0xAB    # WLONG0 = 204ms   WLONG1 = 2.45s 
TCS34725_WTIME_614MS      = 0x00    # WLONG0 = 614ms   WLONG1 = 7.4s  
TCS34725_AILTL            = 0x04    # Clear channel lower interrupt threshold
TCS34725_AILTH            = 0x05
TCS34725_AIHTL            = 0x06    # Clear channel upper interrupt threshold
TCS34725_AIHTH            = 0x07
TCS34725_PERS             = 0x0C    # Persistence register - basic SW filtering mechanism for interrupts
TCS34725_PERS_NONE        = 0b0000  # Every RGBC cycle generates an interrupt                               
TCS34725_PERS_1_CYCLE     = 0b0001  # 1 clean channel value outside threshold range generates an interrupt  
TCS34725_PERS_2_CYCLE     = 0b0010  # 2 clean channel values outside threshold range generates an interrupt 
TCS34725_PERS_3_CYCLE     = 0b0011  # 3 clean channel values outside threshold range generates an interrupt 
TCS34725_PERS_5_CYCLE     = 0b0100  # 5 clean channel values outside threshold range generates an interrupt 
TCS34725_PERS_10_CYCLE    = 0b0101  # 10 clean channel values outside threshold range generates an interrupt
TCS34725_PERS_15_CYCLE    = 0b0110  # 15 clean channel values outside threshold range generates an interrupt
TCS34725_PERS_20_CYCLE    = 0b0111  # 20 clean channel values outside threshold range generates an interrupt
TCS34725_PERS_25_CYCLE    = 0b1000  # 25 clean channel values outside threshold range generates an interrupt
TCS34725_PERS_30_CYCLE    = 0b1001  # 30 clean channel values outside threshold range generates an interrupt
TCS34725_PERS_35_CYCLE    = 0b1010  # 35 clean channel values outside threshold range generates an interrupt
TCS34725_PERS_40_CYCLE    = 0b1011  # 40 clean channel values outside threshold range generates an interrupt
TCS34725_PERS_45_CYCLE    = 0b1100  # 45 clean channel values outside threshold range generates an interrupt
TCS34725_PERS_50_CYCLE    = 0b1101  # 50 clean channel values outside threshold range generates an interrupt
TCS34725_PERS_55_CYCLE    = 0b1110  # 55 clean channel values outside threshold range generates an interrupt
TCS34725_PERS_60_CYCLE    = 0b1111  # 60 clean channel values outside threshold range generates an interrupt
TCS34725_CONFIG           = 0x0D
TCS34725_CONFIG_WLONG     = 0x02    # Choose between short and long = 12x wait times via TCS34725_WTIME
TCS34725_CONTROL          = 0x0F    # Set the gain level for the sensor
TCS34725_ID               = 0x12    # 0x44 = TCS34721/TCS34725, 0x4D = TCS34723/TCS34727
TCS34725_STATUS           = 0x13
TCS34725_STATUS_AINT      = 0x10    # RGBC Clean channel interrupt
TCS34725_STATUS_AVALID    = 0x01    # Indicates that the RGBC channels have completed an integration cycle
TCS34725_CDATAL           = 0x14    # Clear channel data
TCS34725_CDATAH           = 0x15
TCS34725_RDATAL           = 0x16    # Red channel data
TCS34725_RDATAH           = 0x17
TCS34725_GDATAL           = 0x18    # Green channel data
TCS34725_GDATAH           = 0x19
TCS34725_BDATAL           = 0x1A    # Blue channel data
TCS34725_BDATAH           = 0x1B

TCS34725_INTEGRATIONTIME_2_4MS  = 0xFF # 2.4ms - 1 cycle    - Max Count: 1024 
TCS34725_INTEGRATIONTIME_24MS   = 0xF6 # 24ms  - 10 cycles  - Max Count: 10240
TCS34725_INTEGRATIONTIME_50MS   = 0xEB # 50ms  - 20 cycles  - Max Count: 20480
TCS34725_INTEGRATIONTIME_101MS  = 0xD5 # 101ms - 42 cycles  - Max Count: 43008
TCS34725_INTEGRATIONTIME_154MS  = 0xC0 # 154ms - 64 cycles  - Max Count: 65535
TCS34725_INTEGRATIONTIME_700MS  = 0x00 # 700ms - 256 cycles - Max Count: 65535

TCS34725_GAIN_1X                = 0x00 # No gain 
TCS34725_GAIN_4X                = 0x01 # 2x gain 
TCS34725_GAIN_16X               = 0x02 # 16x gain
TCS34725_GAIN_60X               = 0x03 # 60x gain

# Bus speed for I2C communication with sensor.
# Arduino default is 100khz, but the sensor can support up to 400khz.
I2C_BUS_HZ = 100000


class FT232Hardware(object):
	"""Communicate with color sensor using FTDI FT232H or compatible hardware."""

	def __init__(self):
		# Manually calculate I2C read and write addresses for device.
		# This is necessary because the MPSSE is a low level interface
		# to the I2C bus so you need to do most of the I2C protocol manually.
		self.write_addr = TCS34725_ADDRESS << 1
		self.read_addr = self.write_addr + 1
		# Initialize MPSSE for I2C communication.
		self.mpsse = MPSSE(I2C, I2C_BUS_HZ, MSB)
		# TODO: Support multiple devices and selecting one.
		# Check communication by reading the ID of the chip.
		chip_id = self._read8(TCS34725_ID)
		if chip_id != 0x44:
			raise RuntimeError('Unexpected chip ID: 0x{0:X}'.format(chip_id))
		# Set integration time to max.
		self._write8(TCS34725_ATIME, TCS34725_INTEGRATIONTIME_700MS)
		# Set gain to 1x.
		self._write8(TCS34725_CONTROL, TCS34725_GAIN_1X)
		# Bring the chip out of low power mode and enable the color ADCs.
		self._write8(TCS34725_ENABLE, TCS34725_ENABLE_PON);
		time.sleep(0.003)
		self._write8(TCS34725_ENABLE, TCS34725_ENABLE_PON | TCS34725_ENABLE_AEN);
		
	def _write8(self, reg, val):
		"""Write a byte to the specified color sensor register."""
		if reg < 0 or reg > 127:
			raise ValueError('Register must be between 0 and 127.')
		if val < 0 or val > 255:
			raise ValueError('Value must be between 0 and 255.')
		# Send I2C write message.
		self.mpsse.Start()
		self.mpsse.Write(struct.pack('BBB', self.write_addr, TCS34725_COMMAND_BIT | reg, val))
		self.mpsse.Stop()

	def _read8(self, reg):
		"""Read a byte from the specified color sensor register."""
		if reg < 0 or reg > 127:
			raise ValueError('Register must be between 0 and 127.')
		# Make I2C combined write and read for 1 byte.
		self.mpsse.SendAcks()
		self.mpsse.Start()
		self.mpsse.Write(struct.pack('BB', self.write_addr, TCS34725_COMMAND_BIT | reg))
		self.mpsse.Start()
		self.mpsse.Write(struct.pack('B', self.read_addr))
		value = self.mpsse.Read(1)
		# Make unacknowledged read to stop.
		self.mpsse.SendNacks()
		self.mpsse.Read(1)
		self.mpsse.Stop()
		return struct.unpack('B', value)[0]

	def _read16(self, reg):
		"""Read 2 bytes from the specified color sensor register."""
		if reg < 0 or reg > 127:
			raise ValueError('Register must be between 0 and 127.')
		# Make I2C combined write and read for 2 bytes.
		self.mpsse.SendAcks()
		self.mpsse.Start()
		self.mpsse.Write(struct.pack('BB', self.write_addr, TCS34725_COMMAND_BIT | reg))
		self.mpsse.Start()
		self.mpsse.Write(struct.pack('B', self.read_addr))
		value = self.mpsse.Read(2)
		# Make unacknowledged read to stop.
		self.mpsse.SendNacks()
		self.mpsse.Read(1)
		self.mpsse.Stop()
		return struct.unpack('H', value)[0]

	def get_color(self):
		"""Return tuple of RGB color (with float components, 0-1.0) read from sensor."""
		c = self._read16(TCS34725_CDATAL);
		r = self._read16(TCS34725_RDATAL);
		g = self._read16(TCS34725_GDATAL);
		b = self._read16(TCS34725_BDATAL);
		return (float(r)/float(c), float(g)/float(c), float(b)/float(c))

	def close(self):
		"""Close the connection with the sensor hardware."""
		self.mpsse.Close()
