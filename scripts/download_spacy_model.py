from __future__ import annotations

import subprocess
import sys


def main() -> None:
    subprocess.run(
        [sys.executable, "-m", "spacy", "download", "en_core_web_sm"],
        check=True,
    )


if __name__ == "__main__":
    main()

