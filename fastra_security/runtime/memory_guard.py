import ctypes
import sys

if sys.platform == "win32":
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    VirtualLock = kernel32.VirtualLock
    VirtualUnlock = kernel32.VirtualUnlock
else:
    libc = ctypes.CDLL(None)
    mlock = libc.mlock
    munlock = libc.munlock

def secure_string(data: bytes) -> bytes:
    if sys.platform == "win32":
        buf = ctypes.create_string_buffer(data)
        VirtualLock(ctypes.cast(buf, ctypes.c_void_p), len(data))
    else:
        buf = ctypes.create_string_buffer(data)
        mlock(ctypes.cast(buf, ctypes.c_void_p), len(data))
    return data

def wipe_string(data: bytes) -> None:
    if not isinstance(data, bytes):
        return
    if sys.platform == "win32":
        buf = ctypes.create_string_buffer(data)
        ctypes.memset(buf, 0, len(data))
        VirtualUnlock(ctypes.cast(buf, ctypes.c_void_p), len(data))
    else:
        buf = ctypes.create_string_buffer(data)
        ctypes.memset(buf, 0, len(data))
        munlock(ctypes.cast(buf, ctypes.c_void_p), len(data))
