# Build a portable Windows executable with all local assets.
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

assets = [(f'static/{name}', 'static') for name in
          ('index.html', 'overlay.html', 'widget.css', 'pixel.ttf', 'pixel-LICENSE.txt', 'velune.png', 'velune.ico', 'wolderfin-logo.svg')]
a = Analysis(['desktop.py'], pathex=[], binaries=[],
             datas=assets + [('LICENSE', '.'), ('THIRD_PARTY_NOTICES.md', '.'), ('licenses', 'licenses')] + collect_data_files('webview'),
             hiddenimports=collect_submodules('winrt') + ['webview.platforms.winforms', 'webview.platforms.edgechromium', 'pystray._win32'],
             hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='Velune',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          version='version_info.txt', icon='static/velune.ico', console=False, disable_windowed_traceback=False)
