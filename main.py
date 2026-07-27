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
from kivy.graphics import Color, Rectangle, RoundedRectangle, Ellipse, Line, Triangle
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.storage.jsonstore import JsonStore
from kivy.metrics import dp, sp
from kivy.utils import get_color_from_hex
from kivy.utils import platform
import random

# Only force size on desktop for testing
if platform not in ("android", "ios"):
    Window.size = (360, 720)
Window.clearcolor = (0.12, 0.10, 0.22, 1)

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

# ===================== THEMES =====================
LEVEL_THEMES = [
    {"name": "Green Hills", "color": "#4ADE80", "bg": "#0F2A1A", "plat": "#22C55E", "hazard": "#EF4444"},
    {"name": "Forest Rise", "color": "#A3E635", "bg": "#1A2E0A", "plat": "#84CC16", "hazard": "#F97316"},
    {"name": "Mint Climb",  "color": "#2DD4BF", "bg": "#0A2A28", "plat": "#14B8A6", "hazard": "#EC4899"},
    {"name": "Sky Steps",   "color": "#38BDF8", "bg": "#0A1E2E", "plat": "#0EA5E9", "hazard": "#F59E0B"},
    {"name": "Azure Peak",  "color": "#60A5FA", "bg": "#0A1628", "plat": "#3B82F6", "hazard": "#EF4444"},
    {"name": "Blue Height", "color": "#818CF8", "bg": "#12102A", "plat": "#6366F1", "hazard": "#F97316"},
    {"name": "Indigo Wall", "color": "#A78BFA", "bg": "#1A0F2A", "plat": "#8B5CF6", "hazard": "#EF4444"},
    {"name": "Violet Path", "color": "#C084FC", "bg": "#1E0A28", "plat": "#A855F7", "hazard": "#F43F5E"},
    {"name": "Purple Gate", "color": "#F472B6", "bg": "#2A0A1E", "plat": "#EC4899", "hazard": "#FBBF24"},
    {"name": "Pink Summit", "color": "#FB7185", "bg": "#2A0A14", "plat": "#F43F5E", "hazard": "#22D3EE"},
]

def get_level_theme(level):
    return LEVEL_THEMES[(level - 1) % 10].copy()

# ===================== SHOP =====================
SKINS = {
    "default": {"name": "Classic", "price": 0,   "bonus": 1.0,  "color": "#FFFFFF"},
    "red":     {"name": "Crimson", "price": 50,  "bonus": 1.1,  "color": "#FF6B6B"},
    "blue":    {"name": "Ocean",   "price": 80,  "bonus": 1.15, "color": "#4ECDC4"},
    "gold":    {"name": "Golden",  "price": 150, "bonus": 1.3,  "color": "#FFD93D"},
    "neon":    {"name": "Neon",    "price": 250, "bonus": 1.5,  "color": "#6BCB77"},
    "shadow":  {"name": "Shadow",  "price": 400, "bonus": 1.8,  "color": "#A78BFA"},
}

TRAILS = {
    "none":    {"name": "No Trail",   "price": 0,   "bonus": 1.0,  "color": "#888888"},
    "white":   {"name": "White Dust", "price": 40,  "bonus": 1.05, "color": "#FFFFFF"},
    "fire":    {"name": "Fire Trail", "price": 100, "bonus": 1.2,  "color": "#FF6B35"},
    "ice":     {"name": "Ice Trail",  "price": 120, "bonus": 1.25, "color": "#4ECDC4"},
    "rainbow": {"name": "Rainbow",    "price": 300, "bonus": 1.6,  "color": "#FF6BCB"},
    "stars":   {"name": "Star Dust",  "price": 500, "bonus": 2.0,  "color": "#FFE66D"},
}

# ===================== WIDGETS =====================
class BottomBarButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.color = (0.75, 0.75, 0.85, 1)
        self.font_size = sp(15)
        self.bold = True


class PixelButton(Button):
    def __init__(self, bg=(0.35, 0.45, 0.95, 1), **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = bg
        self.color = (1, 1, 1, 1)
        self.font_size = sp(16)
        self.bold = True


# ===================== LOADING =====================
class LoadingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = FloatLayout()
        with root.canvas.before:
            Color(0.10, 0.08, 0.20, 1)
            self.bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=self._upd_bg, size=self._upd_bg)

        # Decorative circles
        with root.canvas.before:
            Color(0.4, 0.3, 0.8, 0.15)
            self.c1 = Ellipse(pos=(0, 0), size=(200, 200))
            Color(0.9, 0.3, 0.5, 0.12)
            self.c2 = Ellipse(pos=(0, 0), size=(160, 160))

        title = Label(
            text="HAUSEL",
            font_size=sp(52),
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(1, None),
            height=dp(70),
            pos_hint={"center_x": 0.5, "center_y": 0.62}
        )
        root.add_widget(title)

        sub = Label(
            text="by LGStudio",
            font_size=sp(16),
            color=(0.7, 0.65, 0.9, 1),
            size_hint=(1, None),
            height=dp(28),
            pos_hint={"center_x": 0.5, "center_y": 0.54}
        )
        root.add_widget(sub)

        tag = Label(
            text="100 levels  •  Vertical parkour",
            font_size=sp(14),
            color=(0.55, 0.5, 0.7, 1),
            size_hint=(1, None),
            height=dp(26),
            pos_hint={"center_x": 0.5, "center_y": 0.48}
        )
        root.add_widget(tag)

        self.progress = ProgressBar(
            max=100, value=0,
            size_hint=(0.7, None), height=dp(10),
            pos_hint={"center_x": 0.5, "center_y": 0.34}
        )
        root.add_widget(self.progress)

        self.loading_label = Label(
            text="Loading...",
            font_size=sp(13),
            color=(0.6, 0.55, 0.75, 1),
            size_hint=(1, None), height=dp(28),
            pos_hint={"center_x": 0.5, "center_y": 0.28}
        )
        root.add_widget(self.loading_label)
        self.add_widget(root)
        self.progress_val = 0

    def _upd_bg(self, *a):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.c1.pos = (self.width * 0.6, self.height * 0.7)
        self.c1.size = (self.width * 0.5, self.width * 0.5)
        self.c2.pos = (-self.width * 0.15, self.height * 0.1)
        self.c2.size = (self.width * 0.45, self.width * 0.45)

    def on_enter(self):
        self.progress_val = 0
        self.progress.value = 0
        Clock.schedule_interval(self._update_progress, 0.03)

    def _update_progress(self, dt):
        self.progress_val += random.uniform(2.0, 4.5)
        if self.progress_val >= 100:
            self.progress.value = 100
            self.loading_label.text = "Let's go!"
            Clock.unschedule(self._update_progress)
            Clock.schedule_once(self._go_main, 0.4)
            return False
        self.progress.value = self.progress_val
        self.loading_label.text = "Loading" + "." * (int(self.progress_val / 15) % 4)
        return True

    def _go_main(self, dt):
        self.manager.transition = FadeTransition(duration=0.3)
        self.manager.current = "main"


# ===================== MAIN MENU =====================
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = load_data()
        self.current_tab = "play"
        self.selected_level = 1

        root = BoxLayout(orientation="vertical", padding=0, spacing=0)

        # Content area - takes all free space
        self.content = FloatLayout(size_hint=(1, 1))
        root.add_widget(self.content)

        # Bottom navigation bar
        self.bottom = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(72),
            padding=[dp(6), dp(8)],
            spacing=dp(6)
        )
        with self.bottom.canvas.before:
            Color(0.14, 0.12, 0.26, 1)
            self.bar_rect = Rectangle(pos=self.bottom.pos, size=self.bottom.size)
            Color(0.45, 0.35, 0.85, 0.6)
            self.bar_line = Rectangle(pos=(0, 0), size=(0, 3))
        self.bottom.bind(pos=self._upd_bar, size=self._upd_bar)

        self.btn_shop = BottomBarButton(text="SHOP")
        self.btn_play = BottomBarButton(text="PLAY")
        self.btn_settings = BottomBarButton(text="SETTINGS")

        self.btn_shop.bind(on_press=lambda x: self.switch_tab("shop"))
        self.btn_play.bind(on_press=lambda x: self.switch_tab("play"))
        self.btn_settings.bind(on_press=lambda x: self.switch_tab("settings"))

        self.bottom.add_widget(self.btn_shop)
        self.bottom.add_widget(self.btn_play)
        self.bottom.add_widget(self.btn_settings)
        root.add_widget(self.bottom)
        self.add_widget(root)

        # Background for whole screen
        with self.canvas.before:
            Color(0.12, 0.10, 0.22, 1)
            self.screen_bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._upd_screen_bg, size=self._upd_screen_bg)

        self.shop_widget = self._build_shop()
        self.play_widget = self._build_play()
        self.settings_widget = self._build_settings()
        self.switch_tab("play")

    def _upd_screen_bg(self, *a):
        self.screen_bg.pos = self.pos
        self.screen_bg.size = self.size

    def on_enter(self, *args):
        self.data = load_data()
        if self.current_tab == "play":
            self._refresh_play()
        elif self.current_tab == "shop":
            self._refresh_shop()

    def _upd_bar(self, *a):
        self.bar_rect.pos = self.bottom.pos
        self.bar_rect.size = self.bottom.size
        self.bar_line.pos = (self.bottom.x, self.bottom.top - 3)
        self.bar_line.size = (self.bottom.width, 3)

    def switch_tab(self, tab):
        self.current_tab = tab
        self.content.clear_widgets()
        for btn in (self.btn_shop, self.btn_play, self.btn_settings):
            btn.color = (0.6, 0.55, 0.75, 1)
            btn.bold = False

        if tab == "shop":
            self.content.add_widget(self.shop_widget)
            self.btn_shop.color = (1, 0.9, 0.4, 1)
            self.btn_shop.bold = True
            self._refresh_shop()
        elif tab == "play":
            self.content.add_widget(self.play_widget)
            self.btn_play.color = (0.4, 1, 0.6, 1)
            self.btn_play.bold = True
            self._refresh_play()
            self.play_widget.opacity = 0
            Animation(opacity=1, duration=0.25, t="out_quad").start(self.play_widget)
        elif tab == "settings":
            self.content.add_widget(self.settings_widget)
            self.btn_settings.color = (0.7, 0.8, 1, 1)
            self.btn_settings.bold = True

    # ----- SHOP -----
    def _build_shop(self):
        root = BoxLayout(orientation="vertical", padding=[dp(14), dp(12), dp(14), dp(6)], spacing=dp(8))

        header = BoxLayout(size_hint=(1, None), height=dp(50))
        header.add_widget(Label(
            text="SHOP", font_size=sp(26), bold=True, color=(1, 0.9, 0.4, 1),
            size_hint=(0.45, 1), halign="left", valign="middle"
        ))
        self.cups_label = Label(
            text="Cups: 0", font_size=sp(18), bold=True, color=(1, 0.85, 0.3, 1),
            size_hint=(0.55, 1), halign="right", valign="middle"
        )
        self.cups_label.bind(size=self.cups_label.setter("text_size"))
        header.add_widget(self.cups_label)
        root.add_widget(header)

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, bar_width=dp(4))
        self.shop_list = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=dp(10), padding=[0, dp(4)]
        )
        self.shop_list.bind(minimum_height=self.shop_list.setter("height"))
        scroll.add_widget(self.shop_list)
        root.add_widget(scroll)
        return root

    def _refresh_shop(self):
        self.cups_label.text = f"Cups: {self.data['cups']}"
        self.shop_list.clear_widgets()

        self.shop_list.add_widget(Label(
            text="CHARACTER SKINS", font_size=sp(13), bold=True,
            color=(0.8, 0.75, 1, 1), size_hint=(1, None), height=dp(28)
        ))
        for key, skin in SKINS.items():
            owned = key in self.data["owned_skins"]
            selected = self.data["selected_skin"] == key
            self.shop_list.add_widget(self._make_shop_item(
                skin["name"],
                f"x{skin['bonus']} cups" if skin["bonus"] > 1 else "Default",
                skin["price"], owned, selected, skin["color"], "skin", key
            ))

        self.shop_list.add_widget(Label(
            text="TRAILS", font_size=sp(13), bold=True,
            color=(0.8, 0.75, 1, 1), size_hint=(1, None), height=dp(32)
        ))
        for key, trail in TRAILS.items():
            owned = key in self.data["owned_trails"]
            selected = self.data["selected_trail"] == key
            self.shop_list.add_widget(self._make_shop_item(
                trail["name"],
                f"x{trail['bonus']} cups" if trail["bonus"] > 1 else "No bonus",
                trail["price"], owned, selected, trail["color"], "trail", key
            ))

    def _make_shop_item(self, title, subtitle, price, owned, selected, color, item_type, item_key):
        box = BoxLayout(
            orientation="horizontal", size_hint=(1, None), height=dp(60),
            padding=[dp(12), dp(8)], spacing=dp(12)
        )
        with box.canvas.before:
            Color(0.18, 0.15, 0.32, 1)
            rr = RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(14)])
        box.bind(pos=lambda *a: setattr(rr, "pos", box.pos),
                 size=lambda *a: setattr(rr, "size", box.size))

        col = get_color_from_hex(color)
        preview = Widget(size_hint=(None, None), size=(dp(38), dp(38)))
        with preview.canvas:
            Color(*col)
            ell = Ellipse(pos=preview.pos, size=preview.size)
        preview.bind(pos=lambda *a: setattr(ell, "pos", preview.pos),
                     size=lambda *a: setattr(ell, "size", preview.size))
        box.add_widget(preview)

        text_box = BoxLayout(orientation="vertical", size_hint=(1, 1))
        t1 = Label(text=title, font_size=sp(15), bold=True, color=(1, 1, 1, 1),
                   halign="left", valign="bottom", size_hint=(1, 0.55))
        t2 = Label(text=subtitle, font_size=sp(12), color=(0.7, 0.65, 0.85, 1),
                   halign="left", valign="top", size_hint=(1, 0.45))
        t1.bind(size=t1.setter("text_size"))
        t2.bind(size=t2.setter("text_size"))
        text_box.add_widget(t1)
        text_box.add_widget(t2)
        box.add_widget(text_box)

        if selected:
            btn = PixelButton(text="ON", bg=(0.25, 0.7, 0.4, 1),
                              size_hint=(None, None), size=(dp(78), dp(36)))
            btn.disabled = True
        elif owned:
            btn = PixelButton(text="SELECT", bg=(0.35, 0.45, 0.9, 1),
                              size_hint=(None, None), size=(dp(78), dp(36)))
            btn.bind(on_press=lambda x, t=item_type, k=item_key: self._select_item(t, k))
        else:
            btn = PixelButton(text=f"{price} C", bg=(0.75, 0.45, 0.2, 1),
                              size_hint=(None, None), size=(dp(78), dp(36)))
            btn.bind(on_press=lambda x, t=item_type, k=item_key, p=price: self._buy_item(t, k, p))
        box.add_widget(btn)
        return box

    def _buy_item(self, item_type, key, price):
        if self.data["cups"] < price:
            return
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

    def _select_item(self, item_type, key):
        if item_type == "skin":
            self.data["selected_skin"] = key
        else:
            self.data["selected_trail"] = key
        save_data(self.data)
        self._refresh_shop()

    # ----- PLAY -----
    def _build_play(self):
        root = BoxLayout(orientation="vertical", padding=[dp(14), dp(10), dp(14), dp(6)], spacing=dp(8))

        top = BoxLayout(size_hint=(1, None), height=dp(44))
        top.add_widget(Label(
            text="SELECT LEVEL", font_size=sp(20), bold=True, color=(0.5, 1, 0.7, 1)
        ))
        self.play_cups = Label(text="Cups: 0", font_size=sp(16), bold=True, color=(1, 0.85, 0.3, 1))
        top.add_widget(self.play_cups)
        root.add_widget(top)

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, bar_width=dp(4))
        self.level_list = GridLayout(cols=1, size_hint_y=None, spacing=dp(8), padding=[0, dp(4)])
        self.level_list.bind(minimum_height=self.level_list.setter("height"))
        scroll.add_widget(self.level_list)
        root.add_widget(scroll)

        self.play_btn = PixelButton(
            text="▶  PLAY", bg=(0.2, 0.75, 0.45, 1),
            size_hint=(1, None), height=dp(54)
        )
        self.play_btn.bind(on_press=self._start_game)
        root.add_widget(self.play_btn)
        return root

    def _refresh_play(self):
        self.play_cups.text = f"Cups: {self.data['cups']}"
        self.level_list.clear_widgets()
        unlocked = self.data.get("unlocked_levels", 1)

        for lvl in range(1, 101):
            theme = get_level_theme(lvl)
            is_unlocked = lvl <= unlocked
            is_selected = lvl == self.selected_level

            col = get_color_from_hex(theme["color"])
            if not is_unlocked:
                col = (col[0] * 0.3, col[1] * 0.3, col[2] * 0.3, 0.5)

            text = f"Level {lvl}  •  {theme['name']}"
            if is_selected:
                text = f"▶ Level {lvl}  •  {theme['name']}"

            btn = Button(
                text=text,
                size_hint=(1, None), height=dp(50),
                background_normal="", background_down="",
                background_color=col,
                color=(1, 1, 1, 1) if is_unlocked else (0.55, 0.55, 0.6, 1),
                font_size=sp(14), bold=is_selected,
                disabled=not is_unlocked
            )
            btn.bind(on_press=lambda x, l=lvl: self._select_level(l))
            self.level_list.add_widget(btn)

    def _select_level(self, level):
        self.selected_level = level
        self._refresh_play()

    def _start_game(self, *args):
        game = self.manager.get_screen("game")
        game.setup_level(self.selected_level, self.data)
        self.manager.transition = SlideTransition(direction="up", duration=0.28)
        self.manager.current = "game"

    # ----- SETTINGS -----
    def _build_settings(self):
        root = BoxLayout(orientation="vertical", padding=[dp(18), dp(14)], spacing=dp(14))

        root.add_widget(Label(
            text="SETTINGS", font_size=sp(24), bold=True, color=(0.75, 0.85, 1, 1),
            size_hint=(1, None), height=dp(44)
        ))

        for label, attr, handler in [
            ("Music", "music_on", self._toggle_music),
            ("Sound Effects", "sound_on", self._toggle_sound),
            ("Vibration", "vibration_on", self._toggle_vib),
        ]:
            row = BoxLayout(size_hint=(1, None), height=dp(48))
            row.add_widget(Label(text=label, font_size=sp(16), color=(0.95, 0.92, 1, 1)))
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

        reset_btn = PixelButton(
            text="Reset Progress", bg=(0.7, 0.2, 0.25, 1),
            size_hint=(1, None), height=dp(48)
        )
        reset_btn.bind(on_press=self._reset_progress)
        root.add_widget(reset_btn)

        info = Label(
            text="HAUSEL  v0.1\nby LGStudio\nVertical platformer • 100 levels",
            font_size=sp(13), color=(0.55, 0.5, 0.7, 1),
            size_hint=(1, None), height=dp(70), halign="center"
        )
        info.bind(size=info.setter("text_size"))
        root.add_widget(info)
        return root

    def _toggle_music(self, inst, value):
        self.data["music_on"] = value
        save_data(self.data)

    def _toggle_sound(self, inst, value):
        self.data["sound_on"] = value
        save_data(self.data)

    def _toggle_vib(self, inst, value):
        self.data["vibration_on"] = value
        save_data(self.data)

    def _reset_progress(self, *args):
        self.data = DEFAULT_DATA.copy()
        save_data(self.data)
        self.music_switch.active = True
        self.sound_switch.active = True
        self.vib_switch.active = True
        self.switch_tab(self.current_tab)


# ===================== GAME ENGINE =====================
class Particle:
    def __init__(self, x, y, color, life=0.6):
        self.x = x
        self.y = y
        self.vx = random.uniform(-50, 50)
        self.vy = random.uniform(30, 90)
        self.life = life
        self.max_life = life
        self.color = color
        self.size = random.uniform(2.5, 6)


class GameWorld(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.level = 1
        self.data = {}
        self.theme = get_level_theme(1)

        self.px = 0
        self.py = 0
        self.pvx = 0
        self.pvy = 0
        self.pw = 20
        self.ph = 30
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

        self.move_left = False
        self.move_right = False
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
        self.pvx = 0
        self.pvy = 0
        self.move_left = False
        self.move_right = False
        self.jump_pressed = False
        self.jump_buffer = 0
        self._generate_level()
        self._draw()
        if self._event:
            self._event.cancel()
        self._event = Clock.schedule_interval(self._update, 1 / 60)

    def stop(self):
        if self._event:
            self._event.cancel()
            self._event = None

    def _generate_level(self):
        self.platforms = []
        self.hazards = []
        W = max(self.width, 300)

        self.platforms.append((W * 0.15, 50, W * 0.7, 18))
        self.px = W * 0.5 - self.pw / 2
        self.py = 70

        difficulty = 1 + (self.level - 1) * 0.07
        num_plats = 11 + self.level // 6
        y = 50
        prev_x = W * 0.3

        for i in range(num_plats):
            gap = random.uniform(55, 95 + difficulty * 6)
            y += gap
            plat_w = random.uniform(60, 120 - min(difficulty * 2.5, 35))
            max_shift = 90 + difficulty * 4
            x = prev_x + random.uniform(-max_shift, max_shift)
            x = max(12, min(W - plat_w - 12, x))
            h = 16
            self.platforms.append((x, y, plat_w, h))

            spike_chance = 0.12 + min(self.level * 0.012, 0.38)
            if i > 1 and random.random() < spike_chance:
                sx = x + random.uniform(6, max(6, plat_w - 28))
                sw = random.uniform(18, min(36, plat_w - 8))
                self.hazards.append((sx, y + h, sw, 14))

            prev_x = x

        self.world_height = y + 200
        goal_y = y + 75
        self.platforms.append((W * 0.2, goal_y, W * 0.6, 18))
        self.goal = (W * 0.32, goal_y + 18, W * 0.36, 48)

    def _update(self, dt):
        if not self.alive:
            self.death_timer += dt
            self._update_particles(dt)
            self._draw()
            if self.death_timer > 1.1:
                self.start_level(self.level, self.data)
            return

        if self.won:
            self._update_particles(dt)
            self._draw()
            return

        dt = min(dt, 0.04)

        target_vx = 0
        if self.move_left:
            target_vx = -self.MOVE_SPEED
            self.facing = -1
        if self.move_right:
            target_vx = self.MOVE_SPEED
            self.facing = 1
        self.pvx = target_vx

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
        self._resolve_platforms()

        if self._check_hazards():
            self._die()
            return

        if self.py < self.cam_y - 100:
            self._die()
            return

        if self.goal and self._rects_overlap(
            self.px, self.py, self.pw, self.ph,
            self.goal[0], self.goal[1], self.goal[2], self.goal[3]
        ):
            self._win()
            return

        target_cam = self.py - self.height * 0.38
        self.cam_y += (target_cam - self.cam_y) * min(1, 6 * dt)
        if self.cam_y < 0:
            self.cam_y = 0

        self.trail_timer += dt
        trail_key = self.data.get("selected_trail", "none")
        if trail_key != "none" and self.trail_timer > 0.035 and (abs(self.pvx) > 15 or abs(self.pvy) > 40):
            self.trail_timer = 0
            col = get_color_from_hex(TRAILS[trail_key]["color"])
            self.particles.append(Particle(
                self.px + self.pw / 2 + random.uniform(-5, 5),
                self.py + 5, col, life=0.5
            ))

        self._update_particles(dt)
        self._draw()

    def _resolve_platforms(self):
        for (x, y, w, h) in self.platforms:
            if self._rects_overlap(self.px, self.py, self.pw, self.ph, x, y, w, h):
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

    def _check_hazards(self):
        for (x, y, w, h) in self.hazards:
            if self._rects_overlap(self.px + 3, self.py, self.pw - 6, self.ph - 3, x, y, w, h):
                return True
        return False

    def _rects_overlap(self, ax, ay, aw, ah, bx, by, bw, bh):
        return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by

    def _die(self):
        self.alive = False
        self.death_timer = 0
        col = get_color_from_hex(self.theme["hazard"])
        for _ in range(20):
            self.particles.append(Particle(
                self.px + self.pw / 2, self.py + self.ph / 2, col, life=0.75
            ))

    def _win(self):
        self.won = True
        base = 10 + self.level * 3
        skin_b = SKINS.get(self.data.get("selected_skin", "default"), {}).get("bonus", 1.0)
        trail_b = TRAILS.get(self.data.get("selected_trail", "none"), {}).get("bonus", 1.0)
        earned = int(base * skin_b * trail_b)
        self.data["cups"] = self.data.get("cups", 0) + earned
        if self.level >= self.data.get("unlocked_levels", 1):
            self.data["unlocked_levels"] = self.level + 1
        save_data(self.data)
        self.earned_cups = earned
        col = get_color_from_hex("#FFD93D")
        for _ in range(28):
            self.particles.append(Particle(
                self.px + self.pw / 2, self.py + self.ph, col, life=1.1
            ))

    def _update_particles(self, dt):
        alive = []
        for p in self.particles:
            p.life -= dt
            if p.life > 0:
                p.x += p.vx * dt
                p.y += p.vy * dt
                p.vy -= 320 * dt
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

            Color(1, 1, 1, 0.07)
            random.seed(self.level * 91)
            for _ in range(30):
                sx = random.uniform(0, W)
                sy = random.uniform(0, self.world_height)
                if 0 < sy - cam < H:
                    Rectangle(pos=(sx, sy - cam), size=(2.5, 2.5))
            random.seed()

            plat_c = get_color_from_hex(self.theme["plat"])
            for (x, y, w, h) in self.platforms:
                if y + h < cam - 30 or y > cam + H + 30:
                    continue
                Color(*plat_c)
                Rectangle(pos=(x, y - cam), size=(w, h))
                Color(min(1, plat_c[0] + 0.2), min(1, plat_c[1] + 0.2), min(1, plat_c[2] + 0.2), 1)
                Rectangle(pos=(x, y + h - 4 - cam), size=(w, 4))

            haz = get_color_from_hex(self.theme["hazard"])
            for (x, y, w, h) in self.hazards:
                if y + h < cam - 15 or y > cam + H + 15:
                    continue
                Color(*haz)
                n = max(2, int(w / 11))
                sw = w / n
                for i in range(n):
                    sx = x + i * sw
                    Triangle(points=[
                        sx, y - cam,
                        sx + sw / 2, y + h - cam,
                        sx + sw, y - cam
                    ])

            if self.goal:
                gx, gy, gw, gh = self.goal
                if gy < cam + H + 30:
                    Color(1, 0.9, 0.3, 1)
                    Rectangle(pos=(gx + gw / 2 - 3, gy - cam), size=(5, gh))
                    Color(1, 0.35, 0.4, 1)
                    Triangle(points=[
                        gx + gw / 2 + 3, gy + gh - cam,
                        gx + gw / 2 + 3, gy + gh - 20 - cam,
                        gx + gw / 2 + 26, gy + gh - 10 - cam
                    ])

            for p in self.particles:
                a = max(0, p.life / p.max_life)
                Color(p.color[0], p.color[1], p.color[2], a)
                Rectangle(pos=(p.x - p.size / 2, p.y - cam - p.size / 2), size=(p.size, p.size))

            if self.alive:
                skin = SKINS.get(self.data.get("selected_skin", "default"), SKINS["default"])
                pc = get_color_from_hex(skin["color"])
                px = self.px
                py = self.py - cam

                Color(pc[0] * 0.65, pc[1] * 0.65, pc[2] * 0.65, 1)
                Rectangle(pos=(px + 3, py), size=(6, 11))
                Rectangle(pos=(px + 11, py), size=(6, 11))
                Color(*pc)
                Rectangle(pos=(px + 2, py + 10), size=(16, 13))
                Color(min(1, pc[0] * 1.1), min(1, pc[1] * 1.1), min(1, pc[2] * 1.1), 1)
                Ellipse(pos=(px + 3, py + 22), size=(14, 14))
                Color(0.1, 0.1, 0.18, 1)
                eye_x = px + 9 if self.facing > 0 else px + 5
                Ellipse(pos=(eye_x, py + 27), size=(3.5, 3.5))


# ===================== GAME SCREEN =====================
class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.level = 1
        self.data = {}
        self.earned = 0

        self.root_layout = FloatLayout()
        self.world = GameWorld(size_hint=(1, 1))
        self.root_layout.add_widget(self.world)

        self.info_label = Label(
            text="Level 1", font_size=sp(16), bold=True, color=(1, 1, 1, 0.95),
            size_hint=(None, None), size=(dp(220), dp(32)),
            pos_hint={"x": 0.03, "top": 0.97}, halign="left"
        )
        self.info_label.bind(size=self.info_label.setter("text_size"))
        self.root_layout.add_widget(self.info_label)

        self.pause_btn = PixelButton(
            text="MENU", bg=(0.55, 0.2, 0.25, 0.9),
            size_hint=(None, None), size=(dp(88), dp(38)),
            pos_hint={"right": 0.97, "top": 0.97}
        )
        self.pause_btn.bind(on_press=self._to_menu)
        self.root_layout.add_widget(self.pause_btn)

        self.win_label = Label(
            text="", font_size=sp(24), bold=True, color=(1, 0.92, 0.35, 1),
            size_hint=(None, None), size=(dp(300), dp(90)),
            pos_hint={"center_x": 0.5, "center_y": 0.58},
            halign="center", opacity=0
        )
        self.win_label.bind(size=self.win_label.setter("text_size"))
        self.root_layout.add_widget(self.win_label)

        self.continue_btn = PixelButton(
            text="CONTINUE", bg=(0.2, 0.7, 0.4, 1),
            size_hint=(None, None), size=(dp(170), dp(50)),
            pos_hint={"center_x": 0.5, "center_y": 0.4},
            opacity=0, disabled=True
        )
        self.continue_btn.bind(on_press=self._after_win)
        self.root_layout.add_widget(self.continue_btn)

        # Control bar
        self.ctrl = BoxLayout(
            orientation="horizontal", size_hint=(1, None), height=dp(76),
            pos_hint={"x": 0, "y": 0}, padding=[dp(10), dp(10)], spacing=dp(10)
        )
        with self.ctrl.canvas.before:
            Color(0.05, 0.04, 0.12, 0.55)
            self.ctrl_bg = Rectangle(pos=self.ctrl.pos, size=self.ctrl.size)
        self.ctrl.bind(pos=lambda *a: setattr(self.ctrl_bg, "pos", self.ctrl.pos),
                       size=lambda *a: setattr(self.ctrl_bg, "size", self.ctrl.size))

        self.btn_left = PixelButton(text="◀", bg=(0.3, 0.28, 0.5, 0.95), size_hint=(0.28, 1))
        self.btn_jump = PixelButton(text="JUMP", bg=(0.3, 0.5, 0.95, 0.95), size_hint=(0.44, 1))
        self.btn_right = PixelButton(text="▶", bg=(0.3, 0.28, 0.5, 0.95), size_hint=(0.28, 1))

        self.btn_left.bind(on_press=lambda x: self._set_move("left", True),
                           on_release=lambda x: self._set_move("left", False))
        self.btn_right.bind(on_press=lambda x: self._set_move("right", True),
                            on_release=lambda x: self._set_move("right", False))
        self.btn_jump.bind(on_press=lambda x: self._do_jump())

        self.ctrl.add_widget(self.btn_left)
        self.ctrl.add_widget(self.btn_jump)
        self.ctrl.add_widget(self.btn_right)
        self.root_layout.add_widget(self.ctrl)

        self.add_widget(self.root_layout)

        Window.bind(on_key_down=self._on_key_down, on_key_up=self._on_key_up)

    def _set_move(self, side, state):
        if side == "left":
            self.world.move_left = state
        else:
            self.world.move_right = state

    def _do_jump(self):
        self.world.jump_pressed = True

    def _on_key_down(self, window, key, scancode, codepoint, modifiers):
        if self.manager.current != "game":
            return
        if key in (276, 97):
            self.world.move_left = True
        elif key in (275, 100):
            self.world.move_right = True
        elif key in (32, 273, 119):
            self.world.jump_pressed = True

    def _on_key_up(self, window, key, scancode):
        if key in (276, 97):
            self.world.move_left = False
        elif key in (275, 100):
            self.world.move_right = False

    def setup_level(self, level, data):
        self.level = level
        self.data = data
        self.earned = 0
        self.win_label.opacity = 0
        self.continue_btn.opacity = 0
        self.continue_btn.disabled = True
        theme = get_level_theme(level)
        self.info_label.text = f"Lv.{level}  {theme['name']}"
        Clock.schedule_once(lambda dt: self.world.start_level(level, data), 0.05)

    def on_leave(self, *args):
        self.world.stop()

    def _to_menu(self, *args):
        self.world.stop()
        self.manager.transition = SlideTransition(direction="down", duration=0.25)
        self.manager.current = "main"

    def _check_win_ui(self, dt):
        if self.world.won and self.win_label.opacity == 0:
            self.earned = getattr(self.world, "earned_cups", 0)
            self.win_label.text = f"LEVEL CLEAR!\n+{self.earned} Cups"
            self.win_label.opacity = 1
            self.continue_btn.opacity = 1
            self.continue_btn.disabled = False
            return False
        return True

    def on_enter(self, *args):
        Clock.schedule_interval(self._check_win_ui, 0.1)

    def _after_win(self, *args):
        self.world.stop()
        self.manager.transition = SlideTransition(direction="down", duration=0.25)
        self.manager.current = "main"


# ===================== APP =====================
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
