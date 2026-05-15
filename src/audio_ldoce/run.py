import subprocess
import sys


def main():
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "requests", "-t", "vendor/"]
    )

    subprocess.run(
        [sys.executable, "-m", "pip", "install", "beautifulsoup4", "-t", "vendor/"]
    )


if __name__ == "__main__":
    main()
