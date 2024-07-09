from decimal import Decimal
import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import convert_percentage_value_to_value


class TestConvertPercentageValueToValue(unittest.TestCase):

    def test_percentage_value(self):
        self.assertAlmostEqual(convert_percentage_value_to_value(60000, "10%"), 66000.0000, places=4)
        self.assertAlmostEqual(convert_percentage_value_to_value(60000, "1.5%"), 60900.0000, places=4)
        self.assertAlmostEqual(convert_percentage_value_to_value(60000, "0.5%"), 60300.0000, places=4)
        self.assertAlmostEqual(convert_percentage_value_to_value(60000, "-10%"), 54000.0000, places=4)
        self.assertAlmostEqual(convert_percentage_value_to_value(60000, "-1.5%"), 59100.0000, places=4)
        self.assertAlmostEqual(convert_percentage_value_to_value(60000, "-0.5%"), 59700.0000, places=4)
        self.assertAlmostEqual(convert_percentage_value_to_value(2.50, "10%"), 2.7500, places=4)
        self.assertAlmostEqual(convert_percentage_value_to_value(2.50, "1.5%"), 2.5375, places=4)
        self.assertAlmostEqual(convert_percentage_value_to_value(2.50, "0.5%"), 2.5125, places=4)
        self.assertAlmostEqual(convert_percentage_value_to_value(2.50, "-10%"), 2.2500, places=4)
        self.assertAlmostEqual(convert_percentage_value_to_value(2.50, "-1.5%"), 2.4625, places=4)
        self.assertAlmostEqual(convert_percentage_value_to_value(2.50, "-0.5%"), 2.4875, places=4)

    def test_decimal_value(self):
        self.assertAlmostEqual(convert_percentage_value_to_value(Decimal('0.00000906'), "10%"), Decimal('0.0000099660'), places=4)
        self.assertAlmostEqual(convert_percentage_value_to_value(Decimal('0.00000906'), "1.5%"), Decimal('0.0000091959'), places=4)
        self.assertAlmostEqual(convert_percentage_value_to_value(Decimal('0.00000906'), "-1.5%"), Decimal('0.0000089241'), places=4)
        self.assertAlmostEqual(convert_percentage_value_to_value(Decimal('0.00000906'), "0.5%"), Decimal('0.0000091053'), places=4)
        self.assertAlmostEqual(convert_percentage_value_to_value(Decimal('0.00000906'), "-0.5%"), Decimal('0.0000090147'), places=4)

    def test_exact_value(self):
        self.assertAlmostEqual(convert_percentage_value_to_value(60000, "70000"), 70000.0000, places=4)
        self.assertAlmostEqual(convert_percentage_value_to_value(60000, "-58000"), -58000.0000, places=4)

    def test_no_value(self):
        self.assertIsNone(convert_percentage_value_to_value(60000, None))
        self.assertIsNone(convert_percentage_value_to_value(60000, ""))


if __name__ == '__main__':
    unittest.main()
