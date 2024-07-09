import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import is_strategy


class TestIsStrategy(unittest.TestCase):

    def setUp(self):
        self.success_regex = [
            "!BETA #10% BTCUSDT [Buy] $60000 -1.5% +3% /62000 >0.5%",         # Full command
            "!BETA #10.50% BTCUSDT [Buy] $60000 -1.5% +3% /62000 >0.5%",      # Wallet Margin - With decimals
            "!BETA #10% btcusdt [Buy] $60000 -1.5% +3% /62000 >0.5%",         # Trading Pair - Lower case
            "!BETA #10% BtcUsdt [Buy] $60000 -1.5% +3% /62000 >0.5%",         # Trading Pair - Camel case
            "!BETA #10% BTCUSDT [buy] $60000 -1.5% +3% /62000 >0.5%",         # Order Action - Lower case
            "!BETA #10% BTCUSDT [Sell] $60000 -1.5% +3% /62000 >0.5%",        # Order Action - Sell
            "!BETA #10% BTCUSDT [Buy] $60000.50 -1.5% +3% /62000 >0.5%",      # Entry Price - With decimals
            "!BETA #10% BTCUSDT [Buy] $60000 -1% +3% /62000 >0.5%",           # Stop Lost - Without decimal
            "!BETA #10% BTCUSDT [Buy] $60000 -50000 +3% /62000 >0.5%",        # Stop Lost - Price
            "!BETA #10% BTCUSDT [Buy] $60000 -50000.50 +3% /62000 >0.5%",     # Stop Lost - Price with decimals
            "!BETA #10% BTCUSDT [Buy] $60000 -1.5% +3.5% /62000 >0.5%",       # Take Profit - With decimals
            "!BETA #10% BTCUSDT [Buy] $60000 -1.5% +70000 /62000 >0.5%",      # Take Profit - Price
            "!BETA #10% BTCUSDT [Buy] $60000 -1.5% +70000.50 /62000 >0.5%",   # Take Profit - Price with decimals
            "!BETA #10% BTCUSDT [Buy] $60000 -1.5% /62000 >0.5%",             # Take Profit - Optional
            "!BETA #10% BTCUSDT [Buy] $60000 -55000 +70000 /62000 >0.5%",     # Stop Lost & Take Profit - Price
            "!BETA #10% BTCUSDT [Buy] $60000 -55000.50 +70000.50 /62000 >0.5%",# Stop Lost & Take Profit - Price with decimals
            "!BETA #10% BTCUSDT [Buy] $60000 -1.5% +3% /62000 >5%",           # Trailing Stop Percentage - Whole Number
        ]

        self.fail_regex = [
            "!BETA 10% BTCUSDT [Buy] $60000 -1.5% +3% /62000 >0.5%",      # Wallet Margin - Without start with #
            "!BETA #10 BTCUSDT [Buy] $60000 -1.5% +3% /62000 >0.5%",      # Wallet Margin - Without end with %
            "!BETA #10% BTCUSDT [Buy] 60000 -1.5% +5 /62000 >0.5%",       # Entry Price - Without $
            "!BETA #10% BTCUSDT [Buy] $60000 1.5% /62000 >0.5%",          # Stop Lost - Without -
            "!BETA #10% BTCUSDT [Buy] $60000 -1.5% 3% /62000 >0.5%",      # Take Profit - Without +
            "!BETA #10% BTCUSDT [Buy] $60000 -1.5% +3% 62000 >0.5%",      # Trailing Stop Price - Without /
            "!BETA #10% BTCUSDT [Buy] $60000 -1.5% +3% /62000 0.5%",      # Trailing Stop Percentage - Without start with >
            "!BETA #10% BTCUSDT [Buy] $60000 -1.5% +3% /62000 >0.5",      # Trailing Stop Percentage - Without end with %
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
                self.assertIsNone(match, f"Should not have parsed formula: {regex}")


if __name__ == "__main__":
    unittest.main()
