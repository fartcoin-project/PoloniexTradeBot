#!/usr/bin/env python3
"""Launch the TradeBot desktop GUI. Run from backend/tradebot/."""

import sys

if __name__ == "__main__" and "--scheduled" in sys.argv:
    from run_scheduled import main as scheduled_main

    sys.argv = [a for a in sys.argv if a != "--scheduled"]
    raise SystemExit(scheduled_main())

from gui.paths import setup_runtime

setup_runtime()

from gui.app import main

if __name__ == "__main__":
    main()
