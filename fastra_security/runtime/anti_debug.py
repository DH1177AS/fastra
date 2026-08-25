import sys, os

def anti_debug_check():
    if sys.gettrace() is not None:
        raise RuntimeError("Debugger terdeteksi")
    if "PYCHARM_HOSTED" in os.environ or "VSCODE_PID" in os.environ:
        raise RuntimeError("IDE development terdeteksi")