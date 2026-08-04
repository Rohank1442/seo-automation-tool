import sys
from phases.v01_research import run_research_phase

def main():
    try:
        run_research_phase()
    except KeyboardInterrupt:
        print("\n\nExecution interrupted by user. Exiting.")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn error occurred during execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
