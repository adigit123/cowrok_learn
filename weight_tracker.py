import json
import os
import sys
from datetime import date

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weight_data.json")


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {"start_date": None, "goal_weight": None, "unit": "lbs", "entries": {}}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def week_number(start_date_str, target_date=None):
    start = date.fromisoformat(start_date_str)
    target = target_date or date.today()
    delta = (target - start).days
    return delta // 7 + 1


def current_week(data):
    if not data["start_date"]:
        return None
    return week_number(data["start_date"])


def setup(data):
    print("\n-- First-time setup --")
    start_input = input("Enter your start date (YYYY-MM-DD) or press Enter for today: ").strip()
    if not start_input:
        data["start_date"] = date.today().isoformat()
    else:
        try:
            date.fromisoformat(start_input)
            data["start_date"] = start_input
        except ValueError:
            print("Invalid date format. Using today.")
            data["start_date"] = date.today().isoformat()

    unit_input = input("Track weight in lbs or kg? (lbs/kg, default lbs): ").strip().lower()
    data["unit"] = "kg" if unit_input == "kg" else "lbs"

    goal = input(f"Enter your goal weight ({data['unit']}), or press Enter to skip: ").strip()
    if goal:
        try:
            data["goal_weight"] = float(goal)
        except ValueError:
            print("Invalid weight. Goal not set.")
            data["goal_weight"] = None
    else:
        data["goal_weight"] = None

    save_data(data)
    goal_str = f"{data['goal_weight']} {data['unit']}" if data["goal_weight"] else "not set"
    print(f"Tracking started from {data['start_date']}. Unit: {data['unit']}. Goal: {goal_str}")


def log_entry(data, week=None):
    if week is None:
        week = current_week(data)
        if week is None or week < 1 or week > 52:
            print("Outside the 52-week tracking window.")
            return
    else:
        try:
            week = int(week)
            if not 1 <= week <= 52:
                raise ValueError
        except ValueError:
            print("Invalid week number. Must be 1–52.")
            return

    existing = data["entries"].get(str(week))
    if existing:
        print(f"Week {week} already has an entry: {existing['weight']} {data['unit']}. Overwrite? (y/n) ", end="")
        if input().strip().lower() != "y":
            return

    weight_input = input(f"Enter weight for week {week} ({data['unit']}): ").strip()
    try:
        weight = float(weight_input)
        if weight <= 0:
            raise ValueError
    except ValueError:
        print("Invalid weight.")
        return

    data["entries"][str(week)] = {"weight": weight}
    save_data(data)
    print(f"Week {week} logged: {weight} {data['unit']}")

    if data["goal_weight"]:
        diff = weight - data["goal_weight"]
        if diff == 0:
            print(f"You are exactly at your goal of {data['goal_weight']} {data['unit']}!")
        else:
            direction = "above" if diff > 0 else "below"
            print(f"You are {abs(diff):.1f} {data['unit']} {direction} your goal of {data['goal_weight']} {data['unit']}.")


def delete_entry(data):
    week_input = input("Enter week number to delete (1-52): ").strip()
    try:
        week = int(week_input)
        if not 1 <= week <= 52:
            raise ValueError
    except ValueError:
        print("Invalid week number.")
        return

    if str(week) not in data["entries"]:
        print(f"No entry found for week {week}.")
        return

    print(f"Delete week {week} ({data['entries'][str(week)]['weight']} {data['unit']})? (y/n) ", end="")
    if input().strip().lower() != "y":
        return

    del data["entries"][str(week)]
    save_data(data)
    print(f"Week {week} entry deleted.")


def show_stats(data):
    entries = data["entries"]
    if not entries:
        print("No entries yet.")
        return

    unit = data["unit"]
    weeks = sorted(int(w) for w in entries)
    weights = [entries[str(w)]["weight"] for w in weeks]

    print(f"\n-- Stats --")
    print(f"Weeks logged: {len(weeks)} / 52")
    print(f"Latest entry: Week {weeks[-1]} — {weights[-1]} {unit}")
    print(f"Heaviest:     Week {weeks[weights.index(max(weights))]} — {max(weights)} {unit}")
    print(f"Lightest:     Week {weeks[weights.index(min(weights))]} — {min(weights)} {unit}")

    if len(weights) > 1:
        total_change = weights[-1] - weights[0]
        if total_change == 0:
            print(f"Total change: no change since week {weeks[0]}")
        else:
            direction = "lost" if total_change < 0 else "gained"
            print(f"Total change: {direction} {abs(total_change):.1f} {unit} since week {weeks[0]}")

    if data["goal_weight"]:
        diff = weights[-1] - data["goal_weight"]
        if diff == 0:
            print(f"Goal ({data['goal_weight']} {unit}): reached!")
        else:
            direction = "above" if diff > 0 else "below"
            print(f"Goal ({data['goal_weight']} {unit}):  {abs(diff):.1f} {unit} {direction}")

    week = current_week(data)
    if week and week >= 1:
        remaining = max(0, 52 - week)
        print(f"Weeks remaining: {remaining}")


def show_chart(data):
    try:
        import matplotlib.pyplot as plt
        import matplotlib.ticker as ticker
    except ImportError:
        print("matplotlib is not installed. Run: pip install matplotlib")
        return

    entries = data["entries"]
    if not entries:
        print("No entries to chart.")
        return

    unit = data["unit"]
    weeks = sorted(int(w) for w in entries)
    weights = [entries[str(w)]["weight"] for w in weeks]

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(weeks, weights, marker="o", linewidth=2, color="#2196F3", label="Weight")

    if data["goal_weight"]:
        ax.axhline(data["goal_weight"], color="#4CAF50", linestyle="--", linewidth=1.5,
                   label=f"Goal ({data['goal_weight']} {unit})")

    ax.set_xlim(1, 52)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(4))
    ax.set_xlabel("Week")
    ax.set_ylabel(f"Weight ({unit})")
    ax.set_title("Weight Tracker — 52-Week Overview")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


def show_table(data):
    unit = data["unit"]
    print(f"\n{'Week':>5}  {'Weight':>10}  {'vs Goal':>8}")
    print("-" * 30)
    for w in range(1, 53):
        entry = data["entries"].get(str(w))
        if entry:
            weight = entry["weight"]
            if data["goal_weight"]:
                diff = weight - data["goal_weight"]
                vs_goal = f"{diff:+.1f}"
            else:
                vs_goal = "—"
            print(f"{w:>5}  {weight:>8.1f} {unit}  {vs_goal:>8}")
        else:
            print(f"{w:>5}  {'—':>10}  {'':>8}")


def main():
    data = load_data()

    if not data["start_date"]:
        setup(data)

    if "unit" not in data:
        data["unit"] = "lbs"

    while True:
        week = current_week(data)
        if week and 1 <= week <= 52:
            week_display = f"Week {week}/52"
        else:
            week_display = "Outside window"
        print(f"\n[{week_display}]")
        print("1. Log weight for current week")
        print("2. Log weight for a specific week")
        print("3. View stats")
        print("4. Show chart")
        print("5. Show full table")
        print("6. Update goal weight")
        print("7. Delete an entry")
        print("q. Quit")
        choice = input("> ").strip().lower()

        if choice == "1":
            log_entry(data)
        elif choice == "2":
            week_input = input("Enter week number (1-52): ").strip()
            log_entry(data, week=week_input)
        elif choice == "3":
            show_stats(data)
        elif choice == "4":
            show_chart(data)
        elif choice == "5":
            show_table(data)
        elif choice == "6":
            goal = input(f"Enter new goal weight ({data['unit']}): ").strip()
            try:
                data["goal_weight"] = float(goal)
                save_data(data)
                print(f"Goal updated to {data['goal_weight']} {data['unit']}.")
            except ValueError:
                print("Invalid weight.")
        elif choice == "7":
            delete_entry(data)
        elif choice == "q":
            sys.exit(0)
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
