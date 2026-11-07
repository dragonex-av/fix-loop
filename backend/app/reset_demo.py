"""
FixLoop Demo Reset Utility
Usage: python -m app.reset_demo
Cleanly wipes and reseeds the database with deterministic demo data.
"""
from app.seed_data import seed

def reset():
    print("=" * 60)
    print("FixLoop v2.0: Resetting Demo Data...")
    print("=" * 60)
    seed()
    print("=" * 60)
    print("FixLoop Demo Reset Complete! 9 benchmark tickets seeded.")
    print("=" * 60)

if __name__ == "__main__":
    reset()
