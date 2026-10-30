"""Domain classes for MessFinder - mirror the UML class diagram."""
from abc import ABC
from datetime import date
from itertools import count

_ids = count(1)


class User(ABC):
    def __init__(self, name, email):
        self.user_id, self.name, self.email = next(_ids), name, email
        self.logged_in = False

    def login(self):
        self.logged_in = True
        return True

    def logout(self):
        self.logged_in = False


class Preference:
    def __init__(self, max_budget=4000, max_distance_km=2.0, food_type="Any", meals_per_day=2):
        self.max_budget, self.max_distance_km = max_budget, max_distance_km
        self.food_type, self.meals_per_day = food_type, meals_per_day

    def score(self, mess):
        """Match score 0-100: price 35, distance 25, food type 20, meals 10, rating 10."""
        price = 35 if mess.monthly_price <= self.max_budget else max(0, 35 - 35 * (mess.monthly_price - self.max_budget) / self.max_budget * 3)
        dist = 25 if mess.distance_km <= self.max_distance_km else max(0, 25 - 25 * (mess.distance_km - self.max_distance_km) / max(self.max_distance_km, 0.5))
        food = 20 if self.food_type in ("Any", mess.food_type) else 0
        meals = 10 if mess.meals_per_day >= self.meals_per_day else 0
        rating = mess.avg_rating() / 5 * 10
        return round(price + dist + food + meals + rating, 1)


class Student(User):
    def __init__(self, name, email, university="Campus University", batch_year=2026):
        super().__init__(name, email)
        self.university, self.batch_year = university, batch_year
        self.preference = Preference()

    def search_mess(self, messes, pref=None):
        pref = pref or self.preference
        approved = [m for m in messes if m.status == "approved"]
        return sorted(((pref.score(m), m) for m in approved), key=lambda t: -t[0])

    def write_review(self, mess, food, hygiene, service, value, comment):
        r = Review(self, food, hygiene, service, value, comment)
        mess.add_review(r)
        return r

    def request_subscription(self, mess, meal_plan):
        s = Subscription(self, mess, meal_plan)
        mess.subscriptions.append(s)
        return s


class MessOwner(User):
    def __init__(self, name, email, phone=""):
        super().__init__(name, email)
        self.phone, self.messes = phone, []

    def add_mess(self, *args, **kw):
        m = Mess(self, *args, **kw)
        self.messes.append(m)
        return m

    def decide_subscription(self, sub, approve=True):
        sub.approve() if approve else sub.cancel()


class Admin(User):
    def approve_mess(self, mess):
        mess.status = "approved"

    def moderate_review(self, mess, review):
        mess.reviews.remove(review)


class WeeklyMenu:
    def __init__(self, day, meal_type, items):
        self.menu_id, self.day, self.meal_type, self.items = next(_ids), day, meal_type, items

    def get_menu(self):
        return f"{self.day} {self.meal_type}: {self.items}"


class Review:
    def __init__(self, student, food, hygiene, service, value, comment):
        self.review_id, self.student = next(_ids), student
        self.food, self.hygiene, self.service, self.value = food, hygiene, service, value
        self.comment, self.date = comment, date.today()

    def overall(self):
        return (self.food + self.hygiene + self.service + self.value) / 4


class Subscription:
    def __init__(self, student, mess, meal_plan):
        self.sub_id, self.student, self.mess, self.meal_plan = next(_ids), student, mess, meal_plan
        self.start_date, self.status = date.today(), "pending"

    def approve(self):
        self.status = "approved"

    def cancel(self):
        self.status = "cancelled"


class Mess:
    def __init__(self, owner, name, address, distance_km, monthly_price, food_type, meals_per_day, status="pending"):
        self.mess_id, self.owner, self.name, self.address = next(_ids), owner, name, address
        self.distance_km, self.monthly_price, self.food_type = distance_km, monthly_price, food_type
        self.meals_per_day, self.status = meals_per_day, status
        self.menu, self.reviews, self.subscriptions = [], [], []

    def add_review(self, review):
        self.reviews.append(review)

    def avg_rating(self):
        return sum(r.overall() for r in self.reviews) / len(self.reviews) if self.reviews else 3.0
