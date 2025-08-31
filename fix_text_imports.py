#!/usr/bin/env python3
import os
import re
from pathlib import Path

def fix_text_imports():
    handlers_dir = Path("core/handlers")
    
    for filepath in handlers_dir.glob("*.py"):
        print(f"Processing {filepath}...")
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Save original content for comparison
        original_content = content
        
        # Fix imports
        content = content.replace(
            "from aiogram.filters import Text",
            "from aiogram import F"
        )
        
        # Fix combined imports
        content = re.sub(
            r'from aiogram\.filters import (.*?)(,?\s*Text\b)(.*?)(\n|$)',
            lambda m: f"from aiogram.filters import {m.group(1)}{m.group(3)}\nfrom aiogram import F\n" if m.group(1).strip() or m.group(3).strip() else "from aiogram import F\n",
            content
        )
        
        # Fix Text() usage
        content = re.sub(
            r'Text\(\[([^\]]+)\](?:,\s*ignore_case=True)?\)',
            r'F.text.in_([\1])',
            content
        )
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed: {filepath}")
        else:
            print(f"ℹ️ No changes needed for {filepath}")

if __name__ == "__main__":
    import sys
    # Set console output to UTF-8
    if sys.platform == 'win32':
        import io
        import sys
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("Starting Text import fixes...")
    fix_text_imports()
    print("All files processed!")
