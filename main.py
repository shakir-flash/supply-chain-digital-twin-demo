# main.py
# One-click orchestrator for your demo: generate → clean → optimize → analyze → visualize

from data_generation import run as gen_run
from data_cleaning import run as clean_run
from optimization import run as opt_run
from analytics import run as an_run
from visualization import run as viz_run

def run_all():
    print("1) Generating raw data...")
    gen_run()
    print("2) Cleaning & validating...")
    clean_run()
    print("3) Solving optimization...")
    opt_run()
    print("4) Aggregating analytics...")
    an_run()
    print("5) Rendering charts...")
    viz_run()
    print("Done. Check the data/ and charts/ folders.")

if __name__ == "__main__":
    run_all()
