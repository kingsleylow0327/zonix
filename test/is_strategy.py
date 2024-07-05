import unittest
import json
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import is_strategy

class TestIsStrategy(unittest.TestCase):

    def setUp(self):
        self.success_regex = [
            "!BETA #10% BTCUSDT [Buy] $60000 -1.5% +3% /62000 >0.5%",     # Full command
            "!BETA #10.5% BTCUSDT [Buy] $60000 -1.5% +3% /62000 >0.5%",   # Wallet Margin with decimals
            "!BETA #10% btcusdt [Buy] $60000 -1.5% +3% /62000 >0.5%",     # Lower case Trading Pair
            "!BETA #10% BtcUsdt [Buy] $60000 -1.5% +3% /62000 >0.5%",     # Camel case Trading Pair
            "!BETA #10% BTCUSDT [buy] $60000 -1.5% +3% /62000 >0.5%",     # Lower case Action
            "!BETA #10% BTCUSDT [Sell] $60000 -1.5% +3% /62000 >0.5%",    # Sell Action
            "!BETA #10% BTCUSDT [Buy] $60000.50 -1.5% +3% /62000 >0.5%",  # Entry Price with decimals
            "!BETA #10% BTCUSDT [Buy] $60000 -1% +3% /62000 >0.5%",       # Stop Lost without decimal
            "!BETA #10% BTCUSDT [Buy] $60000 -50000 +3% /62000 >0.5%",    # Stop Lost (Whole Number)
            "!BETA #10% BTCUSDT [Buy] $60000 -50000.50 +3% /62000 >0.5%", # Stop Lost (Decimals)
            "!BETA #10% BTCUSDT [Buy] $60000 -1.5% +3.5% /62000 >0.5%",   # Take Profit with decimals
            "!BETA #10% BTCUSDT [Buy] $60000 -1.5% +70000 /62000 >0.5%",  # Take Profit (Whole Number)
            "!BETA #10% BTCUSDT [Buy] $60000 -1.5% +70000.50 /62000 >0.5%",# Take Profit (Decimals)
            "!BETA #10% BTCUSDT [Buy] $60000 -1.5% /62000 >0.5%",         # Take Profit (Remove)
            "!BETA #10% BTCUSDT [Buy] $60000 -1.5% +3% /62000 >5%",       # Trailing Stop Percentage (Whole Number)
        ]
        
        self.fail_regex = [
            "!BETA #10% BTCUSDT [Buy] 60000 -1.5% +5 /62000 >0.5%",       # Entry Price without $
            "!BETA #10% BTCUSDT [Buy] $60000 1.5% /62000 >0.5%",          # Stop Lost without -
            "!BETA #10% BTCUSDT [Buy] $60000 -1.5% 3% /62000 >0.5%",      # Take Profit without +
            "!BETA #10% BTCUSDT [Buy] $60000 -1.5% +3% 62000 >0.5%",      # Trailing Stop Price without /
            "!BETA #10% BTCUSDT [Buy] $60000 -1.5% +3% /62000 0.5%",      # Trailing Stop Percentage without >
            "!BETA #10% BTCUSDT [Buy] $60000 -1.5% +3% /62000 >0.5",      # Trailing Stop Percentage without %
        ]

    def test_success_regex(self):
        for regex in self.success_regex:
            with self.subTest(regex=regex):
                match = is_strategy(regex)
                self.assertIsNotNone(match, f"Failed to parse formula: {regex}")

    def test_fail_regex(self):
        for regex in self.fail_regex:
            with self.subTest(regex=regex):
                match = is_strategy(regex)
                self.assertEqual(match, False, f"Should not have parsed formula: {regex}")

if __name__ == "__main__":
    unittest.main()