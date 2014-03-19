from ctypes import *
from ctypes.util import find_library
import logging


log = logging.getLogger(__name__)

# Quartz reference: 
#  https://developer.apple.com/library/mac/documentation/GraphicsImaging/Reference/Quartz_Services_Ref/Reference/reference.html
quartz = CDLL(find_library('ApplicationServices'))


class MacOSXGamma(object):
	"""Adjust color temperature of main display on MacOS X."""

	def __init__(self):
		# Save the current display ID.
		self.display = quartz.CGMainDisplayID()
		log.info('CGMainDisplayID returned display ID: {0}'.format(self.display))
		# TODO: Support multiple monitors.
		# Default to gamma of 1.8.
		self.gamma = (1.8, 1.8, 1.8)

	def set_gamma(self, gamma):
		"""Change RGB gamma value used in computation of gamma ramp. Should be a tuple
		of three float values (one for each channel).  Default gamma is 1.8."""
		self.gamma = gamma

	def adjust_white_point(self, white):
		"""Change the white point of the monitor to the specified value (tuple of 
		RGB floats, 0-1.0)."""
		# Set gamma ramp parameters.
		redMin = c_float(0.0)
		redMax = c_float(white[0])
		redGamma = c_float(self.gamma[0])
		greenMin = c_float(0.0)
		greenMax = c_float(white[1])
		greenGamma = c_float(self.gamma[1])
		blueMin = c_float(0.0)
		blueMax = c_float(white[2])
		blueGamma = c_float(self.gamma[2])
		# Update gamma ramp.
		result = quartz.CGSetDisplayTransferByFormula(self.display,
			redMin, redMax, redGamma,
			greenMin, greenMax, greenGamma,
			blueMin, blueMax, blueGamma)
		if result != 0:
			raise RuntimeError('Error calling CGSetDisplayTransferByFormula with error code: {0}'.format(result))

	def restore(self):
		"""Restore gamma back to original value."""
		quartz.CGDisplayRestoreColorSyncSettings()
