from __future__ import annotations
import time, sys, datetime as dt
from typing import Optional, Literal
import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
import yaml, os

app = typer.Typer()
console = Console()
Base = declarative_base()
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "logs.sqlite")
ENGINE = create_engine(f"sqlite:///{DB_PATH}", future=True)
Session = sessionmaker(bind=ENGINE)

class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True)
    date = Column(Date, default=dt.date.today)
    plan = Column(String, nullable=False)
    drill = Column(String, nullable=False)
    side = Column(String, nullable=True)
    hold_s = Column(Integer, nullable=False)
    sets = Column(Integer, nullable=False, default=1)
    rpe = Column(Integer, nullable=False)
    pain = Column(Boolean, default=False)
    rom_cm = Column(Float, nullable=True)     # positive numbers; lower is deeper
    notes = Column(String, nullable=True)

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    Base.metadata.create_all(ENGINE)

def beep():
    try:
        print("\a", end="") ; sys.stdout.flush()
    except:  # no-op on some terms
        pass

def countdown(seconds:int, label:str):
    with console.status(f"[bold]{label}[/bold] ({seconds}s)"):
        for s in range(seconds, 0, -1):
            console.log(f"{label}: {s}s remaining", log_locals=False)
            time.sleep(1)
    beep()

def load_plan(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)

@app.command()
def session(
    plan_path: str = typer.Option("../plans/front_split_12w.yml", help="YAML routine"),
    week: int = typer.Option(1, min=1),
    day: Literal["A","B","C"] = typer.Option("A")
):
    """Run a guided stretching session and log results."""
    init_db()
    plan = load_plan(plan_path)
    block = plan["weeks"][str(week)][day]
    console.rule(f"[bold green]SplitSmith[/] — Week {week} Day {day}")
    for drill in block["sequence"]:
        name = drill["name"]
        side = drill.get("side")
        sets = drill.get("sets", 1)
        hold = drill["hold_s"]
        rest = drill.get("rest_s", 15)
        cue = drill.get("cue", "")

        console.print(f"\n[bold]{name}[/] {f'({side})' if side else ''} — {sets} x {hold}s")
        if cue: console.print(f"[italic]{cue}[/]")

        for st in range(1, sets+1):
            console.print(f"Set {st}/{sets}: hold {hold}s")
            countdown(hold, f"{name} hold")
            if rest: countdown(rest, "rest")

        # quick log for this drill
        rpe = typer.prompt("RPE (1–10)", type=int)
        pain = typer.confirm("Any pain (sharp/pinching)?", default=False)
        rom_cm = typer.prompt("ROM proxy (cm) — lower is deeper; blank to skip", default="", type=str)
        rom_cm = float(rom_cm) if rom_cm.strip() else None
        notes = typer.prompt("Notes (optional)", default="")
        with Session() as s:
            s.add(Log(
                date=dt.date.today(), plan=os.path.basename(plan_path),
                drill=name, side=side, hold_s=hold, sets=sets,
                rpe=rpe, pain=pain, rom_cm=rom_cm, notes=notes
            ))
            s.commit()
    console.rule("[bold]Done[/] — hydrate, light walk 2–3 min")

@app.command()
def report(days:int=7):
    """Show last N days and progress deltas."""
    init_db()
    with Session() as s:
        table = Table(title=f"Last {days} days")
        for c in ["date","plan","drill","side","hold_s","sets","rpe","pain","rom_cm"]:
            table.add_column(c)
        rows = s.execute(
            "SELECT date,plan,drill,side,hold_s,sets,rpe,pain,rom_cm "
            "FROM logs ORDER BY date DESC LIMIT :limit", {"limit": 200}
        ).all()
        shown = 0
        for r in rows:
            if shown>=200: break
            table.add_row(*[str(x) if x is not None else "" for x in r])
            shown+=1
        console.print(table)

@app.command()
def export_csv(path: str = "../data/splitsmith_export.csv"):
    """Export all logs to CSV."""
    import csv
    init_db()
    with Session() as s, open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date","plan","drill","side","hold_s","sets","rpe","pain","rom_cm","notes"])
        for row in s.query(Log).order_by(Log.date.asc()).all():
            writer.writerow([row.date,row.plan,row.drill,row.side,row.hold_s,row.sets,row.rpe,row.pain,row.rom_cm,row.notes])
    console.print(f"[green]Exported to {path}[/]")

if __name__ == "__main__":
    app()
