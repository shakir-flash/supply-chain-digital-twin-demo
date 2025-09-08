# main.py
from model.run_pipeline import run_full

if __name__ == "__main__":
    print("Running full pipeline...")
    run_full()
    print("Done. See data/results and data/charts.")
