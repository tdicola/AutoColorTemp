from ctypes import *
import logging

from AutoColorTemp import gamma_table_gen


log = logging.getLogger(__name__)

# Windows color system reference: 
#  http://msdn.microsoft.com/en-us/library/windows/desktop/dd371793(v=vs.85).aspx

USHORT_MAX = 65535
RAMP_SIZE = 256


class Win32Gamma(object):
	"""Adjust color temperature of main display on Windows."""

	def __init__(self):
		# Get DC for primary display.
		self.dc = windll.user32.GetDC(None)
		# TODO: Support multiple monitors.
		# Save current gamma ramps.
		self.gamma_ramp = c_ushort * (RAMP_SIZE * 3)
		self.old_ramp = self.gamma_ramp()
		if not windll.gdi32.GetDeviceGammaRamp(self.dc, byref(self.old_ramp)):
			raise RuntimeError('GetDeviceGammaRamp failed.')
		# Set default gamma.
		self.gamma = (2.2, 2.2, 2.2)

	def set_gamma(self, gamma):
		"""Change RGB gamma value used in computation of gamma ramp. Should be a tuple
		of three float values (one for each channel).  Default gamma is 1.0 (no gamma)."""
		self.gamma = gamma

	def adjust_white_point(self, white):
		"""Change the white point of the monitor to the specified value (tuple of 
		RGB floats, 0-1.0)."""
		# Allocate gamma ramps.
		ramp = self.gamma_ramp()
		# Fill gamma ramps.
		for c in range(3):
			for i, value in enumerate(gamma_table_gen(RAMP_SIZE, white[c], self.gamma[c])):
				ramp[i + 256*c] = c_ushort(int(USHORT_MAX*value))
		# Set gamma ramps.
		windll.gdi32.SetDeviceGammaRamp(self.dc, byref(ramp))

	def restore(self):
		"""Restore gamma back to original value."""
		windll.gdi32.SetDeviceGammaRamp(self.dc, byref(self.old_ramp))
