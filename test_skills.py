import sys
import asyncio

def check_import(module_name, pip_name=None):
    if pip_name is None:
        pip_name = module_name
    try:
        module = __import__(module_name)
        version = getattr(module, '__version__', 'Version unknown')
        print(f"[OK] {pip_name} imported successfully (Version: {version})")
        return True
    except ImportError as e:
        print(f"[FAIL] Failed to import {pip_name}: {e}")
        return False
    except Exception as e:
        print(f"[WARN] Error while importing {pip_name}: {e}")
        return False

async def main():
    print("--- Testing Jarvis Skills Dependencies ---")
    
    # Phase 1
    print("\nPhase 1: Automations")
    check_import('pycaw', 'pycaw')
    check_import('comtypes')
    check_import('pyautogui')
    check_import('screen_brightness_control')

    # Phase 2
    print("\nPhase 2: External World")
    check_import('duckduckgo_search')
    check_import('bs4', 'beautifulsoup4')
    check_import('playwright')
    check_import('aiohttp')

    # Phase 3
    print("\nPhase 3: Vision")
    check_import('PIL', 'Pillow')
    check_import('mss')
    check_import('pytesseract')
    check_import('cv2', 'opencv-python')

    # Phase 4
    print("\nPhase 4: Multimedia")
    check_import('spotipy')
    check_import('paho.mqtt', 'paho-mqtt')
    
    print("\n--- Testing Finished ---")

if __name__ == "__main__":
    asyncio.run(main())
