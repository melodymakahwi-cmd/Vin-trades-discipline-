[app]
title = Vin Trades
package.name = vintrades
package.domain = org.vin

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0

requirements = python3,kivy

orientation = portrait
fullscreen = 0

android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.build_tools_version = 34.0.0

[buildozer]
log_level = 2
