"""
Database Seeder Script
Wrapper to invoke deterministic generator pipeline directly.
"""
from generator.generate import run_pipeline

if __name__ == "__main__":
    run_pipeline(scale="starter", seed_database=True, export_files=True)