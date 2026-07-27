# HAUSEL - Vertical Pixel Platformer
# Studio: LGStudio

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
from kivy.graphics import Color, Rectangle, RoundedRectangle, Ellipse, Triangle, Line
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.storage.jsonstore import JsonStore
from kivy.metrics import dp, sp
from kivy.utils import get_color_from_hex, platform
from kivy.core.audio import SoundLoader
import random

if platform not in ("android", "ios"):
    Window.size = (360, 720)
Window.clearcolor = (0.11, 0.09, 0.18, 1)

# ===================== VIBRATION =====================
def do_vibrate(duration=30):
    """Short vibration on Android"""
    try:
        if platform == "android":
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            activity = PythonActivity.mActivity
            Context = autoclass("android.content.Context")
            vibrator = activity.getSystemService(Context.VIBRATOR_SERVICE)
            if vibrator:
                vibrator.vibrate(duration)
    except Exception:
        pass

# ===================== DATA =====================
store = JsonStore("game_data.json")

DEFAULT_DATA = {
    "cups": 0,
    "current_level": 1,
    "unlocked_levels": 1,
    "selected_skin": "default",
    "selected_trail": "none",
    "owned_skins": ["default"],
    "owned_trails": ["none"],
    "music_on": True,
    "vibration_on": True,
    "sound_on": True,
}

def load_data():
    data = DEFAULT_DATA.copy()
    if store.exists("player"):
        data.update(store.get("player"))
    return data

def save_data(data):
    store.put("player", **data)

# ===================== THEMES (warmer, more hand-picked) =====================
LEVEL_THEMES = [
    {"name": "Moss Valley",   "color": "#5C9E6B", "bg": "#1A2F1E", "plat": "#3D7A4A", "hazard": "#C44D4D"},
    {"name": "Pine Ridge",    "color": "#7BA05B", "bg": "#1E2A16", "plat": "#5A7D3E", "hazard": "#D4743A"},
    {"name": "Teal Shores",   "color": "#4A9B9B", "bg": "#152828", "plat": "#2F6F6F", "hazard": "#C45B7A"},
    {"name": "Sky Bridge",    "color": "#5B9BC4", "bg": "#152030", "plat": "#3A6F94", "hazard": "#C47A3A"},
    {"name": "Deep Blue",     "color": "#4A7AB5", "bg": "#121E30", "plat": "#2F5580", "hazard": "#B54A4A"},
    {"name": "Night Indigo",  "color": "#6B6BB5", "bg": "#181830", "plat": "#48488A", "hazard": "#C46B3A"},
    {"name": "Grape Wall",    "color": "#8A6BB5", "bg": "#201830", "plat": "#5F4880", "hazard": "#B54A5B"},
    {"name": "Orchid Path",   "color": "#A55B9B", "bg": "#281828", "plat": "#7A3F70", "hazard": "#C45B5B"},
    {"name": "Rose Gate",     "color": "#C45B7A", "bg": "#2A1520", "plat": "#8A3A55", "hazard": "#C4A03A"},
    {"name": "Coral Peak",    "color": "#C46B6B", "bg": "#2A1818", "plat": "#8A4545", "hazard": "#4AB5B5"},
]

def get_level_theme(level):
    return LEVEL_THEMES[(level - 1) % 10].copy()

# ===================== SHOP =====================
SKINS = {
    "default": {"name": "Classic", "price": 0,   "bonus": 1.0,  "color": "#F0EDE5"},
    "red":     {"name": "Crimson", "price": 50,  "bonus": 1.1,  "color": "#E05A5A"},
    "blue":    {"name": "Ocean",   "price": 80,  "bonus": 1.15, "color": "#4AABB0"},
    "gold":    {"name": "Golden",  "price": 150, "bonus": 1.3,  "color": "#E8C04A"},
    "neon":    {"name": "Neon",    "price": 250, "bonus": 1.5,  "color": "#5CB86A"},
    "shadow":  {"name": "Shadow",  "price": 400, "bonus": 1.8,  "color": "#8B7AC7"},
}

TRAILS = {
    "none":    {"name": "No Trail",   "price": 0,   "bonus": 1.0,  "color": "#777777"},
    "white":   {"name": "White Dust", "price": 40,  "bonus": 1.05, "color": "#E8E4D8"},
    "fire":    {"name": "Fire Trail", "price": 100, "bonus": 1.2,  "color": "#E07A3A"},
    "ice":     {"name": "Ice Trail",  "price": 120, "bonus": 1.25, "color": "#4AABB0"},
    "rainbow": {"name": "Rainbow",    "price": 300, "bonus": 1.6,  "color": "#D45A9B"},
    "stars":   {"name": "Star Dust",  "price": 500, "bonus": 2.0,  "color": "#E8C04A"},
}

# ===================== MUSIC =====================
menu_music = None

def play_menu_music(enabled):
    global menu_music
    try:
        if menu_music is None:
            # Tries to load if you later add menu.ogg next to main.py
            menu_music = SoundLoader.load("menu.ogg")
            if menu_music:
                menu_music.loop = True
                menu_music.volume = 0.35
        if menu_music:
            if enabled:
                if menu_music.state != "play":
                    menu_music.play()
            else:
                menu_music.stop()
    except Exception:
        pass

def stop_menu_music():
    global menu_music
    try:
        if menu_music and menu_music.state == "play":
            menu_music.stop()
    except Exception:
        pass

# ===================== WIDGETS =====================
class BottomBarButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.color = (0.72, 0.68, 0.82, 1)
        self.font_size = sp(15)
        self.bold = True


class PixelButton(Button):
    def __init__(self, bg=(0.35, 0.42, 0.75, 1), **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = bg
        self.color = (1, 1, 1, 1)
        self.font_size = sp(15)
        self.bold = True


class LevelButton(Button):
    """Level select button with mini theme preview"""
    def __init__(self, level, theme, unlocked, selected, **kwargs):
        super().__init__(**kwargs)
        self.level = level
        self.theme = theme
        self.unlocked = unlocked
        self.selected = selected
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.size_hint = (1, None)
        self.height = dp(58)
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *a):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.unlocked:
                c = get_color_from_hex(self.theme["color"])
                bg = get_color_from_hex(self.theme["bg"])
                plat = get_color_from_hex(self.theme["plat"])
                # background
                Color(bg[0], bg[1], bg[2], 0.95)
                RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
                # mini platforms preview
                Color(plat[0], plat[1], plat[2], 0.9)
                h = self.height
                w = self.width
                x0, y0 = self.x, self.y
                # three small platforms
                Rectangle(pos=(x0 + w * 0.08, y0 + h * 0.22), size=(w * 0.22, h * 0.14))
                Rectangle(pos=(x0 + w * 0.38, y0 + h * 0.48), size=(w * 0.2, h * 0.14))
                Rectangle(pos=(x0 + w * 0.62, y0 + h * 0.28), size=(w * 0.26, h * 0.14))
                # border accent
                if self.selected:
                    Color(1, 0.92, 0.45, 0.9)
                    Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(12)), width=1.6)
            else:
                # locked - dark desaturated
                Color(0.12, 0.11, 0.16, 1)
                RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
                Color(0.22, 0.21, 0.28, 1)
                h = self.height
                w = self.width
                x0, y0 = self.x, self.y
                Rectangle(pos=(x0 + w * 0.08, y0 + h * 0.22), size=(w * 0.22, h * 0.14))
                Rectangle(pos=(x0 + w * 0.38, y0 + h * 0.48), size=(w * 0.2, h * 0.14))
                Rectangle(pos=(x0 + w * 0.62, y0 + h * 0.28), size=(w * 0.26, h * 0.14))


# ===================== LOADING =====================
class LoadingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = FloatLayout()
        with root.canvas.before:
            Color(0.10, 0.08, 0.16, 1)
            self.bg = Rectangle(pos=root.pos, size=root.size)
            Color(0.35, 0.28, 0.55, 0.12)
            self.c1 = Ellipse(pos=(0, 0), size=(180, 180))
            Color(0.7, 0.3, 0.4, 0.1)
            self.c2 = Ellipse(pos=(0, 0), size=(140, 140))
        root.bind(pos=self._upd, size=self._upd)

        root.add_widget(Label(
            text="HAUSEL", font_size=sp(50), bold=True, color=(0.95, 0.93, 0.9, 1),
            size_hint=(1, None), height=dp(64),
            pos_hint={"center_x": 0.5, "center_y": 0.62}
        ))
        root.add_widget(Label(
            text="by LGStudio", font_size=sp(15), color=(0.65, 0.6, 0.8, 1),
            size_hint=(1, None), height=dp(26),
            pos_hint={"center_x": 0.5, "center_y": 0.54}
        ))
        root.add_widget(Label(
            text="100 levels  •  climb up",
            font_size=sp(13), color=(0.5, 0.48, 0.62, 1),
            size_hint=(1, None), height=dp(24),
            pos_hint={"center_x": 0.5, "center_y": 0.48}
        ))
        self.progress = ProgressBar(
            max=100, value=0, size_hint=(0.68, None), height=dp(8),
            pos_hint={"center_x": 0.5, "center_y": 0.34}
        )
        root.add_widget(self.progress)
        self.loading_label = Label(
            text="Loading...", font_size=sp(13), color=(0.55, 0.52, 0.68, 1),
            size_hint=(1, None), height=dp(26),
            pos_hint={"center_x": 0.5, "center_y": 0.28}
        )
        root.add_widget(self.loading_label)
        self.add_widget(root)
        self.progress_val = 0

    def _upd(self, *a):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.c1.pos = (self.width * 0.55, self.height * 0.68)
        self.c1.size = (self.width * 0.5, self.width * 0.5)
        self.c2.pos = (-self.width * 0.12, self.height * 0.08)
        self.c2.size = (self.width * 0.42, self.width * 0.42)

    def on_enter(self):
        self.progress_val = 0
        self.progress.value = 0
        Clock.schedule_interval(self._tick, 0.03)

    def _tick(self, dt):
        self.progress_val += random.uniform(2.2, 4.8)
        if self.progress_val >= 100:
            self.progress.value = 100
            self.loading_label.text = "Ready"
            Clock.unschedule(self._tick)
            Clock.schedule_once(self._go, 0.35)
            return False
        self.progress.value = self.progress_val
        self.loading_label.text = "Loading" + "." * (int(self.progress_val / 14) % 4)
        return True

    def _go(self, dt):
        self.manager.transition = FadeTransition(duration=0.28)
        self.manager.current = "main"


# ===================== MAIN =====================
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = load_data()
        self.current_tab = "play"
        self.selected_level = 1

        root = BoxLayout(orientation="vertical", padding=0, spacing=0)

        self.content = FloatLayout(size_hint=(1, 1))
        root.add_widget(self.content)

        self.bottom = BoxLayout(
            orientation="horizontal", size_hint=(1, None), height=dp(70),
            padding=[dp(8), dp(8)], spacing=dp(6)
        )
        with self.bottom.canvas.before:
            Color(0.13, 0.11, 0.22, 1)
            self.bar_rect = Rectangle(pos=self.bottom.pos, size=self.bottom.size)
            Color(0.5, 0.4, 0.75, 0.55)
            self.bar_line = Rectangle(pos=(0, 0), size=(0, 2.5))
        self.bottom.bind(pos=self._upd_bar, size=self._upd_bar)

        self.btn_shop = BottomBarButton(text="SHOP")
        self.btn_play = BottomBarButton(text="PLAY")
        self.btn_settings = BottomBarButton(text="SETTINGS")
        self.btn_shop.bind(on_press=lambda x: self._tab("shop"))
        self.btn_play.bind(on_press=lambda x: self._tab("play"))
        self.btn_settings.bind(on_press=lambda x: self._tab("settings"))
        self.bottom.add_widget(self.btn_shop)
        self.bottom.add_widget(self.btn_play)
        self.bottom.add_widget(self.btn_settings)
        root.add_widget(self.bottom)
        self.add_widget(root)

        with self.canvas.before:
            Color(0.11, 0.09, 0.18, 1)
            self.screen_bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *a: setattr(self.screen_bg, "pos", self.pos),
                  size=lambda *a: setattr(self.screen_bg, "size", self.size))

        self.shop_widget = self._build_shop()
        self.play_widget = self._build_play()
        self.settings_widget = self._build_settings()
        self._tab("play")

    def on_enter(self, *args):
        self.data = load_data()
        if self.data.get("music_on", True):
            play_menu_music(True)
        if self.current_tab == "play":
            self._refresh_play()
        elif self.current_tab == "shop":
            self._refresh_shop()

    def on_leave(self, *args):
        stop_menu_music()

    def _upd_bar(self, *a):
        self.bar_rect.pos = self.bottom.pos
        self.bar_rect.size = self.bottom.size
        self.bar_line.pos = (self.bottom.x, self.bottom.top - 2.5)
        self.bar_line.size = (self.bottom.width, 2.5)

    def _tab(self, tab):
        if self.data.get("vibration_on", True):
            do_vibrate(18)
        self.current_tab = tab
        self.content.clear_widgets()
        for b in (self.btn_shop, self.btn_play, self.btn_settings):
            b.color = (0.6, 0.56, 0.72, 1)
            b.bold = False
        if tab == "shop":
            self.content.add_widget(self.shop_widget)
            self.btn_shop.color = (1, 0.88, 0.4, 1)
            self.btn_shop.bold = True
            self._refresh_shop()
        elif tab == "play":
            self.content.add_widget(self.play_widget)
            self.btn_play.color = (0.45, 0.95, 0.6, 1)
            self.btn_play.bold = True
            self._refresh_play()
        elif tab == "settings":
            self.content.add_widget(self.settings_widget)
            self.btn_settings.color = (0.7, 0.8, 1, 1)
            self.btn_settings.bold = True

    # ----- SHOP -----
    def _build_shop(self):
        root = BoxLayout(orientation="vertical", padding=[dp(14), dp(10), dp(14), dp(4)], spacing=dp(6))
        header = BoxLayout(size_hint=(1, None), height=dp(48))
        header.add_widget(Label(
            text="SHOP", font_size=sp(24), bold=True, color=(1, 0.88, 0.4, 1),
            size_hint=(0.4, 1), halign="left", valign="middle"
        ))
        self.cups_label = Label(
            text="Cups: 0", font_size=sp(17), bold=True, color=(1, 0.85, 0.35, 1),
            size_hint=(0.6, 1), halign="right", valign="middle"
        )
        self.cups_label.bind(size=self.cups_label.setter("text_size"))
        header.add_widget(self.cups_label)
        root.add_widget(header)

        # Fixed height scroll to avoid jump at bottom
        scroll = ScrollView(
            size_hint=(1, 1), do_scroll_x=False, bar_width=dp(3),
            scroll_type=["bars", "content"]
        )
        self.shop_list = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=dp(9), padding=[0, dp(2), 0, dp(20)]
        )
        self.shop_list.bind(minimum_height=self.shop_list.setter("height"))
        scroll.add_widget(self.shop_list)
        root.add_widget(scroll)
        return root

    def _refresh_shop(self):
        self.cups_label.text = f"Cups: {self.data['cups']}"
        self.shop_list.clear_widgets()

        self.shop_list.add_widget(Label(
            text="SKINS", font_size=sp(12), bold=True,
            color=(0.75, 0.7, 0.9, 1), size_hint=(1, None), height=dp(24)
        ))
        for key, skin in SKINS.items():
            owned = key in self.data["owned_skins"]
            selected = self.data["selected_skin"] == key
            self.shop_list.add_widget(self._shop_row(
                skin["name"],
                f"x{skin['bonus']}" if skin["bonus"] > 1 else "base",
                skin["price"], owned, selected, skin["color"], "skin", key
            ))

        self.shop_list.add_widget(Label(
            text="TRAILS", font_size=sp(12), bold=True,
            color=(0.75, 0.7, 0.9, 1), size_hint=(1, None), height=dp(28)
        ))
        for key, trail in TRAILS.items():
            owned = key in self.data["owned_trails"]
            selected = self.data["selected_trail"] == key
            self.shop_list.add_widget(self._shop_row(
                trail["name"],
                f"x{trail['bonus']}" if trail["bonus"] > 1 else "—",
                trail["price"], owned, selected, trail["color"], "trail", key
            ))

    def _shop_row(self, title, subtitle, price, owned, selected, color, item_type, key):
        box = BoxLayout(
            orientation="horizontal", size_hint=(1, None), height=dp(56),
            padding=[dp(10), dp(6)], spacing=dp(10)
        )
        with box.canvas.before:
            Color(0.16, 0.14, 0.26, 1)
            rr = RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(12)])
        box.bind(pos=lambda *a: setattr(rr, "pos", box.pos),
                 size=lambda *a: setattr(rr, "size", box.size))

        col = get_color_from_hex(color)
        prev = Widget(size_hint=(None, None), size=(dp(34), dp(34)))
        with prev.canvas:
            Color(*col)
            ell = Ellipse(pos=prev.pos, size=prev.size)
        prev.bind(pos=lambda *a: setattr(ell, "pos", prev.pos),
                  size=lambda *a: setattr(ell, "size", prev.size))
        box.add_widget(prev)

        tb = BoxLayout(orientation="vertical", size_hint=(1, 1))
        t1 = Label(text=title, font_size=sp(14), bold=True, color=(0.95, 0.93, 0.9, 1),
                   halign="left", valign="bottom", size_hint=(1, 0.55))
        t2 = Label(text=subtitle, font_size=sp(11), color=(0.65, 0.6, 0.78, 1),
                   halign="left", valign="top", size_hint=(1, 0.45))
        t1.bind(size=t1.setter("text_size"))
        t2.bind(size=t2.setter("text_size"))
        tb.add_widget(t1)
        tb.add_widget(t2)
        box.add_widget(tb)

        if selected:
            btn = PixelButton(text="ON", bg=(0.3, 0.65, 0.4, 1),
                              size_hint=(None, None), size=(dp(72), dp(34)))
            btn.disabled = True
        elif owned:
            btn = PixelButton(text="USE", bg=(0.35, 0.4, 0.75, 1),
                              size_hint=(None, None), size=(dp(72), dp(34)))
            btn.bind(on_press=lambda x, t=item_type, k=key: self._select(t, k))
        else:
            btn = PixelButton(text=f"{price}", bg=(0.7, 0.45, 0.25, 1),
                              size_hint=(None, None), size=(dp(72), dp(34)))
            btn.bind(on_press=lambda x, t=item_type, k=key, p=price: self._buy(t, k, p))
        box.add_widget(btn)
        return box

    def _buy(self, item_type, key, price):
        if self.data["cups"] < price:
            return
        if self.data.get("vibration_on", True):
            do_vibrate(25)
        self.data["cups"] -= price
        if item_type == "skin":
            if key not in self.data["owned_skins"]:
                self.data["owned_skins"].append(key)
            self.data["selected_skin"] = key
        else:
            if key not in self.data["owned_trails"]:
                self.data["owned_trails"].append(key)
            self.data["selected_trail"] = key
        save_data(self.data)
        self._refresh_shop()

    def _select(self, item_type, key):
        if self.data.get("vibration_on", True):
            do_vibrate(18)
        if item_type == "skin":
            self.data["selected_skin"] = key
        else:
            self.data["selected_trail"] = key
        save_data(self.data)
        self._refresh_shop()

    # ----- PLAY -----
    def _build_play(self):
        root = BoxLayout(orientation="vertical", padding=[dp(14), dp(10), dp(14), dp(4)], spacing=dp(6))
        top = BoxLayout(size_hint=(1, None), height=dp(42))
        top.add_widget(Label(
            text="LEVELS", font_size=sp(20), bold=True, color=(0.5, 0.92, 0.65, 1)
        ))
        self.play_cups = Label(text="Cups: 0", font_size=sp(15), bold=True, color=(1, 0.85, 0.35, 1))
        top.add_widget(self.play_cups)
        root.add_widget(top)

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, bar_width=dp(3))
        self.level_list = GridLayout(cols=1, size_hint_y=None, spacing=dp(8), padding=[0, dp(2), 0, dp(12)])
        self.level_list.bind(minimum_height=self.level_list.setter("height"))
        scroll.add_widget(self.level_list)
        root.add_widget(scroll)
        return root

    def _refresh_play(self):
        self.play_cups.text = f"Cups: {self.data['cups']}"
        self.level_list.clear_widgets()
        unlocked = self.data.get("unlocked_levels", 1)

        for lvl in range(1, 101):
            theme = get_level_theme(lvl)
            is_unlocked = lvl <= unlocked
            is_selected = lvl == self.selected_level

            btn = LevelButton(lvl, theme, is_unlocked, is_selected)
            if is_unlocked:
                btn.text = f"  Level {lvl}   {theme['name']}"
                btn.color = (0.95, 0.93, 0.9, 1)
                btn.font_size = sp(14)
                btn.bold = is_selected
                btn.bind(on_press=lambda x, l=lvl: self._start(l))
            else:
                btn.text = f"  Level {lvl}   locked"
                btn.color = (0.4, 0.38, 0.48, 1)
                btn.font_size = sp(13)
                btn.disabled = True
            self.level_list.add_widget(btn)

    def _start(self, level):
        if self.data.get("vibration_on", True):
            do_vibrate(22)
        stop_menu_music()
        game = self.manager.get_screen("game")
        game.setup_level(level, self.data)
        self.manager.transition = SlideTransition(direction="up", duration=0.25)
        self.manager.current = "game"

    # ----- SETTINGS -----
    def _build_settings(self):
        root = BoxLayout(orientation="vertical", padding=[dp(18), dp(12)], spacing=dp(12))
        root.add_widget(Label(
            text="SETTINGS", font_size=sp(22), bold=True, color=(0.72, 0.8, 1, 1),
            size_hint=(1, None), height=dp(42)
        ))

        for label, attr, handler in [
            ("Music", "music_on", self._tog_music),
            ("Sound Effects", "sound_on", self._tog_sound),
            ("Vibration", "vibration_on", self._tog_vib),
        ]:
            row = BoxLayout(size_hint=(1, None), height=dp(46))
            row.add_widget(Label(text=label, font_size=sp(15), color=(0.92, 0.9, 0.95, 1)))
            sw = Switch(active=self.data.get(attr, True))
            sw.bind(active=handler)
            if attr == "music_on":
                self.music_switch = sw
            elif attr == "sound_on":
                self.sound_switch = sw
            else:
                self.vib_switch = sw
            row.add_widget(sw)
            root.add_widget(row)

        root.add_widget(Widget(size_hint=(1, 1)))
        reset = PixelButton(text="Reset Progress", bg=(0.65, 0.22, 0.28, 1),
                            size_hint=(1, None), height=dp(46))
        reset.bind(on_press=self._reset)
        root.add_widget(reset)
        info = Label(
            text="HAUSEL  v0.2\nby LGStudio",
            font_size=sp(12), color=(0.5, 0.48, 0.62, 1),
            size_hint=(1, None), height=dp(50), halign="center"
        )
        info.bind(size=info.setter("text_size"))
        root.add_widget(info)
        return root

    def _tog_music(self, inst, value):
        self.data["music_on"] = value
        save_data(self.data)
        play_menu_music(value)
        if self.data.get("vibration_on", True):
            do_vibrate(15)

    def _tog_sound(self, inst, value):
        self.data["sound_on"] = value
        save_data(self.data)
        if self.data.get("vibration_on", True):
            do_vibrate(15)

    def _tog_vib(self, inst, value):
        self.data["vibration_on"] = value
        save_data(self.data)
        if value:
            do_vibrate(25)

    def _reset(self, *a):
        if self.data.get("vibration_on", True):
            do_vibrate(40)
        self.data = DEFAULT_DATA.copy()
        save_data(self.data)
        self.music_switch.active = True
        self.sound_switch.active = True
        self.vib_switch.active = True
        play_menu_music(True)
        self._tab(self.current_tab)


# ===================== GAME =====================
class Particle:
    def __init__(self, x, y, color, life=0.55):
        self.x, self.y = x, y
        self.vx = random.uniform(-55, 55)
        self.vy = random.uniform(25, 85)
        self.life = life
        self.max_life = life
        self.color = color
        self.size = random.uniform(2.5, 5.5)


class GameWorld(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.level = 1
        self.data = {}
        self.theme = get_level_theme(1)
        self.px = self.py = self.pvx = self.pvy = 0
        self.pw, self.ph = 20, 30
        self.on_ground = False
        self.facing = 1
        self.alive = True
        self.won = False
        self.death_timer = 0
        self.cam_y = 0
        self.platforms = []
        self.hazards = []
        self.goal = None
        self.world_height = 2000
        self.move_left = self.move_right = False
        self.jump_pressed = False
        self.jump_buffer = 0
        self.particles = []
        self.trail_timer = 0
        self.GRAVITY = -1100
        self.MOVE_SPEED = 200
        self.JUMP_FORCE = 460
        self.MAX_FALL = -700
        self._event = None

    def start_level(self, level, data):
        self.level = level
        self.data = data
        self.theme = get_level_theme(level)
        self.alive = True
        self.won = False
        self.death_timer = 0
        self.particles = []
        self.cam_y = 0
        self.pvx = self.pvy = 0
        self.move_left = self.move_right = False
        self.jump_pressed = False
        self.jump_buffer = 0
        self._generate()
        self._draw()
        if self._event:
            self._event.cancel()
        self._event = Clock.schedule_interval(self._update, 1 / 60)

    def stop(self):
        if self._event:
            self._event.cancel()
            self._event = None

    def _generate(self):
        self.platforms = []
        self.hazards = []
        W = max(self.width, 300)
        self.platforms.append((W * 0.15, 50, W * 0.7, 18))
        self.px = W * 0.5 - self.pw / 2
        self.py = 70
        difficulty = 1 + (self.level - 1) * 0.07
        num = 11 + self.level // 6
        y = 50
        prev_x = W * 0.3
        for i in range(num):
            y += random.uniform(55, 95 + difficulty * 6)
            plat_w = random.uniform(60, 120 - min(difficulty * 2.5, 35))
            x = prev_x + random.uniform(-(90 + difficulty * 4), 90 + difficulty * 4)
            x = max(12, min(W - plat_w - 12, x))
            self.platforms.append((x, y, plat_w, 16))
            if i > 1 and random.random() < 0.12 + min(self.level * 0.012, 0.38):
                sx = x + random.uniform(6, max(6, plat_w - 28))
                sw = random.uniform(18, min(36, plat_w - 8))
                self.hazards.append((sx, y + 16, sw, 14))
            prev_x = x
        self.world_height = y + 200
        gy = y + 75
        self.platforms.append((W * 0.2, gy, W * 0.6, 18))
        self.goal = (W * 0.32, gy + 18, W * 0.36, 48)

    def _update(self, dt):
        if not self.alive:
            self.death_timer += dt
            self._upd_particles(dt)
            self._draw()
            if self.death_timer > 1.1:
                self.start_level(self.level, self.data)
            return
        if self.won:
            self._upd_particles(dt)
            self._draw()
            return

        dt = min(dt, 0.04)
        target = 0
        if self.move_left:
            target = -self.MOVE_SPEED
            self.facing = -1
        if self.move_right:
            target = self.MOVE_SPEED
            self.facing = 1
        self.pvx = target

        if self.jump_pressed:
            self.jump_buffer = 0.13
            self.jump_pressed = False
        self.jump_buffer = max(0, self.jump_buffer - dt)
        if self.jump_buffer > 0 and self.on_ground:
            self.pvy = self.JUMP_FORCE
            self.on_ground = False
            self.jump_buffer = 0

        self.pvy += self.GRAVITY * dt
        self.pvy = max(self.pvy, self.MAX_FALL)
        self.px += self.pvx * dt
        self.px = max(0, min(self.width - self.pw, self.px))
        self.py += self.pvy * dt
        self.on_ground = False
        self._collide()

        if self._hit_hazard():
            self._die()
            return
        if self.py < self.cam_y - 100:
            self._die()
            return
        if self.goal and self._overlap(self.px, self.py, self.pw, self.ph, *self.goal):
            self._win()
            return

        target_cam = self.py - self.height * 0.38
        self.cam_y += (target_cam - self.cam_y) * min(1, 6 * dt)
        if self.cam_y < 0:
            self.cam_y = 0

        self.trail_timer += dt
        tk = self.data.get("selected_trail", "none")
        if tk != "none" and self.trail_timer > 0.035 and (abs(self.pvx) > 15 or abs(self.pvy) > 40):
            self.trail_timer = 0
            col = get_color_from_hex(TRAILS[tk]["color"])
            self.particles.append(Particle(self.px + self.pw / 2 + random.uniform(-5, 5), self.py + 5, col))

        self._upd_particles(dt)
        self._draw()

    def _collide(self):
        for (x, y, w, h) in self.platforms:
            if self._overlap(self.px, self.py, self.pw, self.ph, x, y, w, h):
                if self.pvy <= 0 and self.py + self.ph - self.pvy * 0.02 >= y + h:
                    self.py = y + h
                    self.pvy = 0
                    self.on_ground = True
                elif self.pvy > 0 and self.py <= y:
                    self.py = y - self.ph
                    self.pvy = 0
                else:
                    if self.px + self.pw / 2 < x + w / 2:
                        self.px = x - self.pw
                    else:
                        self.px = x + w

    def _hit_hazard(self):
        for (x, y, w, h) in self.hazards:
            if self._overlap(self.px + 3, self.py, self.pw - 6, self.ph - 3, x, y, w, h):
                return True
        return False

    def _overlap(self, ax, ay, aw, ah, bx, by, bw, bh):
        return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by

    def _die(self):
        self.alive = False
        self.death_timer = 0
        if self.data.get("vibration_on", True):
            do_vibrate(80)
        col = get_color_from_hex(self.theme["hazard"])
        for _ in range(18):
            self.particles.append(Particle(self.px + self.pw / 2, self.py + self.ph / 2, col, 0.7))

    def _win(self):
        self.won = True
        if self.data.get("vibration_on", True):
            do_vibrate(50)
        base = 10 + self.level * 3
        sb = SKINS.get(self.data.get("selected_skin", "default"), {}).get("bonus", 1.0)
        tb = TRAILS.get(self.data.get("selected_trail", "none"), {}).get("bonus", 1.0)
        earned = int(base * sb * tb)
        self.data["cups"] = self.data.get("cups", 0) + earned
        if self.level >= self.data.get("unlocked_levels", 1):
            self.data["unlocked_levels"] = self.level + 1
        save_data(self.data)
        self.earned_cups = earned
        col = get_color_from_hex("#E8C04A")
        for _ in range(26):
            self.particles.append(Particle(self.px + self.pw / 2, self.py + self.ph, col, 1.0))

    def _upd_particles(self, dt):
        alive = []
        for p in self.particles:
            p.life -= dt
            if p.life > 0:
                p.x += p.vx * dt
                p.y += p.vy * dt
                p.vy -= 300 * dt
                alive.append(p)
        self.particles = alive

    def _draw(self):
        self.canvas.clear()
        W, H = self.width, self.height
        cam = self.cam_y
        with self.canvas:
            bg = get_color_from_hex(self.theme["bg"])
            Color(*bg)
            Rectangle(pos=(0, 0), size=(W, H))
            Color(1, 1, 1, 0.06)
            random.seed(self.level * 91)
            for _ in range(28):
                sx = random.uniform(0, W)
                sy = random.uniform(0, self.world_height)
                if 0 < sy - cam < H:
                    Rectangle(pos=(sx, sy - cam), size=(2.2, 2.2))
            random.seed()

            plat = get_color_from_hex(self.theme["plat"])
            for (x, y, w, h) in self.platforms:
                if y + h < cam - 30 or y > cam + H + 30:
                    continue
                Color(*plat)
                Rectangle(pos=(x, y - cam), size=(w, h))
                Color(min(1, plat[0] + 0.15), min(1, plat[1] + 0.15), min(1, plat[2] + 0.15), 1)
                Rectangle(pos=(x, y + h - 3 - cam), size=(w, 3))

            haz = get_color_from_hex(self.theme["hazard"])
            for (x, y, w, h) in self.hazards:
                if y + h < cam - 15 or y > cam + H + 15:
                    continue
                Color(*haz)
                n = max(2, int(w / 11))
                sw = w / n
                for i in range(n):
                    sx = x + i * sw
                    Triangle(points=[sx, y - cam, sx + sw / 2, y + h - cam, sx + sw, y - cam])

            if self.goal:
                gx, gy, gw, gh = self.goal
                if gy < cam + H + 30:
                    Color(0.95, 0.85, 0.3, 1)
                    Rectangle(pos=(gx + gw / 2 - 2.5, gy - cam), size=(5, gh))
                    Color(0.9, 0.35, 0.4, 1)
                    Triangle(points=[
                        gx + gw / 2 + 2.5, gy + gh - cam,
                        gx + gw / 2 + 2.5, gy + gh - 18 - cam,
                        gx + gw / 2 + 24, gy + gh - 9 - cam
                    ])

            for p in self.particles:
                a = max(0, p.life / p.max_life)
                Color(p.color[0], p.color[1], p.color[2], a)
                Rectangle(pos=(p.x - p.size / 2, p.y - cam - p.size / 2), size=(p.size, p.size))

            if self.alive:
                skin = SKINS.get(self.data.get("selected_skin", "default"), SKINS["default"])
                pc = get_color_from_hex(skin["color"])
                px, py = self.px, self.py - cam
                Color(pc[0] * 0.65, pc[1] * 0.65, pc[2] * 0.65, 1)
                Rectangle(pos=(px + 3, py), size=(6, 11))
                Rectangle(pos=(px + 11, py), size=(6, 11))
                Color(*pc)
                Rectangle(pos=(px + 2, py + 10), size=(16, 13))
                Color(min(1, pc[0] * 1.08), min(1, pc[1] * 1.08), min(1, pc[2] * 1.08), 1)
                Ellipse(pos=(px + 3, py + 22), size=(14, 14))
                Color(0.12, 0.1, 0.16, 1)
                ex = px + 9 if self.facing > 0 else px + 5
                Ellipse(pos=(ex, py + 27), size=(3.5, 3.5))


class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.level = 1
        self.data = {}
        self.root_layout = FloatLayout()
        self.world = GameWorld(size_hint=(1, 1))
        self.root_layout.add_widget(self.world)

        self.info_label = Label(
            text="Level 1", font_size=sp(15), bold=True, color=(0.95, 0.93, 0.9, 0.95),
            size_hint=(None, None), size=(dp(220), dp(30)),
            pos_hint={"x": 0.03, "top": 0.97}, halign="left"
        )
        self.info_label.bind(size=self.info_label.setter("text_size"))
        self.root_layout.add_widget(self.info_label)

        self.pause_btn = PixelButton(
            text="MENU", bg=(0.5, 0.22, 0.28, 0.9),
            size_hint=(None, None), size=(dp(84), dp(36)),
            pos_hint={"right": 0.97, "top": 0.97}
        )
        self.pause_btn.bind(on_press=self._menu)
        self.root_layout.add_widget(self.pause_btn)

        self.win_label = Label(
            text="", font_size=sp(22), bold=True, color=(1, 0.9, 0.4, 1),
            size_hint=(None, None), size=(dp(280), dp(80)),
            pos_hint={"center_x": 0.5, "center_y": 0.58},
            halign="center", opacity=0
        )
        self.win_label.bind(size=self.win_label.setter("text_size"))
        self.root_layout.add_widget(self.win_label)

        self.continue_btn = PixelButton(
            text="CONTINUE", bg=(0.25, 0.65, 0.4, 1),
            size_hint=(None, None), size=(dp(160), dp(48)),
            pos_hint={"center_x": 0.5, "center_y": 0.4},
            opacity=0, disabled=True
        )
        self.continue_btn.bind(on_press=self._after_win)
        self.root_layout.add_widget(self.continue_btn)

        self.ctrl = BoxLayout(
            orientation="horizontal", size_hint=(1, None), height=dp(74),
            pos_hint={"x": 0, "y": 0}, padding=[dp(10), dp(10)], spacing=dp(10)
        )
        with self.ctrl.canvas.before:
            Color(0.06, 0.05, 0.1, 0.5)
            self.ctrl_bg = Rectangle(pos=self.ctrl.pos, size=self.ctrl.size)
        self.ctrl.bind(pos=lambda *a: setattr(self.ctrl_bg, "pos", self.ctrl.pos),
                       size=lambda *a: setattr(self.ctrl_bg, "size", self.ctrl.size))

        self.btn_left = PixelButton(text="◀", bg=(0.28, 0.26, 0.42, 0.95), size_hint=(0.28, 1))
        self.btn_jump = PixelButton(text="JUMP", bg=(0.32, 0.45, 0.8, 0.95), size_hint=(0.44, 1))
        self.btn_right = PixelButton(text="▶", bg=(0.28, 0.26, 0.42, 0.95), size_hint=(0.28, 1))
        self.btn_left.bind(on_press=lambda x: self._move("left", True), on_release=lambda x: self._move("left", False))
        self.btn_right.bind(on_press=lambda x: self._move("right", True), on_release=lambda x: self._move("right", False))
        self.btn_jump.bind(on_press=lambda x: self._jump())
        self.ctrl.add_widget(self.btn_left)
        self.ctrl.add_widget(self.btn_jump)
        self.ctrl.add_widget(self.btn_right)
        self.root_layout.add_widget(self.ctrl)
        self.add_widget(self.root_layout)
        Window.bind(on_key_down=self._kd, on_key_up=self._ku)

    def _move(self, side, state):
        if side == "left":
            self.world.move_left = state
        else:
            self.world.move_right = state

    def _jump(self):
        self.world.jump_pressed = True
        if self.data.get("vibration_on", True):
            do_vibrate(12)

    def _kd(self, w, key, sc, code, mod):
        if self.manager.current != "game":
            return
        if key in (276, 97):
            self.world.move_left = True
        elif key in (275, 100):
            self.world.move_right = True
        elif key in (32, 273, 119):
            self.world.jump_pressed = True

    def _ku(self, w, key, sc):
        if key in (276, 97):
            self.world.move_left = False
        elif key in (275, 100):
            self.world.move_right = False

    def setup_level(self, level, data):
        self.level = level
        self.data = data
        self.win_label.opacity = 0
        self.continue_btn.opacity = 0
        self.continue_btn.disabled = True
        theme = get_level_theme(level)
        self.info_label.text = f"Lv.{level}  {theme['name']}"
        Clock.schedule_once(lambda dt: self.world.start_level(level, data), 0.04)

    def on_leave(self, *a):
        self.world.stop()

    def _menu(self, *a):
        if self.data.get("vibration_on", True):
            do_vibrate(18)
        self.world.stop()
        self.manager.transition = SlideTransition(direction="down", duration=0.22)
        self.manager.current = "main"

    def _check_win(self, dt):
        if self.world.won and self.win_label.opacity == 0:
            earned = getattr(self.world, "earned_cups", 0)
            self.win_label.text = f"LEVEL CLEAR!\n+{earned} Cups"
            self.win_label.opacity = 1
            self.continue_btn.opacity = 1
            self.continue_btn.disabled = False
            return False
        return True

    def on_enter(self, *a):
        Clock.schedule_interval(self._check_win, 0.1)

    def _after_win(self, *a):
        if self.data.get("vibration_on", True):
            do_vibrate(20)
        self.world.stop()
        self.manager.transition = SlideTransition(direction="down", duration=0.22)
        self.manager.current = "main"


class HauselApp(App):
    def build(self):
        self.title = "HAUSEL"
        sm = ScreenManager()
        sm.add_widget(LoadingScreen(name="loading"))
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(GameScreen(name="game"))
        sm.current = "loading"
        return sm


if __name__ == "__main__":
    HauselApp().run()
