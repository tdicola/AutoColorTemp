from ctypes import *
from ctypes.util import find_library
import logging

from AutoColorTemp import gamma_table_gen


log = logging.getLogger(__name__)

# X11 references: 
#  http://www.x.org/releases/current/doc/libX11/libX11/libX11.html
#  http://www.x.org/releases/current/doc/man/man3/XF86VM.3.xhtml
Xlib = CDLL(find_library('X11'))

Xf86vm = CDLL(find_library('Xxf86vm'))

USHORT_MAX = 65535


class X11Gamma(object):
	"""Adjust color temperature of main display on X11/Linux."""

	def __init__(self):
		# Save the current display and screen ID.
		self.display = Xlib.XOpenDisplay(None)
		self.screen = Xlib.XDefaultScreen(self.display)
		log.info('XDefaultScreen returned screen ID: {0}'.format(self.screen))
		# TODO: Support multiple monitors.
		# Save size of gamma ramp.
		self.ramp_size = c_int(0)
		Xf86vm.XF86VidModeGetGammaRampSize(self.display, self.screen, byref(self.ramp_size))
		if self.ramp_size.value == 0:
			raise RuntimeError('Could not read size of X11 gamma ramp.')
		# Save current gamma ramps.
		self.gamma_ramp = c_ushort * self.ramp_size.value
		self.old_red = self.gamma_ramp()
		self.old_green = self.gamma_ramp()
		self.old_blue = self.gamma_ramp()
		Xf86vm.XF86VidModeGetGammaRamp(self.display, self.screen, self.ramp_size, 
			byref(self.old_red), byref(self.old_green), byref(self.old_blue))
		# Default to gamma of 1.0 (no gamma adjustment).
		# For some reason I found the gamma ramp returned by X11 (Ubuntu 12.04) 
		# doesn't seem to apply any gamma adjustment and looks washed out when 
		# typical gamma of 2.2 or so is applied.
		self.gamma = (1.0, 1.0, 1.0)

	def set_gamma(self, gamma):
		"""Change RGB gamma value used in computation of gamma ramp. Should be a tuple
		of three float values (one for each channel).  Default gamma is 1.0 (no gamma)."""
		self.gamma = gamma

	def adjust_white_point(self, white):
		"""Change the white point of the monitor to the specified value (tuple of 
		RGB floats, 0-1.0)."""
		# Allocate gamma ramps.
		red = self.gamma_ramp()
		green = self.gamma_ramp()
		blue = self.gamma_ramp()
		# Fill ramps with values.
		size = self.ramp_size.value
		for i, value in enumerate(gamma_table_gen(size, white[0], self.gamma[0])):
			red[i] = c_ushort(int(USHORT_MAX*value))
		for i, value in enumerate(gamma_table_gen(size, white[1], self.gamma[1])):
			green[i] = c_ushort(int(USHORT_MAX*value))
		for i, value in enumerate(gamma_table_gen(size, white[2], self.gamma[2])):
			blue[i] = c_ushort(int(USHORT_MAX*value))
		# Set gamma ramps.
		Xf86vm.XF86VidModeSetGammaRamp(self.display, self.screen, self.ramp_size, 
			byref(red), byref(green), byref(blue))

	def restore(self):
		"""Restore gamma back to original value."""
		Xf86vm.XF86VidModeSetGammaRamp(self.display, self.screen, self.ramp_size, 
			byref(self.old_red), byref(self.old_green), byref(self.old_blue))
