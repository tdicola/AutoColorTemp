from __future__ import print_function
import logging
import math

from colormath.color_objects import RGBColor, xyYColor


log = logging.getLogger(__name__)


def _rgb_to_temp(r, g, b):
	"""Convert RGB color (with float components, 0-1.0) to color temperature."""
	# First convert RGB to xyY color space.
	x, y, Y = RGBColor(r, g, b).convert_to('xyy').get_value_tuple()
	# Assume 3k - 50k Kelvin range and solve equation to convert xyY to color
	# temperature.  Equation from:
	#   http://en.wikipedia.org/wiki/Color_temperature#Approximation
	xe = 0.3366
	ye = 0.1735
	A0 = -949.86315
	A1 = 6253.80338
	t1 = 0.92159
	A2 = 28.70599
	t2 = 0.20039
	A3 = 0.00004
	t3 = 0.07125
	n = (x - xe)/(y - ye)
	kelvin = A0 + A1*math.exp(-n/t1) + A2*math.exp(-n/t2) + A3*math.exp(-n/t3)
	return kelvin

def _temp_to_white(t):
	"""Convert color temperature to sRGB white point tuple."""
	# Use equation from:
	#   http://en.wikipedia.org/wiki/Planckian_locus#Approximation
	xc = 0.0
	if 1667.0 <= t and t <= 4000.0:
		xc = -0.2661239*(math.pow(10.0, 9.0)/math.pow(t, 3.0)) - 0.2343580*(math.pow(10.0, 6.0)/math.pow(t, 2.0)) + 0.8776956*(math.pow(10.0, 3.0)/float(t)) + 0.179910
	elif 4000 < t and t <= 25000.0:
		xc = -3.0258469*(math.pow(10.0, 9.0)/math.pow(t, 3.0)) + 2.1070379*(math.pow(10.0, 6.0)/math.pow(t, 2.0)) + 0.2226347*(math.pow(10.0, 3.0)/float(t)) + 0.240390
	else:
		raise ValueError('Temperature must be between 1667K and 25000K.')
	yc = 0.0
	if 1667.0 <= t and t <= 2222.0:
		yc = -1.1063814*math.pow(xc, 3.0) - 1.34811020*math.pow(xc, 2.0) + 2.18555832*xc - 0.20219683
	elif 2222.0 < t and t <= 4000.0:
		yc = -0.9549476*math.pow(xc, 3.0) - 1.37418593*math.pow(xc, 2.0) + 2.09137015*xc - 0.16748867
	elif 4000.0 < t and t <= 25000.0:
		yc =  3.0817580*math.pow(xc, 3.0) - 5.87338670*math.pow(xc, 2.0) + 3.75112997*xc - 0.37001483
	# Covert from full bright xyY color space to RGB (sRGB default) for white point at specified temp.
	white = xyYColor(xc, yc, 1.0).convert_to('rgb').get_value_tuple()
	# Return values normalized to 0-1.0 range.
	return (white[0] / 255.0, white[1] / 255.0, white[2] / 255.0)

def gamma_table_gen(size, white, gamma):
	"""Generator function to build a gamma ramp of the given size, white point, and gamma."""
	for i in range(size):
		yield math.pow(float(i)/float(size-1), 1.0/float(gamma)) * float(white)


class AutoColorTemp(object):
	"""Main logic to query the color sensor and update monitor color temperature."""
	
	def __init__(self, hardware, gamma):
		self.hardware = hardware
		self.gamma = gamma

	def update(self):
		"""Query color sensor hardware and update monitor color temperature."""
		# First measure the color from the sensor.
		measured = self.hardware.get_color()
		log.info('Read color from hardware: red={0} green={1} blue={2}'.format(measured[0], measured[1], measured[2]))
		# Compute temperature of measured color.
		temp = _rgb_to_temp(measured[0], measured[1], measured[2])
		print('Measured color temperature: {0:,.0f} kelvin'.format(temp))
		# Adjust monitor color temperature if within range of allowed temps.
		if 1667.0 <= temp and temp <= 25000.0:
			white = _temp_to_white(temp)
			log.info('Computed white point: red={0} green={1} blue={2}'.format(white[0], white[1], white[2]))
			self.gamma.adjust_white_point(white)

	def close(self):
		"""Restore gamma to original value and close hardware connection."""
		log.info('Restoring gamma.')
		self.gamma.restore()
		log.info('Closing hardware connection.')
		self.hardware.close()
