"""Stand-in for a philter-ucsf run that fails, used only in tests."""
import sys

if __name__ == "__main__":
    print("simulated philter failure", file=sys.stderr)
    sys.exit(2)
