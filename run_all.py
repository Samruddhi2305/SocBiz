import subprocess
import sys
import os

scripts = [
    "data_prep.py",
    "demand_agent.py",
    "pricing_agent.py",
    "plot_generator.py",
    "generate_deck.py"
]

def run_reproducible_pipeline():
    print("=================================================================")
    print("STARTING EV CHARGING DYNAMIC TARIFF OPTIMIZATION PIPELINE")
    print("=================================================================")
    
    for script in scripts:
        print(f"\n>>> Running: {script} ...")
        result = subprocess.run([sys.executable, script], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"SUCCESS: {script} completed.")
            # Print last few lines of output
            lines = result.stdout.strip().split('\n')
            for line in lines[-5:]:
                print("  ", line)
        else:
            print(f"ERROR: {script} failed with exit code {result.returncode}")
            print(result.stderr)
            sys.exit(1)
            
    print("\n=================================================================")
    print("PIPELINE EXECUTED SUCCESSFULLY! ALL DELIVERABLES GENERATED.")
    print("=================================================================")

if __name__ == "__main__":
    run_reproducible_pipeline()
