"""MessFinder prototype - run: python3 app.py  then open http://localhost:8000"""
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from html import escape
from models import *

# ---------- seed data ----------
admin = Admin("Admin", "admin@messfinder.app")
owner1 = MessOwner("Karim Uddin", "karim@mail.com", "01700-000001")
owner2 = MessOwner("Salma Begum", "salma@mail.com", "01700-000002")
me = Student("Rahim (demo student)", "rahim@campus.edu")
MESSES = [
    owner1.add_mess("Green Bite Mess", "Road 4, Near Gate 1", 0.8, 3200, "Halal", 3, "approved"),
    owner1.add_mess("Campus Corner Mess", "Market Road", 2.4, 4000, "Mixed", 3, "approved"),
    owner2.add_mess("Veggie Delight Mess", "Lake Side", 1.2, 2800, "Vegetarian", 2, "approved"),
    owner2.add_mess("Budget Plate Mess", "Old Town", 3.0, 2200, "Halal", 2, "approved"),
    owner2.add_mess("New Hidden Mess", "Unverified", 1.0, 2500, "Halal", 2, "pending"),
]
for m, rows in zip(MESSES, [
    [("Sunday", "Lunch", "Rice, Chicken Curry, Dal"), ("Sunday", "Dinner", "Khichuri, Egg")],
    [("Sunday", "Lunch", "Rice, Beef, Mixed Veg")],
    [("Sunday", "Lunch", "Rice, Paneer, Salad")],
    [("Sunday", "Lunch", "Rice, Fish, Dal")], []]):
    m.menu = [WeeklyMenu(*r) for r in rows]
Student("Nila", "nila@campus.edu").write_review(MESSES[0], 4, 5, 4, 5, "Clean and tasty, good portions.")
Student("Arif", "arif@campus.edu").write_review(MESSES[0], 5, 4, 4, 4, "Reliable every day.")
Student("Tania", "tania@campus.edu").write_review(MESSES[1], 3, 3, 4, 2, "A bit expensive for the quality.")
Student("Sumon", "sumon@campus.edu").write_review(MESSES[2], 4, 5, 5, 4, "Great for vegetarians.")
me.login()

# ---------- views ----------
def page(body):
    return f"""<!doctype html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>MessFinder</title><style>
body{{font-family:system-ui,sans-serif;max-width:860px;margin:0 auto;padding:16px;background:#fafafa;color:#222}}
header{{background:#2e7d32;color:#fff;padding:14px 18px;border-radius:10px;margin-bottom:16px}} header a{{color:#fff;text-decoration:none;font-size:22px;font-weight:700}}
.card{{background:#fff;border:1px solid #ddd;border-radius:10px;padding:14px;margin:10px 0}} .score{{float:right;background:#2e7d32;color:#fff;border-radius:20px;padding:4px 12px;font-weight:700}}
form.grid>div{{display:inline-block;width:185px;vertical-align:top;margin:4px}} label{{font-size:13px;display:block}} input,select,textarea{{width:100%;padding:7px;box-sizing:border-box}}
button{{background:#2e7d32;color:#fff;border:0;padding:9px 16px;border-radius:6px;cursor:pointer}} .muted{{color:#666;font-size:14px}}
</style></head><body><header><a href="/">🍽 MessFinder</a><span style="float:right">Logged in: {escape(me.name)}</span></header>{body}</body></html>"""

def home(q):
    g = lambda k, d: q.get(k, [d])[0]
    p = me.preference = Preference(float(g("budget", 4000)), float(g("dist", 2)), g("food", "Any"), int(g("meals", 2)))
    opts = "".join(f"<option{' selected' if o == p.food_type else ''}>{o}</option>" for o in ["Any", "Halal", "Vegetarian", "Mixed"])
    out = f"""<div class=card><h3>Tell us what you need</h3><form class=grid>
<div><label>Max monthly budget (৳)</label><input name=budget type=number value={p.max_budget:g}></div>
<div><label>Max distance (km)</label><input name=dist type=number step=0.1 value={p.max_distance_km:g}></div>
<div><label>Food type</label><select name=food>{opts}</select></div>
<div><label>Meals per day</label><select name=meals>{''.join(f'<option{" selected" if i==p.meals_per_day else ""}>{i}</option>' for i in (1,2,3))}</select></div>
<div><br><button>Find messes</button></div></form></div><h3>Recommended for you</h3>"""
    for s, m in me.search_mess(MESSES):
        out += f"""<div class=card><span class=score>{s}% match</span><b><a href="/mess?id={m.mess_id}">{escape(m.name)}</a></b>
<div class=muted>৳{m.monthly_price:g}/month · {m.distance_km} km · {m.food_type} · {m.meals_per_day} meals/day · ★ {m.avg_rating():.1f} ({len(m.reviews)} reviews)</div></div>"""
    return page(out)

def detail(q):
    m = next((x for x in MESSES if str(x.mess_id) == q.get("id", [""])[0]), None)
    if not m: return page("<p>Mess not found.</p>")
    menu = "".join(f"<li>{escape(w.get_menu())}</li>" for w in m.menu) or "<li>No menu yet</li>"
    revs = "".join(f"<div class=card><b>{escape(r.student.name)}</b> · ★ {r.overall():.1f} <span class=muted>({r.date})</span><br>{escape(r.comment)}</div>" for r in m.reviews) or "<p class=muted>No reviews yet.</p>"
    subs = "".join(f"<li>{escape(s.meal_plan)} - <b>{s.status}</b></li>" for s in m.subscriptions if s.student is me)
    rate = "".join(f'<div><label>{n.title()}</label><select name={n}>{"".join(f"<option>{i}</option>" for i in (5,4,3,2,1))}</select></div>' for n in ("food", "hygiene", "service", "value"))
    return page(f"""<a href="/">← Back</a><div class=card><h2>{escape(m.name)}</h2>
<div class=muted>{escape(m.address)} · Owner: {escape(m.owner.name)} ({escape(m.owner.phone)})<br>৳{m.monthly_price:g}/month · {m.distance_km} km · {m.food_type} · ★ {m.avg_rating():.1f}</div>
<h4>Weekly menu</h4><ul>{menu}</ul></div>
<div class=card><h4>Request subscription</h4><form method=post action="/subscribe?id={m.mess_id}" class=grid>
<div><label>Meal plan</label><select name=plan><option>Lunch</option><option>Dinner</option><option>Lunch+Dinner</option><option>All 3 meals</option></select></div>
<div><br><button>Send request</button></div></form><ul>{subs}</ul>
<p class=muted>Demo: <a href="/approve?id={m.mess_id}">owner approves my latest request</a></p></div>
<h3>Reviews</h3>{revs}<div class=card><h4>Write a review</h4><form method=post action="/review?id={m.mess_id}" class=grid>{rate}
<div style="width:95%"><label>Comment</label><textarea name=comment rows=2></textarea></div><div><button>Submit</button></div></form></div>""")

class H(BaseHTTPRequestHandler):
    def send(self, html, code=200, loc=None):
        self.send_response(code)
        if loc: self.send_header("Location", loc)
        self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers()
        self.wfile.write(html.encode())
    def find(self, q): return next(x for x in MESSES if str(x.mess_id) == q["id"][0])
    def do_GET(self):
        u = urlparse(self.path); q = parse_qs(u.query)
        if u.path == "/": self.send(home(q))
        elif u.path == "/mess": self.send(detail(q))
        elif u.path == "/approve":
            m = self.find(q); subs = [s for s in m.subscriptions if s.student is me and s.status == "pending"]
            if subs: m.owner.decide_subscription(subs[-1], True)
            self.send("", 303, f"/mess?id={m.mess_id}")
        else: self.send(page("<p>404</p>"), 404)
    def do_POST(self):
        u = urlparse(self.path); q = parse_qs(u.query)
        f = parse_qs(self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()); m = self.find(q)
        if u.path == "/review":
            me.write_review(m, *(int(f[k][0]) for k in ("food", "hygiene", "service", "value")), f.get("comment", [""])[0][:300])
        elif u.path == "/subscribe":
            me.request_subscription(m, f["plan"][0])
        self.send("", 303, f"/mess?id={m.mess_id}")
    def log_message(self, *a): pass

if __name__ == "__main__":
    print("MessFinder running at http://localhost:8000  (Ctrl+C to stop)")
    HTTPServer(("", 8000), H).serve_forever()
