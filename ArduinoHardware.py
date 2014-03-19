import logging
import time

import serial


log = logging.getLogger(__name__)


class ArduinoHardware(object):
	"""Communicate with color sensor attached to an Arduino on a serial port."""

	def __init__(self, port):
		# Open the serial connection.
		self.serial = serial.Serial(port, 115200, timeout=5)
		# Wait a few seconds for the Arduino to reset and swallow any data
		# received.  This is necessary because the color sensor Arduino library
		# writes some data to serial on startup and will interfere with later calls.
		time.sleep(3.0)
		self.serial.flushInput()

	def get_color(self):
		"""Return tuple of RGB color (with float components, 0-1.0) read from Arduino."""
		# Clear input buffer and send a question mark character.
		self.serial.flushInput()
		self.serial.write('?')
		self.serial.flush()
		log.info('Sent question command.')
		# Parse the response line for 3 color components.
		line = self.serial.readline()
		if line is None:
			raise RuntimeError('Received no data from serial readline().')
		components = line.strip().split(',')
		if components is None or len(components) != 3:
			raise RuntimeError('Error parsing response line: {0}'.format(line))
		# Return RGB values.
		r = float(components[0])
		g = float(components[1])
		b = float(components[2])
		return (r, g, b)

	def close(self):
		"""Close the connection with the sensor hardware."""
		self.serial.close()
