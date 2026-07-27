[app]

title = HAUSEL
package.name = hausel
package.domain = org.lgstudio

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

version = 0.1

requirements = python3,kivy

orientation = portrait
fullscreen = 0

android.presplash_color = #0A0A12
android.permissions = VIBRATE

# Важно — автоматически принимает лицензии
android.accept_sdk_license = True

android.api = 33
android.minapi = 21
android.ndk = 25b

[buildozer]
log_level = 2
warn_on_root = 1
