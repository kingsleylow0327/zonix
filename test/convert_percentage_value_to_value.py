import unittest

from app import convert_percentage_value_to_value


class TestConvertPercentageValueToValue(unittest.TestCase):

    def test_percentage_value(self):
        self.assertAlmostEqual(convert_percentage_value_to_value(60000, "10%"), 66000, places=5)
        self.assertAlmostEqual(convert_percentage_value_to_value(60000, "1.5%"), 60900, places=5)
        self.assertAlmostEqual(convert_percentage_value_to_value(60000, "0.5%"), 60300, places=5)
        self.assertAlmostEqual(convert_percentage_value_to_value(60000, "-10%"), 54000, places=5)
        self.assertAlmostEqual(convert_percentage_value_to_value(60000, "-1.5%"), 59100, places=5)
        self.assertAlmostEqual(convert_percentage_value_to_value(60000, "-0.5%"), 59700, places=5)
        self.assertAlmostEqual(convert_percentage_value_to_value(2.50, "10%"), 2.75, places=5)
        self.assertAlmostEqual(convert_percentage_value_to_value(2.50, "1.5%"), 2.5375, places=5)
        self.assertAlmostEqual(convert_percentage_value_to_value(2.50, "0.5%"), 2.5125, places=5)
        self.assertAlmostEqual(convert_percentage_value_to_value(2.50, "-10%"), 2.25, places=5)
        self.assertAlmostEqual(convert_percentage_value_to_value(2.50, "-1.5%"), 2.4625, places=5)
        self.assertAlmostEqual(convert_percentage_value_to_value(2.50, "-0.5%"), 2.4875, places=5)

    def test_exact_value(self):
        self.assertAlmostEqual(convert_percentage_value_to_value(60000, "70000"), 70000, places=5)
        self.assertAlmostEqual(convert_percentage_value_to_value(60000, "-58000"), -58000, places=5)

    def test_no_value(self):
        self.assertIsNone(convert_percentage_value_to_value(60000, None))
        self.assertIsNone(convert_percentage_value_to_value(60000, ""))


if __name__ == '__main__':
    unittest.main()