# Сторонние компоненты

Лицензия Velune относится только к собственному коду и материалам WolderFin.
Права на перечисленные компоненты сохраняются за их авторами. Полные тексты
лицензий включены в `licenses/third-party/` и распространяются вместе со сборкой.

| Компонент | Версия сборки | Лицензия / файл |
| --- | --- | --- |
| Python | 3.14.7 | PSF и исторические уведомления: `Python-LICENSE.txt` |
| PyWinRT (runtime, Foundation, Collections, Media.Control, Storage.Streams) | 3.2.1 | MIT: `PyWinRT-MIT.txt` |
| pywebview | 6.2.1 | BSD: `pywebview/LICENSE` |
| pythonnet | 3.1.0 | MIT: `pythonnet/LICENSE` |
| clr_loader | 0.3.1 | MIT: `clr_loader/LICENSE` |
| cffi | 2.1.1 | MIT: `cffi/LICENSE` |
| pycparser | 3.0 | BSD: `pycparser/LICENSE` |
| bottle | 0.13.4 | MIT: `bottle/LICENSE` |
| proxy_tools | 0.1.0 | MIT: `proxy_tools-MIT.txt` |
| typing_extensions | 4.16.0 | PSF: `typing_extensions/LICENSE` |
| pystray | 0.19.5 | LGPL-3.0: `pystray/COPYING` и `pystray/COPYING.LGPL` |
| Pillow и встроенные библиотеки изображений | 12.3.0 | HPND и дополнительные лицензии: `pillow/LICENSE` |
| six | 1.17.0 | MIT: `six/LICENSE` |
| PyInstaller bootloader | 6.22.3 | GPL с исключением для распространяемых приложений: `pyinstaller/COPYING.txt` |
| Press Start 2P | bundled | SIL OFL 1.1: `PressStart2P-OFL.txt`, также `static/pixel-LICENSE.txt` |

## pystray / LGPL

Velune использует неизменённую pystray 0.19.5. Соответствующие исходники
включены в `licenses/third-party/sources/pystray-0.19.5.tar.gz` из официального
[репозитория pystray](https://github.com/moses-palmer/pystray/tree/v0.19.5).
Вы вправе изменять библиотеку и собирать Velune из исходников с её заменой:
создайте окружение, установите зависимости, установите изменённую библиотеку
вместо pystray и выполните `build.ps1`. Ограничения лицензии Velune не применяются
к самой pystray и не отменяют предоставленные LGPL права.

## Внешние компоненты

Microsoft Edge WebView2 Runtime не включён в архив и устанавливается отдельно
по условиям Microsoft. Музыка и обложки поступают от медиаприложений пользователя;
Velune не включает музыкальный контент и не предоставляет на него прав.
