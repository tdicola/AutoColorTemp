import unittest

import AutoColorTemp


class MockColorHardware(object):
	def __init__(self, color=(0, 0, 0)):
		self.color = color
		self.get_color_called = False
		self.close_called = False

	def get_color(self):
		self.get_color_called = True
		return self.color

	def close(self):
		self.close_called = True


class MockGammaAdjust(object):
	def __init__(self):
		self.white = None
		self.restore_called = False

	def adjust_white_point(self, white):
		self.white = white

	def restore(self):
		self.restore_called = True


class TestAutoColorTemp(unittest.TestCase):

	def test_update_gets_color_and_updates_gamma(self):
		color = (1.0, 0.5, 0.0)
		hardware = MockColorHardware(color)
		gamma = MockGammaAdjust()
		main = AutoColorTemp.AutoColorTemp(hardware, gamma)

		main.update()

		self.assertTrue(hardware.get_color_called)
		self.assertEqual(color, gamma.white)

	def test_close_restores_gamma(self):
		hardware = MockColorHardware()
		gamma = MockGammaAdjust()
		main = AutoColorTemp.AutoColorTemp(hardware, gamma)

		self.assertFalse(gamma.restore_called)

		main.close()

		self.assertTrue(gamma.restore_called)

	def test_close_closes_hardware(self):
		hardware = MockColorHardware()
		gamma = MockGammaAdjust()
		main = AutoColorTemp.AutoColorTemp(hardware, gamma)

		self.assertFalse(hardware.close_called

		main.close()

		self.assertTrue(hardware.close_called)

	def test_rgb_to_temp(self):
		# Pure white RGB should be 6500K temperature.
		temp = AutoColorTemp._rgb_to_temp(1.0, 1.0, 1.0)

		self.assertGreater(temp, 6499.0)
		self.assertLess(temp, 6501.0)

	def test_temp_to_white(self):
		# Verify that 5000K is close to pure white (because sRGB color space is used with D50 white point).
		white = AutoColorTemp._temp_to_white(5000.0)

		self.assertGreaterEqual(white[0], 0.99)
		self.assertGreaterEqual(white[1], 0.99)
		self.assertGreaterEqual(white[2], 0.99)
		self.assertLessEqual(white[0], 1.0)
		self.assertLessEqual(white[1], 1.0)
		self.assertLessEqual(white[2], 1.0)

	def test_gamma_table_gen(self):
		ramp = [x for x in AutoColorTemp.gamma_table_gen(256, 0.5, 2.2)]

		# Verify correct number of generated values.
		self.assertEqual(len(ramp), 256)
		# Verify min and max are 0 and white value respectively.
		self.assertEqual(ramp[0], 0.0)
		self.assertEqual(ramp[255], 0.5)
		# Verify intermediate values are an increasing curve.
		for i in range(1, 256):
			self.assertGreater(ramp[i], ramp[i-1])
