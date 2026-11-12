"""Fill the database with a demo coach, a drill library and two practice plans.

Run from the server folder:  python seed.py
Safe to run again: it skips the demo user if it already exists.
"""

from datetime import date, timedelta

from app import app
from extensions import db
from models import Drill, PlanDrill, PracticePlan, User

DEMO_USERNAME = "coach"
DEMO_PASSWORD = "volleyball123"

DRILLS = [
    ("Dynamic Warm-up Lap", "Jog, high knees, butt kicks, lunges and arm circles across the court width.", "Warm-up", "Beginner", 8, "None"),
    ("Partner Passing", "Pairs pass back and forth with a focus on platform angle and footwork.", "Passing", "Beginner", 12, "1 ball per pair"),
    ("Serve and Receive", "Servers rotate in while a 3-person passing line receives and targets the setter.", "Serving", "Intermediate", 15, "Balls, cones"),
    ("Target Serving", "Serve to marked zones. Score a point for each ball that lands in the target.", "Serving", "Beginner", 10, "Ball cart, cones"),
    ("Wall Setting", "Continuous overhead sets against a wall, aiming at a taped target.", "Setting", "Beginner", 8, "Wall, tape"),
    ("Setter Footwork Ladder", "Quick feet to the target, square up, and deliver a hand set to the pin.", "Setting", "Intermediate", 12, "Agility ladder"),
    ("Hit Line Approach", "Three-step approach and arm swing against a coach toss, cross-court and line.", "Hitting", "Intermediate", 15, "Balls, net"),
    ("Block Timing Slides", "Middle blockers shuffle along the net and jump on the coach's hand signal.", "Blocking", "Intermediate", 10, "Net"),
    ("Six-Person Defense", "Coach hits from a box while the back row reads, digs and covers.", "Defense", "Advanced", 20, "Balls, box"),
    ("Dig and Cover Relay", "Teams race to dig, set and cover a series of free balls.", "Defense", "Beginner", 12, "Balls"),
    ("Jump Rope Circuit", "Three rounds of rope, squat jumps and core planks.", "Conditioning", "Beginner", 10, "Jump ropes"),
    ("Scrimmage to 25", "Full six-on-six game with rotation. Coach calls out one focus per rally.", "Team Play", "Advanced", 25, "Net, balls"),
]


def seed():
    with app.app_context():
        if User.query.filter_by(username=DEMO_USERNAME).first():
            print(f"User '{DEMO_USERNAME}' already exists, nothing to do.")
            return

        coach = User(username=DEMO_USERNAME)
        coach.password_hash = DEMO_PASSWORD
        db.session.add(coach)
        db.session.flush()

        drills = {}
        for name, description, category, level, minutes, equipment in DRILLS:
            drill = Drill(
                user_id=coach.id, name=name, description=description, category=category,
                skill_level=level, default_minutes=minutes, equipment=equipment,
            )
            db.session.add(drill)
            drills[name] = drill
        db.session.flush()

        def add_plan(title, focus, days_from_now, target, notes, drill_names):
            plan = PracticePlan(
                user_id=coach.id, title=title, focus=focus,
                practice_date=date.today() + timedelta(days=days_from_now),
                target_minutes=target, notes=notes,
            )
            db.session.add(plan)
            for position, name in enumerate(drill_names, start=1):
                drill = drills[name]
                plan.items.append(PlanDrill(drill=drill, position=position, minutes=drill.default_minutes))

        add_plan(
            "Tuesday Serve and Pass Night", "Serve receive consistency", 2, 90,
            "Bring extra balls. Water break after the third drill.",
            ["Dynamic Warm-up Lap", "Partner Passing", "Target Serving", "Serve and Receive", "Scrimmage to 25"],
        )
        add_plan(
            "Saturday Defense Clinic", "Reading the hitter and covering", 5, 120,
            "Film the six-person defense drill for review.",
            ["Dynamic Warm-up Lap", "Dig and Cover Relay", "Block Timing Slides", "Six-Person Defense", "Jump Rope Circuit"],
        )

        db.session.commit()
        print(f"Seeded demo coach '{DEMO_USERNAME}' (password: {DEMO_PASSWORD}) with {len(DRILLS)} drills and 2 plans.")


if __name__ == "__main__":
    seed()
