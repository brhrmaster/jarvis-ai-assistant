"""Entry point for running as module: python -m pyjarvis_cli"""

import sys
import asyncio
from .client import send_text_to_service

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m pyjarvis_cli <text> [--language <lang>]")
        sys.exit(1)
    
    text = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] == "--language" else None
    
    asyncio.run(send_text_to_service(text, language))

