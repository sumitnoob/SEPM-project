"""Unit tests - run: python3 -m unittest -v"""
import unittest
from models import *


class TestMessFinder(unittest.TestCase):
    def setUp(self):
        self.owner = MessOwner("Owner", "o@x.com")
        self.student = Student("Stu", "s@x.com")
        self.good = self.owner.add_mess("Good", "A", 0.5, 3000, "Halal", 3, "approved")
        self.far = self.owner.add_mess("Far", "B", 5.0, 6000, "Mixed", 1, "approved")
        self.hidden = self.owner.add_mess("Hidden", "C", 0.5, 3000, "Halal", 3, "pending")

    def test_user_login_logout(self):
        self.assertTrue(self.student.login()); self.assertTrue(self.student.logged_in)
        self.student.logout(); self.assertFalse(self.student.logged_in)

    def test_score_perfect_match_is_high(self):
        p = Preference(4000, 1.0, "Halal", 2)
        self.assertGreaterEqual(p.score(self.good), 90)

    def test_score_penalises_price_distance_and_food(self):
        p = Preference(4000, 1.0, "Halal", 2)
        self.assertLess(p.score(self.far), p.score(self.good))

    def test_food_type_any_matches_everything(self):
        self.assertEqual(Preference(4000, 1, "Any", 1).score(self.good) - Preference(4000, 1, "Halal", 1).score(self.good), 0)

    def test_search_ranks_and_hides_unapproved(self):
        res = self.student.search_mess([self.good, self.far, self.hidden], Preference(4000, 1.0, "Halal", 2))
        self.assertEqual([m for _, m in res], [self.good, self.far])

    def test_review_overall_and_average(self):
        self.student.write_review(self.good, 5, 5, 5, 5, "great")
        self.student.write_review(self.good, 3, 3, 3, 3, "ok")
        self.assertEqual(self.good.avg_rating(), 4.0)
        self.assertEqual(self.good.reviews[0].overall(), 5)

    def test_no_reviews_default_rating(self):
        self.assertEqual(self.good.avg_rating(), 3.0)

    def test_subscription_workflow(self):
        sub = self.student.request_subscription(self.good, "Lunch")
        self.assertEqual(sub.status, "pending")
        self.owner.decide_subscription(sub, True); self.assertEqual(sub.status, "approved")
        sub2 = self.student.request_subscription(self.good, "Dinner")
        self.owner.decide_subscription(sub2, False); self.assertEqual(sub2.status, "cancelled")

    def test_admin_approve_and_moderate(self):
        admin = Admin("A", "a@x.com"); admin.approve_mess(self.hidden)
        self.assertEqual(self.hidden.status, "approved")
        r = self.student.write_review(self.hidden, 1, 1, 1, 1, "spam")
        admin.moderate_review(self.hidden, r); self.assertEqual(self.hidden.reviews, [])

    def test_weekly_menu_text(self):
        self.assertEqual(WeeklyMenu("Sunday", "Lunch", "Rice").get_menu(), "Sunday Lunch: Rice")


if __name__ == "__main__":
    unittest.main()
