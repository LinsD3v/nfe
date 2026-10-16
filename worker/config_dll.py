# config_dll.py
# requires Python 3.11 or 3.10 and java Access bridge installed and configured in the system

from RPA.JavaAccessBridge import JavaAccessBridge

DLL = (
    r"C:\Users\user\Desktop\AHK_automaçoes\python_implements\requirements\accessbridge2_0_2"
    r"\WindowsAccessBridge-64.dll"
)

jab = JavaAccessBridge(
    access_bridge_path=DLL,
    ignore_callbacks=True,
    max_depth=10,
)