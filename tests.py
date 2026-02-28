import unittest
from bet_parser import get_coef
from prizm_api import prizm_amount
from marathon_parser_real import parse_2way_winner

class TestPrizmBet(unittest.TestCase):
    def test_get_coef_flat(self):
        match = {"id": "123", "p1": "1.50", "x": "3.40", "p2": "2.10"}
        self.assertEqual(get_coef(match, "П1"), 1.50)
        self.assertEqual(get_coef(match, "X"), 3.40)
        self.assertEqual(get_coef(match, "П2"), 2.10)

    def test_get_coef_legacy(self):
        match = {"id": "123", "odds": {"1": 1.6, "X": 3.5, "2": 2.2}}
        self.assertEqual(get_coef(match, "П1"), 1.60)
        self.assertEqual(get_coef(match, "X"), 3.50)
        self.assertEqual(get_coef(match, "П2"), 2.20)

    def test_get_coef_mixed(self):
        # Flat should take priority
        match = {"id": "123", "p1": "1.70", "odds": {"1": 1.6}}
        self.assertEqual(get_coef(match, "П1"), 1.70)

    def test_prizm_amount(self):
        # 1 PRIZM = 100,000,000 NQT
        tx = {"amountNQT": "100000000"}
        self.assertEqual(prizm_amount(tx), 1.0)
        tx = {"amountNQT": "550000000"}
        self.assertEqual(prizm_amount(tx), 5.5)
        tx = {"amountNQT": "100"}
        self.assertEqual(prizm_amount(tx), 0.000001)

    def test_parse_2way_winner_regression(self):
        # Simple regression test for the parser logic (mocking HTML would be better but this is a start)
        html = """
        <div class="coupon-row" data-event-id="123" data-event-name="Team A - Team B">
            <div class="date">14:00</div>
            <a class="member-link" href="/betting/1">Team A</a>
            <a class="member-link" href="/betting/2">Team B</a>
            <div class="selection-link" data-selection-key="Match_Result.1">1.50</div>
            <div class="selection-link" data-selection-key="Match_Result.3">2.50</div>
        </div>
        """
        results = parse_2way_winner(html, "tennis")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["team1"], "Team A")
        self.assertEqual(results[0]["team2"], "Team B")
        self.assertEqual(results[0]["p1"], "1.5")
        self.assertEqual(results[0]["p2"], "2.5")
        self.assertEqual(results[0]["x"], "—")

if __name__ == "__main__":
    unittest.main()
