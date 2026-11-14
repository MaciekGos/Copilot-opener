"""Copilot Opener - tray app / aplikacja w zasobniku.

Po uruchomieniu od razu odpala GitHub Copilot i najnowszy emulator Androida (AVD),
a potem siedzi w zasobniku. Emulator mozna przypiac "zawsze na wierzchu".
Starts GitHub Copilot + the newest Android emulator right away, then stays in the tray.

Argumenty / arguments:  --no-launch  (nie odpalaj przy starcie / don't launch on start)
                        --show       (pokaz okno / show the window)
"""
import ctypes
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
import tkinter as tk
import winreg
from ctypes import wintypes
from pathlib import Path

import pystray
from PIL import Image, ImageTk

APP_NAME = "Copilot Opener"
CONFIG_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "CopilotOpener"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS = {
    # "auto" (jezyk Windows) / "pl" / "en"
    "language": "auto",
    # Nazwa aplikacji widoczna w menu Start (Get-StartApps)
    "copilot_app_name": "GitHub Copilot",
    # Opcjonalnie: pelna sciezka do exe Copilota (ma pierwszenstwo)
    "copilot_path": "",
    # Czy "Odpal wszystko" ma odpalac tez emulator
    "emulator": True,
    # Opcjonalnie: sciezka do Android SDK (domyslnie wykrywana sama)
    "sdk_path": "",
    # Opcjonalnie: dowolne dodatkowe aplikacje do odpalenia z "Odpal wszystko"
    "extra_apps": [],
    # Odpal wszystko od razu po uruchomieniu programu
    "launch_on_start": True,
    # Emulator zawsze na wierzchu
    "pin_emulator": False,
    # Schowaj okno do zasobnika po odpaleniu
    "hide_after_launch": True,
}

# ---------------- Tlumaczenia / translations ----------------
STR = {
    "pl": {
        "subtitle": "GitHub Copilot + najnowszy emulator Androida",
        "launch_all": "▶  Odpal wszystko",
        "only_copilot": "Tylko Copilot",
        "only_emulator": "Tylko emulator",
        "pin": "Emulator zawsze na wierzchu",
        "hint": "Zamknięcie okna chowa aplikację do zasobnika.",
        "menu_show": "Pokaż okno",
        "menu_autostart": "Uruchamiaj z Windows",
        "menu_config": "Otwórz plik konfiguracji",
        "menu_lang": "Język / Language",
        "menu_quit": "Wyjdź",
        "err_copilot_file": "Nie znaleziono pliku Copilota:\n{path}",
        "err_copilot_nf": "Nie znaleziono aplikacji \"{name}\" w menu Start.\n"
                          "Ustaw \"copilot_path\" w pliku:\n{cfg}",
        "err_sdk": "Nie znaleziono Android SDK (emulator.exe).\n"
                   "Ustaw \"sdk_path\" w pliku:\n{cfg}",
        "err_avd": "Nie znaleziono żadnego emulatora (AVD) w:\n{path}",
        "err_extra": "Nie udało się uruchomić: {app}\n{err}",
        "err_autostart": "Nie udało się zmienić autostartu:\n{err}",
    },
    "en": {
        "subtitle": "GitHub Copilot + the newest Android emulator",
        "launch_all": "▶  Launch everything",
        "only_copilot": "Copilot only",
        "only_emulator": "Emulator only",
        "pin": "Keep emulator always on top",
        "hint": "Closing the window hides the app to the tray.",
        "menu_show": "Show window",
        "menu_autostart": "Start with Windows",
        "menu_config": "Open config file",
        "menu_lang": "Język / Language",
        "menu_quit": "Quit",
        "err_copilot_file": "Copilot file not found:\n{path}",
        "err_copilot_nf": "App \"{name}\" was not found in the Start menu.\n"
                          "Set \"copilot_path\" in:\n{cfg}",
        "err_sdk": "Android SDK (emulator.exe) not found.\n"
                   "Set \"sdk_path\" in:\n{cfg}",
        "err_avd": "No emulator (AVD) found in:\n{path}",
        "err_extra": "Could not launch: {app}\n{err}",
        "err_autostart": "Could not change autostart:\n{err}",
    },
}
LANG = "en"


def t(key, **kw):
    s = STR[LANG][key]
    return s.format(**kw) if kw else s


NO_WINDOW = 0x08000000
DETACHED = 0x00000008
NEW_GROUP = 0x00000200

BG, PANEL, FG, MUTED = "#0d1117", "#161b22", "#f0f6fc", "#8b949e"
ACCENT, ACCENT_HOVER = "#6e40c9", "#8957e5"

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

# ---------------- WinAPI ----------------
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
user32.GetWindowLongW.restype = ctypes.c_long
user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, ctypes.c_uint]

kernel32.CreateMutexW.restype = ctypes.c_void_p
kernel32.CreateEventW.restype = ctypes.c_void_p
kernel32.OpenEventW.restype = ctypes.c_void_p
kernel32.SetEvent.argtypes = [ctypes.c_void_p]
kernel32.WaitForSingleObject.argtypes = [ctypes.c_void_p, wintypes.DWORD]

GWL_EXSTYLE = -20
WS_EX_TOPMOST = 0x8
SWP_NOSIZE, SWP_NOMOVE, SWP_NOACTIVATE = 0x1, 0x2, 0x10
HWND_TOPMOST = ctypes.c_void_p(-1)
HWND_NOTOPMOST = ctypes.c_void_p(-2)

_handles = []  # trzymamy uchwyty mutexu/zdarzenia przy zyciu


def detect_lang():
    try:
        return "pl" if (kernel32.GetUserDefaultUILanguage() & 0xFF) == 0x15 else "en"
    except Exception:
        return "en"


def emulator_windows():
    """Okna procesu emulatora (glowne okno 'Android Emulator - ...' + jego panel/dialogi)."""
    found = []

    def cb(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            n = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(n + 1)
            if n:
                user32.GetWindowTextW(hwnd, buf, n + 1)
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            found.append((hwnd, buf.value, pid.value))
        return True

    user32.EnumWindows(WNDENUMPROC(cb), 0)
    pids = {pid for _, title, pid in found if title.startswith("Android Emulator - ")}
    return [hwnd for hwnd, _, pid in found if pid in pids]


def pin_windows(on):
    for hwnd in emulator_windows():
        is_top = bool(user32.GetWindowLongW(hwnd, GWL_EXSTYLE) & WS_EX_TOPMOST)
        if on != is_top:
            user32.SetWindowPos(hwnd, HWND_TOPMOST if on else HWND_NOTOPMOST,
                                0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)


def acquire_single_instance(signal_launch):
    """True jesli to pierwsza instancja. Druga prosi pierwsza o ponowne odpalenie."""
    ev = kernel32.CreateEventW(None, False, False, "CopilotOpenerLaunchEvent")
    kernel32.CreateMutexW(None, False, "CopilotOpenerMutex")
    if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        if signal_launch:
            other = kernel32.OpenEventW(0x2, False, "CopilotOpenerLaunchEvent")
            if other:
                kernel32.SetEvent(other)
        return False, None
    _handles.append(ev)
    return True, ev


# ---------------- Konfiguracja / autostart ----------------
def save_config(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def load_config():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    cfg = dict(DEFAULTS)
    if CONFIG_FILE.exists():
        try:
            cfg.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    else:
        save_config(cfg)
    return cfg


def autostart_command():
    # Autostart z Windows: tylko zasobnik, bez odpalania aplikacji
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --no-launch'
    pyw = Path(sys.executable).with_name("pythonw.exe")
    return f'"{pyw}" "{Path(__file__).resolve()}" --no-launch'


def autostart_enabled():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            winreg.QueryValueEx(k, "CopilotOpener")
            return True
    except OSError:
        return False


def set_autostart(on):
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
        if on:
            winreg.SetValueEx(k, "CopilotOpener", 0, winreg.REG_SZ, autostart_command())
        else:
            try:
                winreg.DeleteValue(k, "CopilotOpener")
            except FileNotFoundError:
                pass


def resource(name):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / name


def message(text, icon=0x10):
    user32.MessageBoxW(0, text, APP_NAME, icon)


def spawn(args):
    subprocess.Popen(
        args,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        # NO_WINDOW (ukryta konsola dziedziczona przez dzieci) zamiast DETACHED_PROCESS:
        # przy DETACHED emulator.exe odpalal qemu w nowym, widocznym oknie terminala.
        creationflags=NEW_GROUP | NO_WINDOW,
        close_fds=True,
    )


# ---------------- GitHub Copilot ----------------
def open_copilot(cfg):
    path = cfg.get("copilot_path", "")
    if path:
        if Path(path).exists():
            os.startfile(path)
            return None
        return t("err_copilot_file", path=path)

    name = str(cfg.get("copilot_app_name", "GitHub Copilot")).replace("'", "''")
    ps = (
        f"Get-StartApps | Where-Object {{ $_.Name -like '*{name}*' }} "
        "| Select-Object -First 1 -ExpandProperty AppID"
    )
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True, text=True, timeout=20, creationflags=NO_WINDOW,
        ).stdout.strip()
    except Exception:
        out = ""
    if out:
        spawn(["explorer.exe", f"shell:AppsFolder\\{out}"])
        return None
    return t("err_copilot_nf", name=cfg["copilot_app_name"], cfg=CONFIG_FILE)


# ---------------- Emulator Androida ----------------
def find_sdk(cfg):
    candidates = [cfg.get("sdk_path"), os.environ.get("ANDROID_SDK_ROOT"),
                  os.environ.get("ANDROID_HOME"),
                  str(Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk")]
    for c in candidates:
        if c and (Path(c) / "emulator" / "emulator.exe").exists():
            return Path(c)
    return None


def avd_home():
    if os.environ.get("ANDROID_AVD_HOME"):
        return Path(os.environ["ANDROID_AVD_HOME"])
    base = os.environ.get("ANDROID_USER_HOME") or str(Path.home() / ".android")
    return Path(base) / "avd"


def newest_avd():
    home = avd_home()
    best = None
    for ini in home.glob("*.ini"):
        name = ini.stem
        folder = home / f"{name}.avd"
        try:
            for line in ini.read_text(encoding="utf-8", errors="ignore").splitlines():
                if line.startswith("path=") and Path(line[5:].strip()).exists():
                    folder = Path(line[5:].strip())
        except Exception:
            pass
        config = folder / "config.ini"
        api = 0
        if config.exists():
            m = re.search(r"android-(\d+)", config.read_text(encoding="utf-8", errors="ignore"))
            if m:
                api = int(m.group(1))
        mtime = (config if config.exists() else ini).stat().st_mtime
        key = (api, mtime)
        if best is None or key > best[0]:
            best = (key, name)
    return best[1] if best else None


def open_emulator(cfg):
    sdk = find_sdk(cfg)
    if not sdk:
        return t("err_sdk", cfg=CONFIG_FILE)
    avd = newest_avd()
    if not avd:
        return t("err_avd", path=avd_home())
    spawn([str(sdk / "emulator" / "emulator.exe"), "-avd", avd])
    return None


# ---------------- Aplikacja (okno + zasobnik) ----------------
class App:
    def __init__(self, launch_event):
        global LANG
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
        self.cfg = load_config()
        LANG = self.cfg["language"] if self.cfg["language"] in STR else detect_lang()
        self.launch_event = launch_event
        self.q = queue.Queue()
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.configure(bg=BG)
        self.root.resizable(False, False)
        try:
            self.root.iconbitmap(str(resource("icon.ico")))
        except Exception:
            pass
        self.pin_var = tk.BooleanVar(value=bool(self.cfg["pin_emulator"]))
        self.build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.hide)
        self.root.withdraw()  # start schowany

        self.tray = pystray.Icon("CopilotOpener", self.tray_image(), APP_NAME, self.menu())
        self.tray.run_detached()

        threading.Thread(target=self.watch_pin, daemon=True).start()
        threading.Thread(target=self.wait_launch, daemon=True).start()
        self.root.after(200, self.poll)
        if "--show" in sys.argv:
            self.show()
        if "--no-launch" not in sys.argv and self.cfg.get("launch_on_start", True):
            self.root.after(300, self.launch_all)  # od razu po uruchomieniu
        self.root.mainloop()

    # --- UI ---
    def tray_image(self):
        try:
            return Image.open(resource("icon.ico")).convert("RGBA")
        except Exception:
            return Image.new("RGBA", (64, 64), (110, 64, 201, 255))

    def button(self, text, command, primary=False):
        b = tk.Button(self.root, text=text, command=command, relief="flat", bd=0, cursor="hand2",
                      font=("Segoe UI", 11, "bold" if primary else "normal"),
                      bg=ACCENT if primary else PANEL, fg=FG,
                      activebackground=ACCENT_HOVER if primary else "#21262d",
                      activeforeground=FG, pady=10)
        b.pack(fill="x", padx=24, pady=4)
        return b

    def build_ui(self):
        try:
            img = Image.open(resource("icon.ico")).convert("RGBA").resize((72, 72), Image.LANCZOS)
            self.logo = ImageTk.PhotoImage(img)
            tk.Label(self.root, image=self.logo, bg=BG).pack(pady=(22, 6))
        except Exception:
            pass
        tk.Label(self.root, text=APP_NAME, font=("Segoe UI", 16, "bold"), bg=BG, fg=FG).pack()
        tk.Label(self.root, text=t("subtitle"), font=("Segoe UI", 9), bg=BG, fg=MUTED
                 ).pack(pady=(0, 14))

        self.button(t("launch_all"), self.launch_all, primary=True)
        self.button(t("only_copilot"), lambda: self.launch(True, False))
        self.button(t("only_emulator"), lambda: self.launch(False, True))

        tk.Checkbutton(self.root, text=t("pin"), variable=self.pin_var,
                       command=lambda: self.set_pin(self.pin_var.get()),
                       bg=BG, fg=FG, selectcolor=PANEL, activebackground=BG,
                       activeforeground=FG, font=("Segoe UI", 10), cursor="hand2"
                       ).pack(pady=(14, 2))
        tk.Label(self.root, text=t("hint"), font=("Segoe UI", 8), bg=BG, fg=MUTED
                 ).pack(pady=(6, 18))
        self.root.geometry("340x430")

    def rebuild_ui(self):
        for w in self.root.winfo_children():
            w.destroy()
        self.build_ui()

    def show(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def hide(self):
        self.root.withdraw()

    # --- komunikacja miedzy watkami ---
    def ui(self, fn):
        self.q.put(fn)

    def poll(self):
        try:
            while True:
                self.q.get_nowait()()
        except queue.Empty:
            pass
        self.root.after(200, self.poll)

    def wait_launch(self):
        # druga instancja (np. klikniecie skrotu) = odpal ponownie
        while True:
            if kernel32.WaitForSingleObject(self.launch_event, 1000) == 0:
                self.ui(self.launch_all)

    # --- tray ---
    def menu(self):
        Item = pystray.MenuItem
        sep = pystray.Menu.SEPARATOR
        return pystray.Menu(
            Item(t("menu_show"), lambda: self.ui(self.show), default=True),
            sep,
            Item(t("launch_all").lstrip("▶ "), lambda: self.launch_all()),
            Item(t("only_copilot"), lambda: self.launch(True, False)),
            Item(t("only_emulator"), lambda: self.launch(False, True)),
            sep,
            Item(t("pin"), lambda: self.set_pin(not self.cfg["pin_emulator"]),
                 checked=lambda item: bool(self.cfg["pin_emulator"])),
            Item(t("menu_autostart"), lambda: self.toggle_autostart(),
                 checked=lambda item: autostart_enabled()),
            Item(t("menu_lang"), pystray.Menu(
                Item("Polski", lambda: self.set_lang("pl"),
                     checked=lambda item: LANG == "pl", radio=True),
                Item("English", lambda: self.set_lang("en"),
                     checked=lambda item: LANG == "en", radio=True),
            )),
            Item(t("menu_config"), lambda: os.startfile(CONFIG_FILE)),
            sep,
            Item(t("menu_quit"), lambda: self.quit()),
        )

    # --- akcje ---
    def launch_all(self):
        self.launch(True, bool(self.cfg.get("emulator", True)), extras=True)

    def launch(self, copilot, emulator, extras=False):
        def job():
            errors = []
            if copilot:
                err = open_copilot(self.cfg)
                if err:
                    errors.append(err)
            if emulator:
                err = open_emulator(self.cfg)
                if err:
                    errors.append(err)
            if extras:
                for app in self.cfg.get("extra_apps", []):
                    try:
                        os.startfile(app)
                    except Exception as e:
                        errors.append(t("err_extra", app=app, err=e))
            if errors:
                message("\n\n".join(errors))
            elif self.cfg.get("hide_after_launch", True):
                self.ui(self.hide)

        threading.Thread(target=job, daemon=True).start()

    def set_pin(self, value):
        self.cfg["pin_emulator"] = bool(value)
        save_config(self.cfg)
        self.ui(lambda: self.pin_var.set(bool(value)))
        threading.Thread(target=lambda: pin_windows(bool(value)), daemon=True).start()
        self.tray.update_menu()

    def set_lang(self, code):
        global LANG
        LANG = code
        self.cfg["language"] = code
        save_config(self.cfg)
        self.ui(self.rebuild_ui)
        self.tray.menu = self.menu()
        self.tray.update_menu()

    def toggle_autostart(self):
        try:
            set_autostart(not autostart_enabled())
        except OSError as e:
            message(t("err_autostart", err=e))
        self.tray.update_menu()

    def watch_pin(self):
        """Co chwile przypina okna emulatora (gdy emulator dopiero sie uruchomil/zrestartowal)."""
        while True:
            time.sleep(1.5)
            if self.cfg.get("pin_emulator"):
                try:
                    pin_windows(True)
                except Exception:
                    pass

    def quit(self):
        try:
            pin_windows(False)  # po wyjsciu nie zostawiamy przypietego okna
        except Exception:
            pass
        self.tray.stop()
        self.ui(self.root.destroy)


def main():
    first, ev = acquire_single_instance(signal_launch="--no-launch" not in sys.argv)
    if not first:
        return
    App(ev)


if __name__ == "__main__":
    main()
