[app]

# (str) Title of your application
title = HAUSEL

# (str) Package name
package.name = hausel

# (str) Package domain (needed for android/ios packaging)
package.domain = org.lgstudio

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements
requirements = python3,kivy

# (str) Supported orientation (portrait, landscape, sensorLandscape, sensorPortrait...)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Presplash background color (for android toolchain)
android.presplash_color = #0A0A12

# (list) Permissions
android.permissions = VIBRATE

# (int) Target Android API
android.api = 33

# (int) Minimum API
android.minapi = 21

# (str) Android NDK version
android.ndk = 25b

# (bool) If True, skip capturing error messages from stderr
android.skip_update = False

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug)
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1
