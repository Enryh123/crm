# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []

# 收集 selenium 相关的所有依赖
selenium_ret = collect_all('selenium')
datas += selenium_ret[0]; binaries += selenium_ret[1]; hiddenimports += selenium_ret[2]

# 收集 webdriver_manager 相关的所有依赖
webdriver_ret = collect_all('webdriver_manager')
datas += webdriver_ret[0]; binaries += webdriver_ret[1]; hiddenimports += webdriver_ret[2]

block_cipher = None

a = Analysis(
    ['main.py'],  # 你的主程序文件名
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports + [
        'selenium',
        'selenium.webdriver',
        'selenium.webdriver.edge.service',
        'selenium.webdriver.edge.options',
        'selenium.webdriver.edge.webdriver',
        'selenium.webdriver.common.by',
        'selenium.webdriver.common.keys',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',
        'webdriver_manager',
        'webdriver_manager.microsoft',
        'PyQt5',
        'PyQt5.sip',
        'requests',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='班级学生信息系统',  # 生成的exe文件名
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # True以显示控制台窗口，方便查看错误信息
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='app.ico',  # 如果有图标，取消注释这行
)