# HAUSEL v0.4 - One-way platforms | LGStudio

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.uix.switch import Switch
from kivy.uix.progressbar import ProgressBar
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle, RoundedRectangle, Ellipse, Triangle, Line
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
from kivy.metrics import dp, sp
from kivy.utils import get_color_from_hex, platform
from kivy.core.audio import SoundLoader
import random
import os

if platform not in ("android", "ios"):
    Window.size = (360, 740)
Window.clearcolor = (0.40, 0.78, 0.98, 1)

def asset(name):
    base = os.path.dirname(os.path.abspath(__file__))
    for p in (os.path.join(base, "assets", name), os.path.join(base, name)):
        if os.path.exists(p):
            return p
    return os.path.join(base, "assets", name)

from kivy.core.text import LabelBase
UI_FONT = "Roboto"
try:
    _ff = asset("fonts/Fredoka-Bold.ttf")
    if os.path.exists(_ff):
        LabelBase.register(name="Fredoka", fn_regular=_ff)
        UI_FONT = "Fredoka"
except Exception:
    pass

class OutlinedLabel(Label):
    def __init__(self, **kw):
        ow = kw.pop("outline_width", 2)
        oc = kw.pop("outline_color", (0, 0, 0, 1))
        kw.setdefault("color", (1, 1, 1, 1))
        kw.setdefault("font_name", UI_FONT)
        kw.setdefault("bold", True)
        super().__init__(**kw)
        self.outline_width = ow
        self.outline_color = oc

def do_vibrate(ms=30):
    try:
        if platform == "android":
            from jnius import autoclass
            act = autoclass("org.kivy.android.PythonActivity").mActivity
            Ctx = autoclass("android.content.Context")
            v = act.getSystemService(Ctx.VIBRATOR_SERVICE)
            if v:
                v.vibrate(int(ms))
    except Exception:
        pass

_sounds = {}
_menu = None

def load_audio():
    global _menu
    for k, f in [("jump", "jump.wav"), ("land", "land.wav"), ("death", "death.wav"),
                 ("win", "win.wav"), ("click", "click.wav")]:
        try:
            s = SoundLoader.load(asset(f))
            if s:
                s.volume = 0.4
                _sounds[k] = s
        except Exception:
            pass
    try:
        _menu = SoundLoader.load(asset("menu.wav"))
        if _menu:
            _menu.loop = True
            _menu.volume = 0.25
    except Exception:
        pass

def sfx(n, on=True):
    if not on:
        return
    s = _sounds.get(n)
    if s:
        try:
            s.stop()
            s.play()
        except Exception:
            pass

def menu_music(on):
    if not _menu:
        return
    try:
        if on:
            if _menu.state != "play":
                _menu.play()
        else:
            _menu.stop()
    except Exception:
        pass

store = JsonStore("game_data.json")
DEFAULT = {
    "cups": 0, "unlocked_levels": 1,
    "selected_skin": "default", "selected_trail": "none",
    "owned_skins": ["default"], "owned_trails": ["none"],
    "music_on": True, "vibration_on": True, "sound_on": True,
    "used_codes": [],
}

def _fresh_progress():
    d = DEFAULT.copy()
    d["owned_skins"] = ["default"]
    d["owned_trails"] = ["none"]
    d["used_codes"] = []
    return d

def _new_acc_id():
    import time
    return "acc_" + str(int(time.time() * 1000))

def _load_db():
    """Multi-account database stored locally."""
    if store.exists("db"):
        db = dict(store.get("db"))
        if "accounts" not in db or not db["accounts"]:
            aid = _new_acc_id()
            db = {
                "accounts": [{"id": aid, "name": "Игрок 1", "data": _fresh_progress()}],
                "current_id": aid,
            }
            store.put("db", **db)
        return db
    # migrate old single-player save if present
    if store.exists("player"):
        old = dict(store.get("player"))
        aid = _new_acc_id()
        db = {
            "accounts": [{"id": aid, "name": "Игрок 1", "data": old}],
            "current_id": aid,
        }
        store.put("db", **db)
        return db
    aid = _new_acc_id()
    db = {
        "accounts": [{"id": aid, "name": "Игрок 1", "data": _fresh_progress()}],
        "current_id": aid,
    }
    store.put("db", **db)
    return db

def _save_db(db):
    store.put("db", **db)

def load_data():
    db = _load_db()
    cid = db.get("current_id")
    for acc in db.get("accounts", []):
        if acc.get("id") == cid:
            d = _fresh_progress()
            d.update(acc.get("data") or {})
            for k in ("owned_skins", "owned_trails", "used_codes"):
                if not isinstance(d.get(k), list):
                    d[k] = list(DEFAULT[k])
            d["_account_id"] = acc["id"]
            d["_account_name"] = acc.get("name", "Игрок")
            return d
    # fallback first account
    if db.get("accounts"):
        acc = db["accounts"][0]
        db["current_id"] = acc["id"]
        _save_db(db)
        d = _fresh_progress()
        d.update(acc.get("data") or {})
        d["_account_id"] = acc["id"]
        d["_account_name"] = acc.get("name", "Игрок")
        return d
    return _fresh_progress()

def save_data(d):
    db = _load_db()
    cid = d.get("_account_id") or db.get("current_id")
    # strip internal keys before saving progress
    progress = {k: v for k, v in d.items() if not k.startswith("_")}
    for acc in db.get("accounts", []):
        if acc.get("id") == cid:
            acc["data"] = progress
            break
    _save_db(db)

def list_accounts():
    db = _load_db()
    return list(db.get("accounts", [])), db.get("current_id")

def create_account(name):
    name = (name or "").strip() or "Игрок"
    db = _load_db()
    aid = _new_acc_id()
    db.setdefault("accounts", []).append({
        "id": aid, "name": name[:20], "data": _fresh_progress()
    })
    db["current_id"] = aid
    _save_db(db)
    return aid

def switch_account(aid):
    db = _load_db()
    for acc in db.get("accounts", []):
        if acc.get("id") == aid:
            db["current_id"] = aid
            _save_db(db)
            return True
    return False

def delete_account(aid):
    db = _load_db()
    accs = db.get("accounts", [])
    if len(accs) <= 1:
        return False  # keep at least one
    db["accounts"] = [a for a in accs if a.get("id") != aid]
    if db.get("current_id") == aid:
        db["current_id"] = db["accounts"][0]["id"]
    _save_db(db)
    return True

def rename_account(aid, name):
    name = (name or "").strip() or "Игрок"
    db = _load_db()
    for acc in db.get("accounts", []):
        if acc.get("id") == aid:
            acc["name"] = name[:20]
            _save_db(db)
            return True
    return False

PROMO = {"YAULTRA": {"cups": 10000}}

THEMES = [
    {"name": "Moss Valley",  "c": "#7BC98A", "bg": "#1E3D2A", "plat": "#4FAA5E", "haz": "#E05555"},
    {"name": "Pine Ridge",   "c": "#9BC96A", "bg": "#263C1A", "plat": "#6FAA48", "haz": "#E08840"},
    {"name": "Teal Shores",  "c": "#55C8C0", "bg": "#1A3C3C", "plat": "#38A098", "haz": "#E06890"},
    {"name": "Sky Bridge",   "c": "#6AB8D8", "bg": "#1A3444", "plat": "#4898C0", "haz": "#E09840"},
    {"name": "Deep Blue",    "c": "#6A9CD8", "bg": "#1A2C44", "plat": "#4870B0", "haz": "#E05050"},
    {"name": "Night Indigo", "c": "#8A8AD8", "bg": "#222244", "plat": "#5858B0", "haz": "#E08840"},
    {"name": "Grape Wall",   "c": "#A880D8", "bg": "#2A1C44", "plat": "#7050B0", "haz": "#E05070"},
    {"name": "Orchid Path",  "c": "#C870B8", "bg": "#321C30", "plat": "#904088", "haz": "#E06060"},
    {"name": "Rose Gate",    "c": "#E07098", "bg": "#321C28", "plat": "#A84060", "haz": "#E0B040"},
    {"name": "Coral Peak",   "c": "#E08080", "bg": "#321C1C", "plat": "#A85050", "haz": "#40C0C0"},
]

def theme(lv):
    return THEMES[(lv - 1) % 10].copy()

SKINS = {
    "default": {"name": "Classic", "price": 0, "bonus": 1.0, "color": "#FFF8F0"},
    "red": {"name": "Crimson", "price": 50, "bonus": 1.1, "color": "#FF6B6B"},
    "blue": {"name": "Ocean", "price": 80, "bonus": 1.15, "color": "#4ECDC4"},
    "gold": {"name": "Golden", "price": 150, "bonus": 1.3, "color": "#FFD93D"},
    "neon": {"name": "Neon", "price": 250, "bonus": 1.5, "color": "#6BCB77"},
    "shadow": {"name": "Shadow", "price": 400, "bonus": 1.8, "color": "#A78BFA"},
}
TRAILS = {
    "none": {"name": "No Trail", "price": 0, "bonus": 1.0, "color": "#888"},
    "white": {"name": "White Dust", "price": 40, "bonus": 1.05, "color": "#FFF"},
    "fire": {"name": "Fire Trail", "price": 100, "bonus": 1.2, "color": "#FF7A3A"},
    "ice": {"name": "Ice Trail", "price": 120, "bonus": 1.25, "color": "#4ECDC4"},
    "rainbow": {"name": "Rainbow", "price": 300, "bonus": 1.6, "color": "#FF6BCB"},
    "stars": {"name": "Star Dust", "price": 500, "bonus": 2.0, "color": "#FFD93D"},
}

class Btn(Button):
    """Bright button: shadow + outline + press scale animation."""
    def __init__(self, bg=(0.35, 0.65, 1.0, 1), **kw):
        super().__init__(**kw)
        self.background_normal = self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.color = (1, 1, 1, 1)
        self.font_size = sp(15)
        self.bold = True
        self.font_name = UI_FONT
        self.outline_width = 2
        self.outline_color = (0.05, 0.05, 0.12, 1)
        self._bg = list(bg)
        with self.canvas.before:
            # soft shadow
            Color(0, 0, 0, 0.28)
            self._shadow = RoundedRectangle(radius=[dp(14)])
            # dark outline
            Color(0.08, 0.08, 0.14, 1)
            self._border = RoundedRectangle(radius=[dp(14)])
            # fill
            Color(*bg)
            self._fill = RoundedRectangle(radius=[dp(12)])
        self.bind(pos=self._upd_btn, size=self._upd_btn)
        self.bind(on_press=self._anim_down, on_release=self._anim_up)

    def _upd_btn(self, *a):
        sh = 4 if not getattr(self, "_pressed", False) else 1
        self._shadow.pos = (self.x + 2, self.y - sh)
        self._shadow.size = (self.width, self.height)
        self._border.pos = (self.x - 2, self.y - 2)
        self._border.size = (self.width + 4, self.height + 4)
        self._fill.pos = self.pos
        self._fill.size = self.size

    def _anim_down(self, *a):
        self._pressed = True
        from kivy.animation import Animation
        Animation(opacity=0.85, duration=0.06, t="out_quad").start(self)
        self._upd_btn()

    def _anim_up(self, *a):
        self._pressed = False
        from kivy.animation import Animation
        Animation(opacity=1, duration=0.1, t="out_quad").start(self)
        self._upd_btn()

class NavBtn(Button):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.background_normal = self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.color = (1, 1, 1, 1)
        self.font_size = sp(14)
        self.bold = True
        self.font_name = UI_FONT
        self.outline_width = 2
        self.outline_color = (0, 0, 0, 1)

class LevelCard(Button):
    def __init__(self, lv, th, unlocked, **kw):
        super().__init__(**kw)
        self.lv, self.th, self.unlocked = lv, th, unlocked
        self.background_normal = self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.size_hint = (1, None)
        self.height = dp(58)
        self.bind(pos=self._d, size=self._d)

    def _d(self, *a):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.unlocked:
                bg = get_color_from_hex(self.th["bg"])
                pl = get_color_from_hex(self.th["plat"])
                Color(*bg)
                RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
                Color(pl[0], pl[1], pl[2], 0.95)
                x, y, w, h = self.x, self.y, self.width, self.height
                # drawn-looking platform lines
                Rectangle(pos=(x + w * 0.08, y + h * 0.35), size=(w * 0.28, h * 0.12))
                Rectangle(pos=(x + w * 0.42, y + h * 0.55), size=(w * 0.22, h * 0.12))
                Rectangle(pos=(x + w * 0.7, y + h * 0.3), size=(w * 0.2, h * 0.12))
            else:
                Color(0.15, 0.13, 0.22, 1)
                RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
                Color(0.28, 0.25, 0.35, 1)
                x, y, w, h = self.x, self.y, self.width, self.height
                Rectangle(pos=(x + w * 0.08, y + h * 0.35), size=(w * 0.28, h * 0.12))
                Rectangle(pos=(x + w * 0.42, y + h * 0.55), size=(w * 0.22, h * 0.12))


# ========== LOADING ==========
class LoadingScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = FloatLayout()
        with root.canvas.before:
            Color(0.40, 0.78, 0.98, 1)
            self.bg = Rectangle()
            Color(0.55, 0.4, 0.95, 0.14)
            self.c1 = Ellipse()
            Color(0.95, 0.45, 0.6, 0.1)
            self.c2 = Ellipse()
        root.bind(size=self._u, pos=self._u)
        root.add_widget(Label(text="HAUSEL", font_size=sp(50), bold=True, color=(1, 0.96, 0.92, 1),
                              size_hint=(1, None), height=dp(60), pos_hint={"center_x": 0.5, "center_y": 0.6}))
        root.add_widget(Label(text="by LGStudio", font_size=sp(15), color=(0.8, 0.7, 0.95, 1),
                              size_hint=(1, None), height=dp(26), pos_hint={"center_x": 0.5, "center_y": 0.52}))
        self.bar = ProgressBar(max=100, size_hint=(0.68, None), height=dp(9),
                               pos_hint={"center_x": 0.5, "center_y": 0.36})
        root.add_widget(self.bar)
        self.lbl = Label(text="Loading...", font_size=sp(13), color=(0.75, 0.7, 0.9, 1),
                         size_hint=(1, None), height=dp(26), pos_hint={"center_x": 0.5, "center_y": 0.3})
        root.add_widget(self.lbl)
        self.add_widget(root)
        self.v = 0

    def _u(self, *a):
        self.bg.pos, self.bg.size = self.pos, self.size
        self.c1.pos = (self.width * 0.5, self.height * 0.65)
        self.c1.size = (self.width * 0.5, self.width * 0.5)
        self.c2.pos = (-self.width * 0.1, 0)
        self.c2.size = (self.width * 0.4, self.width * 0.4)

    def on_enter(self):
        self.v = 0
        load_audio()
        Clock.schedule_interval(self._t, 0.025)

    def _t(self, dt):
        self.v += random.uniform(2.5, 5)
        if self.v >= 100:
            self.bar.value = 100
            self.lbl.text = "Let's climb!"
            Clock.unschedule(self._t)
            Clock.schedule_once(lambda dt: (
                setattr(self.manager, "transition", FadeTransition(duration=0.28)),
                setattr(self.manager, "current", "main")
            ), 0.3)
            return False
        self.bar.value = self.v
        self.lbl.text = "Loading" + "." * (int(self.v / 12) % 4)
        return True


# ========== MAIN ==========
class MainScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.data = load_data()
        self.tab = "play"
        col = BoxLayout(orientation="vertical")
        self.body = FloatLayout(size_hint=(1, 1))
        col.add_widget(self.body)
        self.nav = BoxLayout(size_hint=(1, None), height=dp(66), padding=[dp(6), dp(6)], spacing=dp(4))
        with self.nav.canvas.before:
            Color(0.25, 0.55, 0.95, 1)
            self.nbg = Rectangle()
            Color(1, 1, 1, 0.35)
            self.nln = Rectangle(size=(0, 3))
        self.nav.bind(pos=self._nu, size=self._nu)
        self.bs = NavBtn(text="SHOP")
        self.bp = NavBtn(text="PLAY")
        self.bt = NavBtn(text="SETTINGS")
        self.bs.bind(on_press=lambda x: self.sw("shop"))
        self.bp.bind(on_press=lambda x: self.sw("play"))
        self.bt.bind(on_press=lambda x: self.sw("settings"))
        for b in (self.bs, self.bp, self.bt):
            self.nav.add_widget(b)
        col.add_widget(self.nav)
        self.add_widget(col)
        with self.canvas.before:
            Color(0.40, 0.78, 0.98, 1)
            self.sbg = Rectangle()
        self.bind(pos=lambda *a: (setattr(self.sbg, "pos", self.pos), setattr(self.sbg, "size", self.size)),
                  size=lambda *a: (setattr(self.sbg, "pos", self.pos), setattr(self.sbg, "size", self.size)))
        self.wshop = self._shop()
        self.wplay = self._play()
        self.wset = self._set()
        self.sw("play")

    def _nu(self, *a):
        self.nbg.pos, self.nbg.size = self.nav.pos, self.nav.size
        self.nln.pos = (self.nav.x, self.nav.top - 3)
        self.nln.size = (self.nav.width, 3)

    def on_enter(self, *a):
        self.data = load_data()
        if self.data.get("music_on", True):
            menu_music(True)
        if self.tab == "shop":
            self._rs()
        elif self.tab == "play":
            self._rp()

    def on_leave(self, *a):
        menu_music(False)

    def sw(self, tab):
        if self.data.get("vibration_on"):
            do_vibrate(14)
        sfx("click", self.data.get("sound_on", True))
        self.tab = tab
        self.body.clear_widgets()
        for b in (self.bs, self.bp, self.bt):
            b.color = (0.7, 0.65, 0.85, 1)
        if tab == "shop":
            self.wshop.size_hint = (1, 1)
            self.body.add_widget(self.wshop)
            self.bs.color = (1, 0.9, 0.4, 1)
            self._rs()
        elif tab == "play":
            self.wplay.size_hint = (1, 1)
            self.body.add_widget(self.wplay)
            self.bp.color = (0.5, 1, 0.7, 1)
            self._rp()
        else:
            self.wset.size_hint = (1, 1)
            self.body.add_widget(self.wset)
            self.bt.color = (0.75, 0.85, 1, 1)
            self.data = load_data()
            self._refresh_accounts()
            if hasattr(self, "_sync_set_btns"):
                self._sync_set_btns()

    def _shop(self):
        root = BoxLayout(orientation="vertical", padding=[dp(12), dp(10), dp(12), dp(6)], spacing=dp(8))
        head = BoxLayout(size_hint=(1, None), height=dp(44))
        head.add_widget(OutlinedLabel(text="МАГАЗИН", font_size=sp(24), size_hint=(0.5, 1),
                                      halign="left", valign="middle"))
        self.cups_l = OutlinedLabel(text="Cups: 0", font_size=sp(16), size_hint=(0.5, 1),
                                    color=(1, 0.92, 0.35, 1), halign="right", valign="middle")
        self.cups_l.bind(size=self.cups_l.setter("text_size"))
        head.add_widget(self.cups_l)
        root.add_widget(head)

        sc = ScrollView(size_hint=(1, 1), do_scroll_x=False, bar_width=dp(4))
        self.shop_scroll_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10),
                                         padding=[0, 0, 0, dp(24)])
        self.shop_scroll_box.bind(minimum_height=self.shop_scroll_box.setter("height"))
        self.sbox = GridLayout(cols=2, size_hint_y=None, spacing=dp(10),
                               padding=[dp(4), dp(4)], row_default_height=dp(130),
                               row_force_default=True)
        self.sbox.bind(minimum_height=self.sbox.setter("height"))
        self.shop_scroll_box.add_widget(self.sbox)

        # Promo at the END of scroll — always last item in shop
        promo_box = BoxLayout(orientation="vertical", size_hint=(1, None), height=dp(110), spacing=dp(6))
        with promo_box.canvas.before:
            Color(0.25, 0.5, 0.95, 1)
            pr = RoundedRectangle(radius=[dp(14)])
        promo_box.bind(pos=lambda *a, r=pr, b=promo_box: setattr(r, "pos", b.pos) or setattr(r, "size", b.size),
                       size=lambda *a, r=pr, b=promo_box: setattr(r, "pos", b.pos) or setattr(r, "size", b.size))
        promo_box.add_widget(OutlinedLabel(text="Промокод", font_size=sp(14), size_hint=(1, None), height=dp(22)))
        prow = BoxLayout(size_hint=(1, None), height=dp(42), spacing=dp(8), padding=[dp(8), 0])
        self.code_in = TextInput(
            hint_text="Введи код...", multiline=False, font_size=sp(14),
            size_hint=(0.55, 1), background_color=(0.15, 0.35, 0.75, 1),
            foreground_color=(1, 1, 1, 1), cursor_color=(1, 1, 1, 1),
            padding=[dp(10), dp(10)]
        )
        prow.add_widget(self.code_in)
        okb = Btn(text="Активировать", bg=(0.3, 0.85, 0.45, 1), size_hint=(0.45, 1))
        okb.font_size = sp(12)
        okb.bind(on_press=self._code)
        prow.add_widget(okb)
        promo_box.add_widget(prow)
        self.code_msg = OutlinedLabel(text="", font_size=sp(12), size_hint=(1, None), height=dp(22),
                                      color=(1, 0.95, 0.4, 1))
        promo_box.add_widget(self.code_msg)
        self.shop_scroll_box.add_widget(promo_box)

        sc.add_widget(self.shop_scroll_box)
        root.add_widget(sc)
        return root

    def _rs(self):
        self.cups_l.text = f"Cups: {self.data['cups']}"
        self.sbox.clear_widgets()
        # skins cards
        for k, s in SKINS.items():
            self.sbox.add_widget(self._card(s["name"], f"x{s['bonus']}" if s["bonus"] > 1 else "base",
                                            s["price"], k in self.data["owned_skins"],
                                            self.data["selected_skin"] == k, s["color"], "skin", k))
        for k, t in TRAILS.items():
            self.sbox.add_widget(self._card(t["name"], f"x{t['bonus']}" if t["bonus"] > 1 else "—",
                                            t["price"], k in self.data["owned_trails"],
                                            self.data["selected_trail"] == k, t["color"], "trail", k))

    def _card(self, title, sub, price, owned, sel, color, typ, key):
        box = BoxLayout(orientation="vertical", size_hint=(1, None), height=dp(130),
                        padding=[dp(8), dp(8)], spacing=dp(4))
        with box.canvas.before:
            Color(0, 0, 0, 0.2)
            self_sh = RoundedRectangle(radius=[dp(16)])
            Color(1, 1, 1, 1)
            self_bd = RoundedRectangle(radius=[dp(16)])
            Color(0.92, 0.95, 1, 1)
            self_fl = RoundedRectangle(radius=[dp(14)])
        def _u(*a, b=box, sh=self_sh, bd=self_bd, fl=self_fl):
            sh.pos = (b.x + 2, b.y - 3)
            sh.size = b.size
            bd.pos = (b.x - 1, b.y - 1)
            bd.size = (b.width + 2, b.height + 2)
            fl.pos = b.pos
            fl.size = b.size
        box.bind(pos=_u, size=_u)

        col = get_color_from_hex(color)
        prev = Widget(size_hint=(1, None), height=dp(44))
        with prev.canvas:
            Color(*col)
            el = Ellipse()
        prev.bind(pos=lambda *a, e=el, w=prev: setattr(e, "pos", (w.center_x - dp(18), w.y + 4)),
                  size=lambda *a, e=el, w=prev: setattr(e, "size", (dp(36), dp(36))))
        box.add_widget(prev)
        box.add_widget(OutlinedLabel(text=title, font_size=sp(13), size_hint=(1, None), height=dp(22),
                                     color=(0.15, 0.2, 0.35, 1), outline_color=(1, 1, 1, 0.5)))
        box.add_widget(OutlinedLabel(text=sub, font_size=sp(11), size_hint=(1, None), height=dp(16),
                                     color=(0.4, 0.45, 0.6, 1), outline_width=1))
        if sel:
            b = Btn(text="ON", bg=(0.3, 0.8, 0.45, 1), size_hint=(1, None), height=dp(28))
            b.disabled = True
        elif owned:
            b = Btn(text="USE", bg=(0.35, 0.6, 1, 1), size_hint=(1, None), height=dp(28))
            b.bind(on_press=lambda x, t=typ, k=key: self._sel(t, k))
        else:
            b = Btn(text=str(price), bg=(1, 0.7, 0.25, 1), size_hint=(1, None), height=dp(28))
            b.bind(on_press=lambda x, t=typ, k=key, p=price: self._buy(t, k, p))
        b.font_size = sp(12)
        box.add_widget(b)
        return box

    def _buy(self, typ, key, price):
        if self.data["cups"] < price:
            return
        if self.data.get("vibration_on"):
            do_vibrate(20)
        sfx("click", self.data.get("sound_on", True))
        self.data["cups"] -= price
        if typ == "skin":
            if key not in self.data["owned_skins"]:
                self.data["owned_skins"].append(key)
            self.data["selected_skin"] = key
        else:
            if key not in self.data["owned_trails"]:
                self.data["owned_trails"].append(key)
            self.data["selected_trail"] = key
        save_data(self.data)
        self._rs()

    def _sel(self, typ, key):
        if self.data.get("vibration_on"):
            do_vibrate(14)
        sfx("click", self.data.get("sound_on", True))
        if typ == "skin":
            self.data["selected_skin"] = key
        else:
            self.data["selected_trail"] = key
        save_data(self.data)
        self._rs()

    def _code(self, *a):
        code = self.code_in.text.strip().upper()
        self.code_in.text = ""

        if not code:
            self.code_msg.color = (1, 0.55, 0.45, 1)
            self.code_msg.text = "Введи промокод"
            return

        if code in self.data.get("used_codes", []):
            self.code_msg.color = (1, 0.7, 0.4, 1)
            self.code_msg.text = "Этот код уже использован"
            return

        if code not in PROMO:
            self.code_msg.color = (1, 0.45, 0.4, 1)
            self.code_msg.text = "Такого промокода нет"
            if self.data.get("vibration_on"):
                do_vibrate(20)
            return

        reward = PROMO[code]
        if self.data.get("vibration_on"):
            do_vibrate(40)
        sfx("win", self.data.get("sound_on", True))

        got = []
        if "cups" in reward:
            self.data["cups"] += reward["cups"]
            got.append(f"+{reward['cups']} кубков")
        if "skin" in reward:
            sk = reward["skin"]
            if sk not in self.data["owned_skins"]:
                self.data["owned_skins"].append(sk)
            self.data["selected_skin"] = sk
            got.append(f"скин {sk}")
        if "trail" in reward:
            tr = reward["trail"]
            if tr not in self.data["owned_trails"]:
                self.data["owned_trails"].append(tr)
            self.data["selected_trail"] = tr
            got.append(f"след {tr}")

        self.data.setdefault("used_codes", []).append(code)
        save_data(self.data)
        self.code_msg.color = (0.45, 1, 0.55, 1)
        self.code_msg.text = "Активировано: " + ", ".join(got)
        self._rs()

    def _play(self):
        """Home screen: big character + big PLAY + level chips."""
        root = FloatLayout()

        # cups top
        self.pc = OutlinedLabel(
            text="Cups: 0", font_size=sp(18), color=(1, 0.92, 0.3, 1),
            size_hint=(None, None), size=(dp(200), dp(36)),
            pos_hint={"center_x": 0.5, "top": 0.97}
        )
        root.add_widget(self.pc)

        # big character preview (drawn)
        self.char_preview = Widget(size_hint=(None, None), size=(dp(140), dp(160)),
                                   pos_hint={"center_x": 0.5, "center_y": 0.58})
        self.char_preview.bind(pos=self._draw_char, size=self._draw_char)
        root.add_widget(self.char_preview)

        self.home_name = OutlinedLabel(
            text="Level 1", font_size=sp(16),
            size_hint=(None, None), size=(dp(220), dp(30)),
            pos_hint={"center_x": 0.5, "center_y": 0.40}
        )
        root.add_widget(self.home_name)

        # big yellow PLAY button
        playb = Btn(text="▶  PLAY", bg=(1.0, 0.85, 0.15, 1),
                    size_hint=(None, None), size=(dp(180), dp(64)),
                    pos_hint={"center_x": 0.5, "center_y": 0.28})
        playb.font_size = sp(22)
        playb.color = (0.15, 0.15, 0.2, 1)
        playb.outline_color = (0.1, 0.1, 0.15, 1)
        playb.bind(on_press=self._home_play)
        root.add_widget(playb)

        # level select strip
        lv_row = BoxLayout(size_hint=(1, None), height=dp(50),
                           pos_hint={"x": 0, "y": 0.06}, padding=[dp(10), 0], spacing=dp(6))
        self.lv_chip_box = BoxLayout(spacing=dp(6), size_hint=(None, 1))
        self.lv_chip_box.bind(minimum_width=self.lv_chip_box.setter("width"))
        sc = ScrollView(size_hint=(1, 1), do_scroll_y=False, bar_width=0)
        sc.add_widget(self.lv_chip_box)
        lv_row.add_widget(sc)
        root.add_widget(lv_row)
        return root

    def _draw_char(self, *a):
        w = self.char_preview
        w.canvas.clear()
        skin = SKINS.get(self.data.get("selected_skin", "default"), SKINS["default"])
        pc = get_color_from_hex(skin["color"])
        with w.canvas:
            # soft shadow
            Color(0, 0, 0, 0.2)
            Ellipse(pos=(w.x + dp(20), w.y + dp(8)), size=(dp(100), dp(30)))
            # legs
            Color(pc[0] * 0.7, pc[1] * 0.7, pc[2] * 0.7, 1)
            Rectangle(pos=(w.x + dp(48), w.y + dp(30)), size=(dp(18), dp(36)))
            Rectangle(pos=(w.x + dp(74), w.y + dp(30)), size=(dp(18), dp(36)))
            # body
            Color(*pc)
            RoundedRectangle(pos=(w.x + dp(40), w.y + dp(60)), size=(dp(60), dp(50)), radius=[dp(12)])
            # head
            Color(min(1, pc[0] * 1.1), min(1, pc[1] * 1.1), min(1, pc[2] * 1.1), 1)
            Ellipse(pos=(w.x + dp(42), w.y + dp(100)), size=(dp(56), dp(56)))
            # eyes
            Color(0.1, 0.1, 0.15, 1)
            Ellipse(pos=(w.x + dp(54), w.y + dp(124)), size=(dp(12), dp(12)))
            Ellipse(pos=(w.x + dp(74), w.y + dp(124)), size=(dp(12), dp(12)))
            Color(1, 1, 1, 1)
            Ellipse(pos=(w.x + dp(57), w.y + dp(128)), size=(dp(5), dp(5)))
            Ellipse(pos=(w.x + dp(77), w.y + dp(128)), size=(dp(5), dp(5)))

    def _rp(self):
        self.data = load_data()
        self.pc.text = f"Cups: {self.data['cups']}"
        un = self.data.get("unlocked_levels", 1)
        self.home_name.text = f"Level {min(un, 100)}"
        self.selected_level = min(un, 100)
        self._draw_char()
        self.lv_chip_box.clear_widgets()
        for lv in range(1, min(un, 100) + 1):
            th = theme(lv)
            col = get_color_from_hex(th["c"])
            b = Btn(text=str(lv), bg=col, size_hint=(None, None), size=(dp(44), dp(44)))
            b.font_size = sp(14)
            b.bind(on_press=lambda x, l=lv: self._pick_lv(l))
            self.lv_chip_box.add_widget(b)

    def _pick_lv(self, lv):
        self.selected_level = lv
        self.home_name.text = f"Level {lv}"
        if self.data.get("vibration_on"):
            do_vibrate(12)
        sfx("click", self.data.get("sound_on", True))

    def _home_play(self, *a):
        lv = getattr(self, "selected_level", 1)
        self._go(lv)

    def _go(self, level):
        if self.data.get("vibration_on"):
            do_vibrate(18)
        sfx("click", self.data.get("sound_on", True))
        menu_music(False)
        g = self.manager.get_screen("game")
        g.setup(level, self.data)
        self.manager.transition = SlideTransition(direction="up", duration=0.2)
        self.manager.current = "game"

    def _set(self):
        root = BoxLayout(orientation="vertical", padding=[dp(14), dp(10)], spacing=dp(8))
        root.add_widget(Label(text="SETTINGS", font_size=sp(22), bold=True, color=(0.75, 0.85, 1, 1),
                              size_hint=(1, None), height=dp(36)))

        self.acc_label = Label(text="", font_size=sp(13), color=(1, 0.9, 0.5, 1),
                               size_hint=(1, None), height=dp(22), halign="left")
        self.acc_label.bind(size=self.acc_label.setter("text_size"))
        root.add_widget(self.acc_label)

        root.add_widget(Label(text="АККАУНТЫ", font_size=sp(12), bold=True,
                              color=(0.8, 0.75, 1, 1), size_hint=(1, None), height=dp(20)))
        sc = ScrollView(size_hint=(1, None), height=dp(130), do_scroll_x=False, bar_width=dp(3))
        self.acc_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(5))
        self.acc_box.bind(minimum_height=self.acc_box.setter("height"))
        sc.add_widget(self.acc_box)
        root.add_widget(sc)

        crow = BoxLayout(size_hint=(1, None), height=dp(40), spacing=dp(6))
        self.acc_name_in = TextInput(
            hint_text="Имя нового аккаунта", multiline=False, font_size=sp(13),
            size_hint=(0.55, 1), background_color=(0.25, 0.2, 0.4, 1),
            foreground_color=(1, 1, 1, 1), cursor_color=(1, 1, 1, 1),
            padding=[dp(8), dp(8)]
        )
        crow.add_widget(self.acc_name_in)
        cb = Btn(text="Создать", bg=(0.3, 0.65, 0.4, 1), size_hint=(0.45, 1))
        cb.font_size = sp(13)
        cb.bind(on_press=self._acc_create)
        crow.add_widget(cb)
        root.add_widget(crow)

        self.acc_msg = Label(text="", font_size=sp(11), color=(0.7, 0.9, 0.7, 1),
                             size_hint=(1, None), height=dp(18))
        root.add_widget(self.acc_msg)

        # 2x2 settings grid (like reference)
        grid = GridLayout(cols=2, size_hint=(1, None), height=dp(150), spacing=dp(10),
                          padding=[dp(4), dp(4)])
        self.btn_sound = Btn(text="ЗВУК\nВКЛ", bg=(0.35, 0.7, 1, 1), size_hint=(1, 1))
        self.btn_music = Btn(text="МУЗЫКА\nВКЛ", bg=(0.45, 0.55, 1, 1), size_hint=(1, 1))
        self.btn_vib = Btn(text="ВИБРАЦИЯ\nВКЛ", bg=(0.4, 0.85, 0.55, 1), size_hint=(1, 1))
        self.btn_reset = Btn(text="СБРОС\nПРОГРЕССА", bg=(1, 0.4, 0.4, 1), size_hint=(1, 1))
        for b in (self.btn_sound, self.btn_music, self.btn_vib, self.btn_reset):
            b.font_size = sp(13)
        self.btn_sound.bind(on_press=self._tap_sound)
        self.btn_music.bind(on_press=self._tap_music)
        self.btn_vib.bind(on_press=self._tap_vib)
        self.btn_reset.bind(on_press=self._reset)
        grid.add_widget(self.btn_sound)
        grid.add_widget(self.btn_music)
        grid.add_widget(self.btn_vib)
        grid.add_widget(self.btn_reset)
        root.add_widget(grid)

        # keep switches for internal state sync (hidden)
        self.sw_music_on = Switch(active=True, size_hint=(None, None), size=(0, 0), opacity=0)
        self.sw_sound_on = Switch(active=True, size_hint=(None, None), size=(0, 0), opacity=0)
        self.sw_vibration_on = Switch(active=True, size_hint=(None, None), size=(0, 0), opacity=0)

        root.add_widget(Widget(size_hint=(1, 1)))
        info = OutlinedLabel(text="HAUSEL  v0.7\nby LGStudio", font_size=sp(12),
                             size_hint=(1, None), height=dp(40), color=(1, 1, 1, 0.85))
        root.add_widget(info)
        return root

    def _sync_set_btns(self):
        def mark(btn, on, on_bg, off_bg, label):
            btn.text = f"{label}\n{'ВКЛ' if on else 'ВЫКЛ'}"
            btn._bg = list(on_bg if on else off_bg)
            try:
                btn._fill.rgba = (*btn._bg,) if hasattr(btn._fill, 'rgba') else None
            except Exception:
                pass
            from kivy.graphics import Color
            # force redraw fill color
            btn.canvas.before.clear()
            with btn.canvas.before:
                Color(0, 0, 0, 0.28)
                btn._shadow = RoundedRectangle(pos=(btn.x+2, btn.y-4), size=btn.size, radius=[dp(14)])
                Color(0.08, 0.08, 0.14, 1)
                btn._border = RoundedRectangle(pos=(btn.x-2, btn.y-2), size=(btn.width+4, btn.height+4), radius=[dp(14)])
                Color(*btn._bg)
                btn._fill = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(12)])
            btn.bind(pos=btn._upd_btn, size=btn._upd_btn)
        mark(self.btn_sound, self.data.get("sound_on", True), (0.35, 0.7, 1, 1), (0.55, 0.55, 0.65, 1), "ЗВУК")
        mark(self.btn_music, self.data.get("music_on", True), (0.45, 0.55, 1, 1), (0.55, 0.55, 0.65, 1), "МУЗЫКА")
        mark(self.btn_vib, self.data.get("vibration_on", True), (0.4, 0.85, 0.55, 1), (0.55, 0.55, 0.65, 1), "ВИБРАЦИЯ")

    def _tap_sound(self, *a):
        self.data["sound_on"] = not self.data.get("sound_on", True)
        save_data(self.data)
        self._sync_set_btns()
        sfx("click", self.data.get("sound_on", True))

    def _tap_music(self, *a):
        self.data["music_on"] = not self.data.get("music_on", True)
        save_data(self.data)
        menu_music(self.data["music_on"])
        self._sync_set_btns()
        sfx("click", self.data.get("sound_on", True))

    def _tap_vib(self, *a):
        self.data["vibration_on"] = not self.data.get("vibration_on", True)
        save_data(self.data)
        self._sync_set_btns()
        if self.data["vibration_on"]:
            do_vibrate(25)

    def _refresh_accounts(self):
        if not hasattr(self, "acc_box"):
            return
        accs, cur = list_accounts()
        self.acc_label.text = f"Сейчас: {self.data.get('_account_name', 'Игрок')}"
        self.acc_box.clear_widgets()
        for acc in accs:
            aid = acc["id"]
            is_cur = aid == cur
            row = BoxLayout(size_hint=(1, None), height=dp(38), spacing=dp(4), padding=[dp(6), dp(2)])
            with row.canvas.before:
                Color(*(0.3, 0.26, 0.48, 1) if is_cur else (0.2, 0.17, 0.32, 1))
                rr = RoundedRectangle(radius=[dp(8)])
            row.bind(pos=lambda w, *a, r=rr: setattr(r, "pos", w.pos),
                     size=lambda w, *a, r=rr: setattr(r, "size", w.size))
            cups = (acc.get("data") or {}).get("cups", 0)
            lbl = Label(
                text=f"{'● ' if is_cur else '○ '}{acc.get('name', 'Игрок')} ({cups})",
                font_size=sp(12),
                color=(1, 0.95, 0.9, 1) if is_cur else (0.75, 0.7, 0.85, 1),
                size_hint=(0.55, 1), halign="left", valign="middle"
            )
            lbl.bind(size=lbl.setter("text_size"))
            row.add_widget(lbl)
            if not is_cur:
                sb = Btn(text="Войти", bg=(0.35, 0.5, 0.85, 1), size_hint=(0.25, 1))
                sb.font_size = sp(11)
                sb.bind(on_press=lambda x, a=aid: self._acc_switch(a))
                row.add_widget(sb)
            else:
                row.add_widget(Label(text="активен", font_size=sp(11),
                                     color=(0.5, 0.9, 0.6, 1), size_hint=(0.25, 1)))
            db = Btn(text="X", bg=(0.6, 0.25, 0.3, 1), size_hint=(0.2, 1))
            db.font_size = sp(12)
            db.bind(on_press=lambda x, a=aid: self._acc_del(a))
            row.add_widget(db)
            self.acc_box.add_widget(row)

    def _acc_create(self, *a):
        name = self.acc_name_in.text.strip()
        self.acc_name_in.text = ""
        create_account(name)
        if self.data.get("vibration_on"):
            do_vibrate(25)
        sfx("click", self.data.get("sound_on", True))
        self.data = load_data()
        self.acc_msg.text = f"Создан: {self.data.get('_account_name')}"
        self.acc_msg.color = (0.5, 1, 0.6, 1)
        self._refresh_accounts()
        self.sw_music_on.active = self.data.get("music_on", True)
        self.sw_sound_on.active = self.data.get("sound_on", True)
        self.sw_vibration_on.active = self.data.get("vibration_on", True)

    def _acc_switch(self, aid):
        save_data(self.data)
        switch_account(aid)
        if self.data.get("vibration_on"):
            do_vibrate(20)
        sfx("click", self.data.get("sound_on", True))
        self.data = load_data()
        self.acc_msg.text = f"Вход: {self.data.get('_account_name')}"
        self.acc_msg.color = (0.6, 0.85, 1, 1)
        self._refresh_accounts()
        self.sw_music_on.active = self.data.get("music_on", True)
        self.sw_sound_on.active = self.data.get("sound_on", True)
        self.sw_vibration_on.active = self.data.get("vibration_on", True)
        menu_music(self.data.get("music_on", True))

    def _acc_del(self, aid):
        if not delete_account(aid):
            self.acc_msg.text = "Нельзя удалить единственный аккаунт"
            self.acc_msg.color = (1, 0.55, 0.4, 1)
            return
        if self.data.get("vibration_on"):
            do_vibrate(30)
        self.data = load_data()
        self.acc_msg.text = "Аккаунт удалён"
        self.acc_msg.color = (1, 0.7, 0.5, 1)
        self._refresh_accounts()
        self.sw_music_on.active = self.data.get("music_on", True)
        self.sw_sound_on.active = self.data.get("sound_on", True)
        self.sw_vibration_on.active = self.data.get("vibration_on", True)

    def _tm(self, i, v):
        self.data["music_on"] = v
        save_data(self.data)
        menu_music(v)

    def _ts(self, i, v):
        self.data["sound_on"] = v
        save_data(self.data)

    def _tv(self, i, v):
        self.data["vibration_on"] = v
        save_data(self.data)
        if v:
            do_vibrate(22)

    def _reset(self, *a):
        # reset only current account progress, keep name/id
        aid = self.data.get("_account_id")
        aname = self.data.get("_account_name", "Игрок")
        self.data = _fresh_progress()
        self.data["_account_id"] = aid
        self.data["_account_name"] = aname
        save_data(self.data)
        self.sw_music_on.active = True
        self.sw_sound_on.active = True
        self.sw_vibration_on.active = True
        menu_music(True)
        self.acc_msg.text = "Прогресс аккаунта сброшен"
        self.acc_msg.color = (1, 0.7, 0.5, 1)
        self._refresh_accounts()
        self.sw(self.tab)


# ========== GAME ==========
class Particle:
    def __init__(self, x, y, c, life=0.5):
        self.x, self.y = x, y
        self.vx = random.uniform(-50, 50)
        self.vy = random.uniform(20, 80)
        self.life = self.max = life
        self.c = c
        self.sz = random.uniform(2.5, 5.5)


class GameWorld(Widget):
    """One-way platforms: pass through from below, solid from above."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self._init()
        self._ev = None

    def _init(self):
        self.level = 1
        self.data = {}
        self.th = theme(1)
        self.px = self.py = self.vx = self.vy = 0.0
        self.pw, self.ph = 24, 34
        self.ground = False
        self.face = 1
        self.alive = True
        self.won = False
        self.dtimer = 0
        self.cam = 0.0
        self.plats = []
        self.haz = []
        self.goal = None
        self.wh = 2000
        self.left = self.right = False
        self.jpress = False
        self.jheld = False
        self.jbuf = 0.0
        self.coyote = 0.0
        self.parts = []
        self.ttrail = 0.0
        self.was_g = False
        self.anim_t = 0.0
        self.squash = 1.0  # y scale for land/jump squash-stretch
        # physics tuned for responsive feel
        self.G = -1600
        self.G_FALL = -2200   # heavier when falling
        self.SPEED = 260
        self.ACCEL = 1800
        self.FRICTION = 2000
        self.JUMP = 620
        self.JUMP_CUT = 0.45  # release jump early -> cut velocity
        self.MAXFALL = -700
        self.COYOTE_T = 0.09
        self.JUMP_BUF = 0.12

    def start(self, level, data):
        self._init()
        self.level = level
        self.data = data
        self.th = theme(level)
        self.left = False
        self.right = False
        self.jpress = False
        self._build()
        self._draw()
        if self._ev:
            self._ev.cancel()
        self._ev = Clock.schedule_interval(self.update, 1 / 60)

    def stop(self):
        if self._ev:
            self._ev.cancel()
            self._ev = None

    def _build(self):
        """Full-width style levels with one-way platforms filling the climb."""
        self.plats = []
        self.haz = []
        W = max(float(self.width), 320.0)
        rng = random.Random(self.level * 7919 + 3)

        # Start floor — solid feel, wide
        self.plats.append((W * 0.05, 30, W * 0.9, 14))
        self.px = W / 2 - self.pw / 2
        self.py = 46

        # Vertical spacing: easy early, a bit tighter later but always jumpable
        # jump height ~ 540^2 / 2000 ≈ 146 px
        gap_base = 42
        gap_extra = min(self.level // 12, 12)
        n = 12 + min(self.level // 4, 10)  # more platforms, fuller field

        y = 30.0
        for i in range(n):
            gap = gap_base + gap_extra * (0.5 + 0.5 * rng.random())
            gap = min(gap, 62)  # always reachable
            y += gap

            # Platform width: often wide, sometimes split feel
            # Prefer wide platforms so level feels "full"
            if rng.random() < 0.55:
                # one wide platform
                w = W * (0.45 + 0.4 * rng.random())
                x = (W - w) * rng.random()
                x = max(8, min(W - w - 8, x))
                self.plats.append((x, y, w, 12))
                # occasional spike on top (not whole platform)
                if i >= 3 and self.level >= 5 and rng.random() < min(0.12 + self.level * 0.006, 0.22):
                    hw = min(24, w * 0.25)
                    hx = x + 16 + max(0, (w - hw - 32)) * rng.random()
                    self.haz.append((hx, y + 12, hw, 10))
            else:
                # two platforms side by side (fuller field)
                w1 = W * (0.28 + 0.15 * rng.random())
                w2 = W * (0.28 + 0.15 * rng.random())
                gap_x = 20 + 30 * rng.random()
                total = w1 + gap_x + w2
                if total > W - 16:
                    scale = (W - 16) / total
                    w1 *= scale
                    w2 *= scale
                    gap_x *= scale
                x1 = 8 + (W - 16 - w1 - gap_x - w2) * rng.random()
                x2 = x1 + w1 + gap_x
                self.plats.append((x1, y, w1, 12))
                self.plats.append((x2, y, w2, 12))

        # Goal — wide top platform
        y += 40
        gw = W * 0.75
        gx = (W - gw) / 2
        self.plats.append((gx, y, gw, 14))
        self.goal = (gx + gw * 0.25, y + 14, gw * 0.5, 50)
        self.wh = y + 280

    def update(self, dt):
        if not self.alive:
            self.dtimer += dt
            self._parts(dt)
            self._draw()
            if self.dtimer > 1.0:
                self.start(self.level, self.data)
            return
        if self.won:
            self._parts(dt)
            self._draw()
            return

        dt = min(dt, 0.033)
        self.anim_t += dt

        # --- horizontal: accelerate / friction (no sticky drift) ---
        want = 0.0
        if self.left and not self.right:
            want = -1.0
            self.face = -1
        elif self.right and not self.left:
            want = 1.0
            self.face = 1
        # if both or neither: slow down
        if want != 0:
            self.vx += want * self.ACCEL * dt
            if self.vx > self.SPEED:
                self.vx = self.SPEED
            if self.vx < -self.SPEED:
                self.vx = -self.SPEED
        else:
            if abs(self.vx) <= self.FRICTION * dt:
                self.vx = 0.0
            else:
                self.vx -= (1 if self.vx > 0 else -1) * self.FRICTION * dt

        # --- jump buffer + coyote time ---
        if self.jpress:
            self.jbuf = self.JUMP_BUF
            self.jpress = False
            self.jheld = True
        self.jbuf = max(0.0, self.jbuf - dt)

        if self.ground:
            self.coyote = self.COYOTE_T
        else:
            self.coyote = max(0.0, self.coyote - dt)

        if self.jbuf > 0 and self.coyote > 0:
            self.vy = self.JUMP
            self.ground = False
            self.coyote = 0.0
            self.jbuf = 0.0
            self.squash = 1.25  # stretch up
            sfx("jump", self.data.get("sound_on", True))

        # variable jump height: release early cuts upward speed
        if not self.jheld and self.vy > 0:
            self.vy *= self.JUMP_CUT

        # gravity: stronger when falling for snappy landings
        g = self.G if self.vy > 0 else self.G_FALL
        self.vy += g * dt
        if self.vy < self.MAXFALL:
            self.vy = self.MAXFALL

        self.px += self.vx * dt
        self.px = max(0.0, min(self.width - self.pw, self.px))
        self.py += self.vy * dt

        self.was_g = self.ground
        self.ground = False
        self._collide_oneway()

        if self.ground and not self.was_g:
            self.squash = 0.7  # squash on land
            sfx("land", self.data.get("sound_on", True))

        # recover squash/stretch
        self.squash += (1.0 - self.squash) * min(1.0, 12 * dt)

        if self._hazard():
            self._die()
            return
        if self.py < self.cam - 100:
            self._die()
            return
        if self.goal and self._ov(self.px, self.py, self.pw, self.ph, *self.goal):
            self._win()
            return

        # camera: player in lower part → lots of space above to see next platforms
        target = self.py - self.height * 0.25
        self.cam += (target - self.cam) * min(1.0, 9 * dt)
        if self.cam < 0:
            self.cam = 0

        self.ttrail += dt
        tk = self.data.get("selected_trail", "none")
        if tk != "none" and self.ttrail > 0.03 and (abs(self.vx) > 15 or abs(self.vy) > 30):
            self.ttrail = 0
            c = get_color_from_hex(TRAILS[tk]["color"])
            self.parts.append(Particle(self.px + self.pw / 2, self.py + 3, c, 0.4))

        self._parts(dt)
        self._draw()

    def _collide_oneway(self):
        """One-way: pass through from below, solid from above."""
        if self.vy > 40:  # clearly going up
            return
        feet = self.py
        best = None
        cx = self.px + self.pw / 2
        for (x, y, w, h) in self.plats:
            top = y + h
            # horizontal overlap (center of player over platform)
            if cx < x - 2 or cx > x + w + 2:
                continue
            if feet <= top + 3 and feet >= top - 16:
                if best is None or top > best:
                    best = top
        if best is not None and self.vy <= 20:
            self.py = best
            self.vy = 0
            self.ground = True

    def _hazard(self):
        for (x, y, w, h) in self.haz:
            if self._ov(self.px + 3, self.py, self.pw - 6, self.ph - 3, x, y, w, h):
                return True
        return False

    def _ov(self, ax, ay, aw, ah, bx, by, bw, bh):
        return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by

    def _die(self):
        self.alive = False
        self.dtimer = 0
        if self.data.get("vibration_on"):
            do_vibrate(70)
        sfx("death", self.data.get("sound_on", True))
        c = get_color_from_hex(self.th["haz"])
        for _ in range(20):
            self.parts.append(Particle(self.px + self.pw / 2, self.py + self.ph / 2, c, 0.6))

    def _win(self):
        self.won = True
        if self.data.get("vibration_on"):
            do_vibrate(40)
        sfx("win", self.data.get("sound_on", True))
        base = 10 + self.level * 3
        sb = SKINS.get(self.data.get("selected_skin", "default"), {}).get("bonus", 1)
        tb = TRAILS.get(self.data.get("selected_trail", "none"), {}).get("bonus", 1)
        self.earned = int(base * sb * tb)
        self.data["cups"] = self.data.get("cups", 0) + self.earned
        if self.level >= self.data.get("unlocked_levels", 1):
            self.data["unlocked_levels"] = self.level + 1
        save_data(self.data)
        c = get_color_from_hex("#FFD93D")
        for _ in range(28):
            self.parts.append(Particle(self.px + self.pw / 2, self.py + self.ph, c, 1.0))

    def _parts(self, dt):
        alive = []
        for p in self.parts:
            p.life -= dt
            if p.life > 0:
                p.x += p.vx * dt
                p.y += p.vy * dt
                p.vy -= 260 * dt
                alive.append(p)
        self.parts = alive

    def _draw(self):
        self.canvas.clear()
        W, H = self.width, self.height
        cam = self.cam
        with self.canvas:
            bg = get_color_from_hex(self.th["bg"])
            Color(*bg)
            Rectangle(pos=(0, 0), size=(W, H))

            # soft drawn dots
            Color(1, 1, 1, 0.07)
            random.seed(self.level * 51)
            for _ in range(40):
                sx = random.uniform(0, W)
                sy = random.uniform(0, self.wh)
                if 0 < sy - cam < H:
                    Rectangle(pos=(sx, sy - cam), size=(2.2, 2.2))
            random.seed()

            pl = get_color_from_hex(self.th["plat"])
            for (x, y, w, h) in self.plats:
                if y + h < cam - 30 or y > cam + H + 30:
                    continue
                # platform body
                Color(*pl)
                Rectangle(pos=(x, y - cam), size=(w, h))
                # lighter top edge (drawn look)
                Color(min(1, pl[0] + 0.2), min(1, pl[1] + 0.2), min(1, pl[2] + 0.2), 1)
                Rectangle(pos=(x, y + h - 3 - cam), size=(w, 3))
                # slight darker bottom
                Color(pl[0] * 0.7, pl[1] * 0.7, pl[2] * 0.7, 0.6)
                Rectangle(pos=(x, y - cam), size=(w, 2))

            hz = get_color_from_hex(self.th["haz"])
            for (x, y, w, h) in self.haz:
                if y + h < cam - 15 or y > cam + H + 15:
                    continue
                Color(*hz)
                n = max(2, int(w / 9))
                sw = w / n
                for i in range(n):
                    sx = x + i * sw
                    Triangle(points=[sx, y - cam, sx + sw / 2, y + h - cam, sx + sw, y - cam])

            if self.goal:
                gx, gy, gw, gh = self.goal
                if gy < cam + H + 40:
                    Color(1, 0.9, 0.35, 1)
                    Rectangle(pos=(gx + gw / 2 - 3, gy - cam), size=(6, gh))
                    Color(1, 0.35, 0.45, 1)
                    Triangle(points=[
                        gx + gw / 2 + 3, gy + gh - cam,
                        gx + gw / 2 + 3, gy + gh - 22 - cam,
                        gx + gw / 2 + 28, gy + gh - 11 - cam
                    ])

            for p in self.parts:
                a = max(0, p.life / p.max)
                Color(p.c[0], p.c[1], p.c[2], a)
                Rectangle(pos=(p.x - p.sz / 2, p.y - cam - p.sz / 2), size=(p.sz, p.sz))

            if self.alive:
                sk = SKINS.get(self.data.get("selected_skin", "default"), SKINS["default"])
                pc = get_color_from_hex(sk["color"])
                px, py = self.px, self.py - cam
                sq = self.squash
                # walk bob / leg cycle
                moving = abs(self.vx) > 20 and self.ground
                phase = self.anim_t * (10 if moving else 0)
                leg_off = (3.5 if moving else 0) * __import__("math").sin(phase)
                bob = (1.5 if moving else 0) * abs(__import__("math").sin(phase))
                # jump pose
                in_air = not self.ground
                body_h = 14 * sq
                head_s = 16 * (2 - sq) * 0.9 + 2
                leg_h = (10 if in_air else 12) * (2 - sq)

                # legs
                Color(pc[0] * 0.65, pc[1] * 0.65, pc[2] * 0.65, 1)
                if in_air:
                    # tucked legs
                    Rectangle(pos=(px + 5, py + 2), size=(6, leg_h * 0.7))
                    Rectangle(pos=(px + 13, py + 2), size=(6, leg_h * 0.7))
                else:
                    Rectangle(pos=(px + 5, py + leg_off * 0.3), size=(6, leg_h))
                    Rectangle(pos=(px + 13, py - leg_off * 0.3), size=(6, leg_h))
                # body
                Color(*pc)
                by = py + leg_h * 0.85 + bob
                Rectangle(pos=(px + 2, by), size=(20, body_h))
                # head
                Color(min(1, pc[0] * 1.1), min(1, pc[1] * 1.1), min(1, pc[2] * 1.1), 1)
                hy = by + body_h - 2
                Ellipse(pos=(px + 4, hy), size=(head_s, head_s))
                # eyes
                Color(0.1, 0.08, 0.14, 1)
                eye_y = hy + head_s * 0.45
                if self.face > 0:
                    Ellipse(pos=(px + 12, eye_y), size=(4.5, 4.5))
                    Ellipse(pos=(px + 18, eye_y), size=(3.5, 3.5))
                else:
                    Ellipse(pos=(px + 5, eye_y), size=(4.5, 4.5))
                    Ellipse(pos=(px + 11, eye_y), size=(3.5, 3.5))
                # white eye shine
                Color(1, 1, 1, 0.9)
                if self.face > 0:
                    Ellipse(pos=(px + 13, eye_y + 1.5), size=(2, 2))
                else:
                    Ellipse(pos=(px + 6, eye_y + 1.5), size=(2, 2))


class GameScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.level = 1
        self.data = {}

        # CRITICAL: vertical split — game ABOVE controls, never overlap
        col = BoxLayout(orientation="vertical", spacing=0, padding=0)

        self.area = FloatLayout(size_hint=(1, 1))
        self.world = GameWorld(size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
        self.area.add_widget(self.world)

        self.info = Label(text="Lv.1", font_size=sp(14), bold=True, color=(1, 0.98, 0.95, 0.95),
                          size_hint=(None, None), size=(dp(210), dp(28)),
                          pos_hint={"x": 0.03, "top": 0.98}, halign="left")
        self.info.bind(size=self.info.setter("text_size"))
        self.area.add_widget(self.info)

        self.mb = Btn(text="MENU", bg=(0.55, 0.22, 0.3, 0.92),
                      size_hint=(None, None), size=(dp(76), dp(32)),
                      pos_hint={"right": 0.97, "top": 0.98})
        self.mb.bind(on_press=self._menu)
        self.area.add_widget(self.mb)

        self.win_l = Label(text="", font_size=sp(22), bold=True, color=(1, 0.92, 0.4, 1),
                           size_hint=(None, None), size=(dp(280), dp(80)),
                           pos_hint={"center_x": 0.5, "center_y": 0.55},
                           halign="center", opacity=0)
        self.win_l.bind(size=self.win_l.setter("text_size"))
        self.area.add_widget(self.win_l)

        self.cont = Btn(text="CONTINUE", bg=(0.25, 0.7, 0.4, 1),
                        size_hint=(None, None), size=(dp(160), dp(46)),
                        pos_hint={"center_x": 0.5, "center_y": 0.38},
                        opacity=0, disabled=True)
        self.cont.bind(on_press=self._cont)
        self.area.add_widget(self.cont)

        col.add_widget(self.area)

        # Controls — fixed bottom strip, game never draws here
        self.ctrl = BoxLayout(size_hint=(1, None), height=dp(72),
                              padding=[dp(8), dp(6)], spacing=dp(8))
        with self.ctrl.canvas.before:
            Color(0.20, 0.45, 0.90, 1)
            self.cbg = Rectangle()
        self.ctrl.bind(pos=lambda *a: setattr(self.cbg, "pos", self.ctrl.pos),
                       size=lambda *a: setattr(self.cbg, "size", self.ctrl.size))
        self.bl = Btn(text="<", bg=(0.4, 0.45, 0.95, 1), size_hint=(0.28, 1))
        self.bj = Btn(text="JUMP", bg=(1.0, 0.75, 0.2, 1), size_hint=(0.44, 1))
        self.br = Btn(text=">", bg=(0.4, 0.45, 0.95, 1), size_hint=(0.28, 1))
        self.bl.font_size = sp(28)
        self.br.font_size = sp(28)
        self.bj.font_size = sp(18)
        self.bl.bind(on_press=lambda x: self._mv("l", True), on_release=lambda x: self._mv("l", False),
                     on_touch_up=self._touch_up_ctrl)
        self.br.bind(on_press=lambda x: self._mv("r", True), on_release=lambda x: self._mv("r", False),
                     on_touch_up=self._touch_up_ctrl)
        self.bj.bind(on_press=lambda x: self._jp(), on_release=lambda x: self._jr())
        self.ctrl.add_widget(self.bl)
        self.ctrl.add_widget(self.bj)
        self.ctrl.add_widget(self.br)
        col.add_widget(self.ctrl)

        self.add_widget(col)
        Window.bind(on_key_down=self._kd, on_key_up=self._ku)

    def _mv(self, s, st):
        if s == "l":
            self.world.left = st
        else:
            self.world.right = st

    def _jp(self):
        self.world.jpress = True
        self.world.jheld = True

    def _jr(self):
        self.world.jheld = False

    def _touch_up_ctrl(self, inst, touch):
        # ensure movement stops when finger lifts anywhere
        if not inst.collide_point(*touch.pos):
            if inst is self.bl:
                self.world.left = False
            elif inst is self.br:
                self.world.right = False
        return False

    def _kd(self, w, key, sc, code, mod):
        if self.manager.current != "game":
            return
        if key in (276, 97):
            self.world.left = True
        elif key in (275, 100):
            self.world.right = True
        elif key in (32, 273, 119):
            self.world.jpress = True
            self.world.jheld = True

    def _ku(self, w, key, sc):
        if key in (276, 97):
            self.world.left = False
        elif key in (275, 100):
            self.world.right = False
        if key in (32, 273, 119):
            self.world.jheld = False

    def setup(self, level, data):
        self.level = level
        self.data = data
        self.win_l.opacity = 0
        self.cont.opacity = 0
        self.cont.disabled = True
        self.world.left = False
        self.world.right = False
        self.world.jpress = False
        th = theme(level)
        self.info.text = f"Lv.{level}  {th['name']}"
        Clock.schedule_once(lambda dt: self.world.start(level, data), 0.06)

    def on_leave(self, *a):
        self.world.stop()

    def _menu(self, *a):
        if self.data.get("vibration_on"):
            do_vibrate(14)
        self.world.stop()
        self.manager.transition = SlideTransition(direction="down", duration=0.2)
        self.manager.current = "main"

    def _chk(self, dt):
        if self.world.won and self.win_l.opacity == 0:
            e = getattr(self.world, "earned", 0)
            self.win_l.text = f"LEVEL CLEAR!\n+{e} Cups"
            self.win_l.opacity = 1
            self.cont.opacity = 1
            self.cont.disabled = False
            return False
        return True

    def on_enter(self, *a):
        Clock.schedule_interval(self._chk, 0.1)

    def _cont(self, *a):
        self.world.stop()
        self.manager.transition = SlideTransition(direction="down", duration=0.2)
        self.manager.current = "main"


class HauselApp(App):
    def build(self):
        self.title = "HAUSEL"
        sm = ScreenManager()
        sm.add_widget(LoadingScreen(name="loading"))
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(GameScreen(name="game"))
        return sm


if __name__ == "__main__":
    HauselApp().run()
