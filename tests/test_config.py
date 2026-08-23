import unittest

from main import produkt_soll_aktiviert


class ProduktAktivierungTest(unittest.TestCase):
    def test_deaktiviert_per_config_flag(self):
        self.assertFalse(produkt_soll_aktiviert({"aktiviert": False}))

    def test_aktiviert_per_default(self):
        self.assertTrue(produkt_soll_aktiviert({}))

    def test_deaktiviert_per_enabled_flag(self):
        self.assertFalse(produkt_soll_aktiviert({"enabled": False}))


if __name__ == "__main__":
    unittest.main()
