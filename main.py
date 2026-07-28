# HAUSEL v0.3 - Vertical Pixel Platformer | LGStudio

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
from kivy.animation import Animation
from kivy.storage.jsonstore import JsonStore
from kivy.metrics import dp, sp
from kivy.utils import get_color_from_hex, platform
from kivy.core.audio import SoundLoader
import random
import os

if platform not in ("android", "ios"):
    Window.size = (360, 740)
Window.clearcolor = (0.18, 0.14, 0.28, 1)

# ===================== PATHS =====================
def asset(name):
    base = os.path.dirname(os.path.abspath(__file__))
    p1 = os.path.join(base, "assets", name)
    p2 = os.path.join(base, name)
    return p1 if os.path.exists(p1) else p2

# ===================== VIBRATION =====================
def do_vibrate(ms=30):
    try:
        if platform == "android":
            from jnius import autoclass
            activity = autoclass("org.kivy.android.PythonActivity").mActivity
            Context = autoclass("android.content.Context")
            v = activity.getSystemService(Context.VIBRATOR_SERVICE)
            if v:
                v.vibrate(int(ms))
    except Exception:
        pass

# ===================== AUDIO =====================
_sounds = {}
_menu = None

def _load_sounds():
    global _menu
    for key, fname in [("jump", "jump.wav"), ("land", "land.wav"), ("death", "death.wav"),
                       ("win", "win.wav"), ("click", "click.wav")]:
        try:
            s = SoundLoader.load(asset(fname))
            if s:
                s.volume = 0.45
                _sounds[key] = s
        except Exception:
            pass
    try:
        _menu = SoundLoader.load(asset("menu.wav"))
        if _menu:
            _menu.loop = True
            _menu.volume = 0.28
    except Exception:
        pass

def sfx(name, enabled=True):
    if not enabled:
        return
    s = _sounds.get(name)
    if s:
        try:
            s.stop()
            s.play()
        except Exception:
            pass

def menu_music(on):
    global _menu
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

# ===================== DATA =====================
store = JsonStore("game_data.json")
DEFAULT = {
    "cups": 0, "unlocked_levels": 1,
    "selected_skin": "default", "selected_trail": "none",
    "owned_skins": ["default"], "owned_trails": ["none"],
    "music_on": True, "vibration_on": True, "sound_on": True,
    "used_codes": [],
}

def load_data():
    d = DEFAULT.copy()
    if store.exists("player"):
        d.update(store.get("player"))
    # ensure lists
    for k in ("owned_skins", "owned_trails", "used_codes"):
        if not isinstance(d.get(k), list):
            d[k] = list(DEFAULT[k])
    return d

def save_data(d):
    store.put("player", **d)

PROMO = {
    "YAULTRA": {"cups": 10000},
}

# ===================== THEMES =====================
LEVEL_THEMES = [
    {"name": "Moss Valley",  "color": "#6BBF7A", "bg": "#1E3A28", "plat": "#4A9A58", "hazard": "#E05555"},
    {"name": "Pine Ridge",   "color": "#8FBF5A", "bg": "#243818", "plat": "#6A9A3E", "hazard": "#E08040"},
    {"name": "Teal Shores",  "color": "#4DB8B0", "bg": "#183838", "plat": "#2E8A84", "hazard": "#E06090"},
    {"name": "Sky Bridge",   "color": "#5AADD0", "bg": "#183040", "plat": "#3A88B0", "hazard": "#E09040"},
    {"name": "Deep Blue",    "color": "#5A90D0", "bg": "#182840", "plat": "#3A68A8", "hazard": "#E05050"},
    {"name": "Night Indigo", "color": "#7A7AD0", "bg": "#202040", "plat": "#5050A0", "hazard": "#E08040"},
    {"name": "Grape Wall",   "color": "#9A70D0", "bg": "#281840", "plat": "#6848A0", "hazard": "#E05070"},
    {"name": "Orchid Path",  "color": "#C060B0", "bg": "#301828", "plat": "#883878", "hazard": "#E06060"},
    {"name": "Rose Gate",    "color": "#E06090", "bg": "#301820", "plat": "#A03858", "hazard": "#E0B040"},
    {"name": "Coral Peak",   "color": "#E07070", "bg": "#301818", "plat": "#A04848", "hazard": "#40C0C0"},
]

def theme_for(level):
    return LEVEL_THEMES[(level - 1) % 10].copy()

SKINS = {
    "default": {"name": "Classic", "price": 0,   "bonus": 1.0,  "color": "#FFF5E6"},
    "red":     {"name": "Crimson", "price": 50,  "bonus": 1.1,  "color": "#FF6B6B"},
    "blue":    {"name": "Ocean",   "price": 80,  "bonus": 1.15, "color": "#4ECDC4"},
    "gold":    {"name": "Golden",  "price": 150, "bonus": 1.3,  "color": "#FFD93D"},
    "neon":    {"name": "Neon",    "price": 250, "bonus": 1.5,  "color": "#6BCB77"},
    "shadow":  {"name": "Shadow",  "price": 400, "bonus": 1.8,  "color": "#A78BFA"},
}
TRAILS = {
    "none":    {"name": "No Trail",   "price": 0,   "bonus": 1.0,  "color": "#888"},
    "white":   {"name": "White Dust", "price": 40,  "bonus": 1.05, "color": "#FFF"},
    "fire":    {"name": "Fire Trail", "price": 100, "bonus": 1.2,  "color": "#FF7A3A"},
    "ice":     {"name": "Ice Trail",  "price": 120, "bonus": 1.25, "color": "#4ECDC4"},
    "rainbow": {"name": "Rainbow",    "price": 300, "bonus": 1.6,  "color": "#FF6BCB"},
    "stars":   {"name": "Star Dust",  "price": 500, "bonus": 2.0,  "color": "#FFD93D"},
}

# ===================== UI HELPERS =====================
class Btn(Button):
    def __init__(self, bg=(0.4, 0.45, 0.85, 1), **kw):
        super().__init__(**kw)
        self.background_normal = self.background_down = ""
        self.background_color = bg
        self.color = (1, 1, 1, 1)
        self.font_size = sp(15)
        self.bold = True


class NavBtn(Button):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.background_normal = self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.color = (0.75, 0.7, 0.9, 1)
        self.font_size = sp(14)
        self.bold = True


class LevelCard(Button):
    def __init__(self, level, th, unlocked, **kw):
        super().__init__(**kw)
        self.level, self.th, self.unlocked = level, th, unlocked
        self.background_normal = self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.size_hint = (1, None)
        self.height = dp(60)
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *a):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.unlocked:
                bg = get_color_from_hex(self.th["bg"])
                pl = get_color_from_hex(self.th["plat"])
                ac = get_color_from_hex(self.th["color"])
                Color(bg[0], bg[1], bg[2], 1)
                RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])
                Color(pl[0], pl[1], pl[2], 0.95)
                x0, y0, w, h = self.x, self.y, self.width, self.height
                Rectangle(pos=(x0 + w * 0.06, y0 + h * 0.2), size=(w * 0.2, h * 0.16))
                Rectangle(pos=(x0 + w * 0.35, y0 + h * 0.45), size=(w * 0.18, h * 0.16))
                Rectangle(pos=(x0 + w * 0.6, y0 + h * 0.25), size=(w * 0.24, h * 0.16))
                Color(ac[0], ac[1], ac[2], 0.35)
                Line(rounded_rectangle=(self.x + 1, self.y + 1, self.width - 2, self.height - 2, dp(13)), width=1.2)
            else:
                Color(0.14, 0.12, 0.2, 1)
                RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])
                Color(0.25, 0.22, 0.32, 1)
                x0, y0, w, h = self.x, self.y, self.width, self.height
                Rectangle(pos=(x0 + w * 0.06, y0 + h * 0.2), size=(w * 0.2, h * 0.16))
                Rectangle(pos=(x0 + w * 0.35, y0 + h * 0.45), size=(w * 0.18, h * 0.16))
                Rectangle(pos=(x0 + w * 0.6, y0 + h * 0.25), size=(w * 0.24, h * 0.16))


# ===================== LOADING =====================
class LoadingScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = FloatLayout()
        with root.canvas.before:
            Color(0.16, 0.12, 0.28, 1)
            self.bg = Rectangle(size=root.size)
            Color(0.5, 0.35, 0.9, 0.15)
            self.c1 = Ellipse(size=(200, 200))
            Color(0.95, 0.4, 0.55, 0.12)
            self.c2 = Ellipse(size=(160, 160))
        root.bind(size=self._u, pos=self._u)
        root.add_widget(Label(text="HAUSEL", font_size=sp(52), bold=True,
                              color=(1, 0.95, 0.9, 1), size_hint=(1, None), height=dp(64),
                              pos_hint={"center_x": 0.5, "center_y": 0.6}))
        root.add_widget(Label(text="by LGStudio", font_size=sp(15),
                              color=(0.75, 0.65, 0.95, 1), size_hint=(1, None), height=dp(28),
                              pos_hint={"center_x": 0.5, "center_y": 0.52}))
        self.bar = ProgressBar(max=100, size_hint=(0.7, None), height=dp(10),
                               pos_hint={"center_x": 0.5, "center_y": 0.36})
        root.add_widget(self.bar)
        self.lbl = Label(text="Loading...", font_size=sp(13), color=(0.7, 0.65, 0.85, 1),
                         size_hint=(1, None), height=dp(28),
                         pos_hint={"center_x": 0.5, "center_y": 0.3})
        root.add_widget(self.lbl)
        self.add_widget(root)
        self.v = 0

    def _u(self, *a):
        self.bg.pos, self.bg.size = self.pos, self.size
        self.c1.pos = (self.width * 0.5, self.height * 0.65)
        self.c1.size = (self.width * 0.55, self.width * 0.55)
        self.c2.pos = (-self.width * 0.1, self.height * 0.05)
        self.c2.size = (self.width * 0.45, self.width * 0.45)

    def on_enter(self):
        self.v = 0
        _load_sounds()
        Clock.schedule_interval(self._tick, 0.025)

    def _tick(self, dt):
        self.v += random.uniform(2.5, 5)
        if self.v >= 100:
            self.bar.value = 100
            self.lbl.text = "Let's climb!"
            Clock.unschedule(self._tick)
            Clock.schedule_once(lambda dt: setattr(self.manager, "current", "main") or
                                setattr(self.manager, "transition", FadeTransition(duration=0.3)), 0.35)
            return False
        self.bar.value = self.v
        self.lbl.text = "Loading" + "." * (int(self.v / 12) % 4)
        return True


# ===================== MAIN =====================
class MainScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.data = load_data()
        self.tab = "play"

        col = BoxLayout(orientation="vertical")
        self.body = FloatLayout(size_hint=(1, 1))
        col.add_widget(self.body)

        self.nav = BoxLayout(size_hint=(1, None), height=dp(68), padding=[dp(6), dp(6)], spacing=dp(4))
        with self.nav.canvas.before:
            Color(0.2, 0.16, 0.35, 1)
            self.nav_bg = Rectangle()
            Color(0.7, 0.5, 1, 0.5)
            self.nav_line = Rectangle(size=(0, 3))
        self.nav.bind(pos=self._nav_u, size=self._nav_u)
        self.b_shop = NavBtn(text="SHOP")
        self.b_play = NavBtn(text="PLAY")
        self.b_set = NavBtn(text="SETTINGS")
        self.b_shop.bind(on_press=lambda x: self.switch("shop"))
        self.b_play.bind(on_press=lambda x: self.switch("play"))
        self.b_set.bind(on_press=lambda x: self.switch("settings"))
        for b in (self.b_shop, self.b_play, self.b_set):
            self.nav.add_widget(b)
        col.add_widget(self.nav)
        self.add_widget(col)

        with self.canvas.before:
            Color(0.18, 0.14, 0.28, 1)
            self.sbg = Rectangle()
        self.bind(pos=lambda *a: setattr(self.sbg, "pos", self.pos) or setattr(self.sbg, "size", self.size),
                  size=lambda *a: setattr(self.sbg, "pos", self.pos) or setattr(self.sbg, "size", self.size))

        self.w_shop = self._mk_shop()
        self.w_play = self._mk_play()
        self.w_set = self._mk_set()
        self.switch("play")

    def _nav_u(self, *a):
        self.nav_bg.pos, self.nav_bg.size = self.nav.pos, self.nav.size
        self.nav_line.pos = (self.nav.x, self.nav.top - 3)
        self.nav_line.size = (self.nav.width, 3)

    def on_enter(self, *a):
        self.data = load_data()
        if self.data.get("music_on", True):
            menu_music(True)
        self.refresh()

    def on_leave(self, *a):
        menu_music(False)

    def switch(self, tab):
        if self.data.get("vibration_on", True):
            do_vibrate(15)
        sfx("click", self.data.get("sound_on", True))
        self.tab = tab
        self.body.clear_widgets()
        for b in (self.b_shop, self.b_play, self.b_set):
            b.color = (0.65, 0.6, 0.8, 1)
        if tab == "shop":
            self.body.add_widget(self.w_shop)
            self.b_shop.color = (1, 0.9, 0.4, 1)
            self._ref_shop()
        elif tab == "play":
            self.body.add_widget(self.w_play)
            self.b_play.color = (0.5, 1, 0.65, 1)
            self._ref_play()
        else:
            self.body.add_widget(self.w_set)
            self.b_set.color = (0.7, 0.85, 1, 1)

    def refresh(self):
        if self.tab == "shop":
            self._ref_shop()
        elif self.tab == "play":
            self._ref_play()

    # ---- SHOP ----
    def _mk_shop(self):
        root = BoxLayout(orientation="vertical", padding=[dp(12), dp(8), dp(12), dp(4)], spacing=dp(4))
        head = BoxLayout(size_hint=(1, None), height=dp(44))
        head.add_widget(Label(text="SHOP", font_size=sp(22), bold=True, color=(1, 0.9, 0.4, 1),
                              size_hint=(0.4, 1), halign="left"))
        self.cups_l = Label(text="Cups: 0", font_size=sp(16), bold=True, color=(1, 0.88, 0.35, 1),
                            size_hint=(0.6, 1), halign="right")
        self.cups_l.bind(size=self.cups_l.setter("text_size"))
        head.add_widget(self.cups_l)
        root.add_widget(head)

        sc = ScrollView(size_hint=(1, 1), do_scroll_x=False, bar_width=dp(4))
        self.shop_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8),
                                  padding=[0, 0, 0, dp(140)])
        self.shop_box.bind(minimum_height=self.shop_box.setter("height"))
        sc.add_widget(self.shop_box)
        root.add_widget(sc)

        # promo
        prow = BoxLayout(size_hint=(1, None), height=dp(42), spacing=dp(8))
        self.code_in = TextInput(hint_text="Promo code...", multiline=False, font_size=sp(14),
                                 size_hint=(0.7, 1), background_color=(0.22, 0.18, 0.35, 1),
                                 foreground_color=(1, 1, 1, 1), cursor_color=(1, 1, 1, 1),
                                 padding=[dp(10), dp(10)])
        prow.add_widget(self.code_in)
        ok = Btn(text="OK", bg=(0.35, 0.7, 0.4, 1), size_hint=(0.3, 1))
        ok.bind(on_press=self._apply_code)
        prow.add_widget(ok)
        root.add_widget(prow)
        return root

    def _ref_shop(self):
        self.cups_l.text = f"Cups: {self.data['cups']}"
        self.shop_box.clear_widgets()
        self.shop_box.add_widget(Label(text="SKINS", font_size=sp(12), bold=True,
                                       color=(0.8, 0.75, 1, 1), size_hint=(1, None), height=dp(22)))
        for k, s in SKINS.items():
            self.shop_box.add_widget(self._row(s["name"], f"x{s['bonus']}" if s["bonus"] > 1 else "base",
                                               s["price"], k in self.data["owned_skins"],
                                               self.data["selected_skin"] == k, s["color"], "skin", k))
        self.shop_box.add_widget(Label(text="TRAILS", font_size=sp(12), bold=True,
                                       color=(0.8, 0.75, 1, 1), size_hint=(1, None), height=dp(26)))
        for k, t in TRAILS.items():
            self.shop_box.add_widget(self._row(t["name"], f"x{t['bonus']}" if t["bonus"] > 1 else "—",
                                               t["price"], k in self.data["owned_trails"],
                                               self.data["selected_trail"] == k, t["color"], "trail", k))

    def _row(self, title, sub, price, owned, selected, color, typ, key):
        box = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(54),
                        padding=[dp(10), dp(5)], spacing=dp(10))
        with box.canvas.before:
            Color(0.24, 0.2, 0.4, 1)
            rr = RoundedRectangle(radius=[dp(12)])
        box.bind(pos=lambda *a: setattr(rr, "pos", box.pos), size=lambda *a: setattr(rr, "size", box.size))
        col = get_color_from_hex(color)
        prev = Widget(size_hint=(None, None), size=(dp(32), dp(32)))
        with prev.canvas:
            Color(*col)
            el = Ellipse()
        prev.bind(pos=lambda *a: setattr(el, "pos", prev.pos), size=lambda *a: setattr(el, "size", prev.size))
        box.add_widget(prev)
        tb = BoxLayout(orientation="vertical")
        t1 = Label(text=title, font_size=sp(14), bold=True, color=(1, 0.98, 0.95, 1),
                   halign="left", valign="bottom", size_hint=(1, 0.55))
        t2 = Label(text=sub, font_size=sp(11), color=(0.7, 0.65, 0.85, 1),
                   halign="left", valign="top", size_hint=(1, 0.45))
        t1.bind(size=t1.setter("text_size"))
        t2.bind(size=t2.setter("text_size"))
        tb.add_widget(t1)
        tb.add_widget(t2)
        box.add_widget(tb)
        if selected:
            b = Btn(text="ON", bg=(0.3, 0.7, 0.4, 1), size_hint=(None, None), size=(dp(70), dp(32)))
            b.disabled = True
        elif owned:
            b = Btn(text="USE", bg=(0.4, 0.45, 0.85, 1), size_hint=(None, None), size=(dp(70), dp(32)))
            b.bind(on_press=lambda x, t=typ, k=key: self._select(t, k))
        else:
            b = Btn(text=str(price), bg=(0.8, 0.5, 0.25, 1), size_hint=(None, None), size=(dp(70), dp(32)))
            b.bind(on_press=lambda x, t=typ, k=key, p=price: self._buy(t, k, p))
        box.add_widget(b)
        return box

    def _buy(self, typ, key, price):
        if self.data["cups"] < price:
            return
        if self.data.get("vibration_on"):
            do_vibrate(22)
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
        self._ref_shop()

    def _select(self, typ, key):
        if self.data.get("vibration_on"):
            do_vibrate(15)
        sfx("click", self.data.get("sound_on", True))
        if typ == "skin":
            self.data["selected_skin"] = key
        else:
            self.data["selected_trail"] = key
        save_data(self.data)
        self._ref_shop()

    def _apply_code(self, *a):
        code = self.code_in.text.strip().upper()
        self.code_in.text = ""
        if not code or code in self.data.get("used_codes", []):
            return
        if code not in PROMO:
            return
        r = PROMO[code]
        if self.data.get("vibration_on"):
            do_vibrate(40)
        sfx("win", self.data.get("sound_on", True))
        if "cups" in r:
            self.data["cups"] += r["cups"]
        self.data.setdefault("used_codes", []).append(code)
        save_data(self.data)
        self._ref_shop()

    # ---- PLAY ----
    def _mk_play(self):
        root = BoxLayout(orientation="vertical", padding=[dp(12), dp(8), dp(12), dp(4)], spacing=dp(4))
        top = BoxLayout(size_hint=(1, None), height=dp(40))
        top.add_widget(Label(text="LEVELS", font_size=sp(20), bold=True, color=(0.5, 1, 0.7, 1)))
        self.pcups = Label(text="Cups: 0", font_size=sp(15), bold=True, color=(1, 0.88, 0.35, 1))
        top.add_widget(self.pcups)
        root.add_widget(top)
        sc = ScrollView(size_hint=(1, 1), do_scroll_x=False, bar_width=dp(4))
        self.lv_box = GridLayout(cols=1, size_hint_y=None, spacing=dp(8),
                                 padding=[0, 0, 0, dp(140)])
        self.lv_box.bind(minimum_height=self.lv_box.setter("height"))
        sc.add_widget(self.lv_box)
        root.add_widget(sc)
        return root

    def _ref_play(self):
        self.pcups.text = f"Cups: {self.data['cups']}"
        self.lv_box.clear_widgets()
        un = self.data.get("unlocked_levels", 1)
        for lv in range(1, 101):
            th = theme_for(lv)
            ok = lv <= un
            card = LevelCard(lv, th, ok)
            if ok:
                card.text = f"  Level {lv}   {th['name']}"
                card.color = (1, 0.98, 0.95, 1)
                card.font_size = sp(14)
                card.bind(on_press=lambda x, l=lv: self._go(l))
            else:
                card.text = f"  Level {lv}   locked"
                card.color = (0.45, 0.42, 0.55, 1)
                card.font_size = sp(13)
                card.disabled = True
            self.lv_box.add_widget(card)

    def _go(self, level):
        if self.data.get("vibration_on"):
            do_vibrate(20)
        sfx("click", self.data.get("sound_on", True))
        menu_music(False)
        g = self.manager.get_screen("game")
        g.setup(level, self.data)
        self.manager.transition = SlideTransition(direction="up", duration=0.22)
        self.manager.current = "game"

    # ---- SETTINGS ----
    def _mk_set(self):
        root = BoxLayout(orientation="vertical", padding=[dp(16), dp(12)], spacing=dp(12))
        root.add_widget(Label(text="SETTINGS", font_size=sp(22), bold=True,
                              color=(0.75, 0.85, 1, 1), size_hint=(1, None), height=dp(40)))
        for lab, attr, h in [("Music", "music_on", self._tm), ("Sound Effects", "sound_on", self._ts),
                             ("Vibration", "vibration_on", self._tv)]:
            row = BoxLayout(size_hint=(1, None), height=dp(44))
            row.add_widget(Label(text=lab, font_size=sp(15), color=(0.95, 0.92, 1, 1)))
            sw = Switch(active=self.data.get(attr, True))
            sw.bind(active=h)
            setattr(self, f"sw_{attr}", sw)
            row.add_widget(sw)
            root.add_widget(row)
        root.add_widget(Widget(size_hint=(1, 1)))
        rb = Btn(text="Reset Progress", bg=(0.7, 0.25, 0.3, 1), size_hint=(1, None), height=dp(46))
        rb.bind(on_press=self._reset)
        root.add_widget(rb)
        info = Label(text="HAUSEL  v0.3\nby LGStudio", font_size=sp(12),
                     color=(0.55, 0.5, 0.7, 1), size_hint=(1, None), height=dp(48),
                     halign="center")
        info.bind(size=info.setter("text_size"))
        root.add_widget(info)
        return root

    def _tm(self, i, v):
        self.data["music_on"] = v
        save_data(self.data)
        menu_music(v)
        if self.data.get("vibration_on"):
            do_vibrate(12)

    def _ts(self, i, v):
        self.data["sound_on"] = v
        save_data(self.data)
        if self.data.get("vibration_on"):
            do_vibrate(12)

    def _tv(self, i, v):
        self.data["vibration_on"] = v
        save_data(self.data)
        if v:
            do_vibrate(25)

    def _reset(self, *a):
        if self.data.get("vibration_on"):
            do_vibrate(35)
        self.data = DEFAULT.copy()
        save_data(self.data)
        self.sw_music_on.active = True
        self.sw_sound_on.active = True
        self.sw_vibration_on.active = True
        menu_music(True)
        self.switch(self.tab)


# ===================== GAME WORLD =====================
class Particle:
    def __init__(self, x, y, c, life=0.5):
        self.x, self.y = x, y
        self.vx = random.uniform(-60, 60)
        self.vy = random.uniform(20, 90)
        self.life = self.max = life
        self.c = c
        self.sz = random.uniform(2.5, 6)


class GameWorld(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.reset_state()
        self._ev = None

    def reset_state(self):
        self.level = 1
        self.data = {}
        self.th = theme_for(1)
        self.px = self.py = self.vx = self.vy = 0
        self.pw, self.ph = 22, 32
        self.ground = False
        self.face = 1
        self.alive = True
        self.won = False
        self.dtimer = 0
        self.cam = 0
        self.plats = []
        self.haz = []
        self.goal = None
        self.wh = 2000
        self.left = self.right = False
        self.jpress = False
        self.jbuf = 0
        self.parts = []
        self.ttrail = 0
        self.was_ground = False
        # tuned physics — reliable jumps
        self.G = -980
        self.SPEED = 220
        self.JUMP = 520
        self.MAXFALL = -600

    def start(self, level, data):
        self.reset_state()
        self.level = level
        self.data = data
        self.th = theme_for(level)
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
        """Deterministic fair levels. Max gap always within jump reach."""
        self.plats = []
        self.haz = []
        W = max(float(self.width), 320.0)
        rng = random.Random(self.level * 9973 + 17)

        # jump height ≈ JUMP^2 / (2*|G|) ≈ 520^2 / 1960 ≈ 138 px
        # keep vertical gaps well under that
        max_gap = 72 + min(self.level // 10, 20)   # 72..92
        min_gap = 42
        min_w = max(85, 130 - self.level // 4)
        max_w = max(min_w + 25, 160 - self.level // 5)
        max_dx = 48 + min(self.level // 8, 22)

        # start
        sw = min(W * 0.6, 220)
        sx = (W - sw) / 2
        self.plats.append((sx, 40, sw, 18))
        self.px = W / 2 - self.pw / 2
        self.py = 60

        n = 8 + min(self.level // 5, 7)
        y = 40.0
        px, pw = sx, sw

        for i in range(n):
            gap = min_gap + (max_gap - min_gap) * (0.35 + 0.65 * rng.random())
            gap = min(gap, 95)
            y += gap
            w = min_w + (max_w - min_w) * rng.random()
            # horizontal offset limited so always reachable
            dx = (rng.random() * 2 - 1) * max_dx
            x = px + pw / 2 + dx - w / 2
            x = max(16, min(W - w - 16, x))
            self.plats.append((x, y, w, 16))

            # rare small spikes, never full width, never on first 2
            if i >= 2 and self.level >= 4 and rng.random() < min(0.1 + self.level * 0.008, 0.25):
                hw = min(22, w * 0.28)
                hx = x + 12 + (w - hw - 24) * rng.random()
                if hx > x + 10 and hx + hw < x + w - 10:
                    self.haz.append((hx, y + 16, hw, 11))
            px, pw = x, w

        # goal platform — always close and wide
        y += 55
        gw = min(W * 0.55, 200)
        gx = (W - gw) / 2
        self.plats.append((gx, y, gw, 18))
        self.goal = (gx + gw * 0.2, y + 18, gw * 0.6, 55)
        self.wh = y + 250

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
        tv = 0
        if self.left:
            tv = -self.SPEED
            self.face = -1
        if self.right:
            tv = self.SPEED
            self.face = 1
        self.vx = tv

        if self.jpress:
            self.jbuf = 0.12
            self.jpress = False
        self.jbuf = max(0, self.jbuf - dt)
        if self.jbuf > 0 and self.ground:
            self.vy = self.JUMP
            self.ground = False
            self.jbuf = 0
            sfx("jump", self.data.get("sound_on", True))

        self.vy += self.G * dt
        self.vy = max(self.vy, self.MAXFALL)
        self.px += self.vx * dt
        self.px = max(0, min(self.width - self.pw, self.px))
        self.py += self.vy * dt
        self.was_ground = self.ground
        self.ground = False
        self._collide()

        if self.ground and not self.was_ground:
            sfx("land", self.data.get("sound_on", True))

        if self._hazard():
            self._die()
            return
        if self.py < self.cam - 120:
            self._die()
            return
        if self.goal and self._hit(self.px, self.py, self.pw, self.ph, *self.goal):
            self._win()
            return

        # camera: keep player in lower third so you SEE platforms above
        target = self.py - self.height * 0.28
        self.cam += (target - self.cam) * min(1.0, 8 * dt)
        if self.cam < 0:
            self.cam = 0

        self.ttrail += dt
        tk = self.data.get("selected_trail", "none")
        if tk != "none" and self.ttrail > 0.03 and (abs(self.vx) > 20 or abs(self.vy) > 40):
            self.ttrail = 0
            c = get_color_from_hex(TRAILS[tk]["color"])
            self.parts.append(Particle(self.px + self.pw / 2, self.py + 4, c, 0.4))

        self._parts(dt)
        self._draw()

    def _collide(self):
        for (x, y, w, h) in self.plats:
            if self._hit(self.px, self.py, self.pw, self.ph, x, y, w, h):
                if self.vy <= 0 and (self.py + self.ph) >= y + h - 4:
                    self.py = y + h
                    self.vy = 0
                    self.ground = True
                elif self.vy > 0 and self.py < y + 4:
                    self.py = y - self.ph
                    self.vy = 0
                else:
                    if self.px + self.pw / 2 < x + w / 2:
                        self.px = x - self.pw
                    else:
                        self.px = x + w

    def _hazard(self):
        for (x, y, w, h) in self.haz:
            if self._hit(self.px + 4, self.py, self.pw - 8, self.ph - 4, x, y, w, h):
                return True
        return False

    def _hit(self, ax, ay, aw, ah, bx, by, bw, bh):
        return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by

    def _die(self):
        self.alive = False
        self.dtimer = 0
        if self.data.get("vibration_on"):
            do_vibrate(70)
        sfx("death", self.data.get("sound_on", True))
        c = get_color_from_hex(self.th["hazard"])
        for _ in range(22):
            self.parts.append(Particle(self.px + self.pw / 2, self.py + self.ph / 2, c, 0.65))

    def _win(self):
        self.won = True
        if self.data.get("vibration_on"):
            do_vibrate(45)
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
        for _ in range(30):
            self.parts.append(Particle(self.px + self.pw / 2, self.py + self.ph, c, 1.0))

    def _parts(self, dt):
        alive = []
        for p in self.parts:
            p.life -= dt
            if p.life > 0:
                p.x += p.vx * dt
                p.y += p.vy * dt
                p.vy -= 280 * dt
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
            # soft dots
            Color(1, 1, 1, 0.08)
            random.seed(self.level * 44)
            for _ in range(35):
                sx = random.uniform(0, W)
                sy = random.uniform(0, self.wh)
                if 0 < sy - cam < H:
                    Rectangle(pos=(sx, sy - cam), size=(2.5, 2.5))
            random.seed()

            pl = get_color_from_hex(self.th["plat"])
            for (x, y, w, h) in self.plats:
                if y + h < cam - 40 or y > cam + H + 40:
                    continue
                Color(*pl)
                Rectangle(pos=(x, y - cam), size=(w, h))
                Color(min(1, pl[0] + 0.18), min(1, pl[1] + 0.18), min(1, pl[2] + 0.18), 1)
                Rectangle(pos=(x, y + h - 4 - cam), size=(w, 4))

            hz = get_color_from_hex(self.th["hazard"])
            for (x, y, w, h) in self.haz:
                if y + h < cam - 20 or y > cam + H + 20:
                    continue
                Color(*hz)
                n = max(2, int(w / 10))
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
                Color(pc[0] * 0.65, pc[1] * 0.65, pc[2] * 0.65, 1)
                Rectangle(pos=(px + 4, py), size=(6, 12))
                Rectangle(pos=(px + 12, py), size=(6, 12))
                Color(*pc)
                Rectangle(pos=(px + 2, py + 11), size=(18, 14))
                Color(min(1, pc[0] * 1.1), min(1, pc[1] * 1.1), min(1, pc[2] * 1.1), 1)
                Ellipse(pos=(px + 3, py + 24), size=(16, 16))
                Color(0.1, 0.08, 0.15, 1)
                ex = px + 10 if self.face > 0 else px + 5
                Ellipse(pos=(ex, py + 30), size=(4, 4))


# ===================== GAME SCREEN =====================
class GameScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.level = 1
        self.data = {}

        col = BoxLayout(orientation="vertical", spacing=0)

        # game viewport — ALL remaining space above controls
        self.area = FloatLayout(size_hint=(1, 1))
        self.world = GameWorld(size_hint=(1, 1))
        self.area.add_widget(self.world)

        self.info = Label(text="Lv.1", font_size=sp(14), bold=True, color=(1, 0.98, 0.95, 0.95),
                          size_hint=(None, None), size=(dp(200), dp(28)),
                          pos_hint={"x": 0.03, "top": 0.98}, halign="left")
        self.info.bind(size=self.info.setter("text_size"))
        self.area.add_widget(self.info)

        self.menu_btn = Btn(text="MENU", bg=(0.55, 0.22, 0.3, 0.92),
                            size_hint=(None, None), size=(dp(78), dp(34)),
                            pos_hint={"right": 0.97, "top": 0.98})
        self.menu_btn.bind(on_press=self._menu)
        self.area.add_widget(self.menu_btn)

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

        # compact control bar
        self.ctrl = BoxLayout(size_hint=(1, None), height=dp(64),
                              padding=[dp(8), dp(6)], spacing=dp(8))
        with self.ctrl.canvas.before:
            Color(0.12, 0.1, 0.2, 0.92)
            self.cbg = Rectangle()
        self.ctrl.bind(pos=lambda *a: setattr(self.cbg, "pos", self.ctrl.pos),
                       size=lambda *a: setattr(self.cbg, "size", self.ctrl.size))
        self.bl = Btn(text="◀", bg=(0.32, 0.28, 0.5, 1), size_hint=(0.28, 1))
        self.bj = Btn(text="JUMP", bg=(0.35, 0.5, 0.9, 1), size_hint=(0.44, 1))
        self.br = Btn(text="▶", bg=(0.32, 0.28, 0.5, 1), size_hint=(0.28, 1))
        self.bl.bind(on_press=lambda x: self._mv("l", True), on_release=lambda x: self._mv("l", False))
        self.br.bind(on_press=lambda x: self._mv("r", True), on_release=lambda x: self._mv("r", False))
        self.bj.bind(on_press=lambda x: self._jp())
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

    def _kd(self, w, key, sc, code, mod):
        if self.manager.current != "game":
            return
        if key in (276, 97):
            self.world.left = True
        elif key in (275, 100):
            self.world.right = True
        elif key in (32, 273, 119):
            self.world.jpress = True

    def _ku(self, w, key, sc):
        if key in (276, 97):
            self.world.left = False
        elif key in (275, 100):
            self.world.right = False

    def setup(self, level, data):
        self.level = level
        self.data = data
        self.win_l.opacity = 0
        self.cont.opacity = 0
        self.cont.disabled = True
        th = theme_for(level)
        self.info.text = f"Lv.{level}  {th['name']}"
        Clock.schedule_once(lambda dt: self.world.start(level, data), 0.05)

    def on_leave(self, *a):
        self.world.stop()

    def _menu(self, *a):
        if self.data.get("vibration_on"):
            do_vibrate(15)
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
        if self.data.get("vibration_on"):
            do_vibrate(15)
        self.world.stop()
        self.manager.transition = SlideTransition(direction="down", duration=0.2)
        self.manager.current = "main"


class HauselApp(App):
    def build(self):
        self.title = "HAUSEL"
        sm = ScreenManager(transition=FadeTransition(duration=0.25))
        sm.add_widget(LoadingScreen(name="loading"))
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(GameScreen(name="game"))
        return sm


if __name__ == "__main__":
    HauselApp().run()
