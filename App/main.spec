# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('controllers', 'controllers'),
        ('database', 'database'),
        ('docs', 'docs'),
        ('models', 'models'),
        ('routers', 'routers'),
        ('utils', 'utils'),
        ('views', 'views'),
    ],
    hiddenimports=[
        'mysql.connector',
        'mysql.connector.locales.eng.client_error',
        'escpos',
        'reportlab',
        'reportlab.lib',               
        'reportlab.lib.colors',        
        'reportlab.lib.pagesizes',     
        'reportlab.lib.units',         
        'reportlab.platypus',          
        'reportlab.pdfgen',
        'openpyxl',
        'win32print',
        'win32api',
        'win32con',
        'qrcode',
        'barcode',
        'PIL'
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

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SenaEmpresa',  # <--- Puedes cambiar aquí el nombre que tendrá el archivo .exe
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,      # <--- False para que sea una app de escritorio sin ventana de consola
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/Logo_Sena.ico',  # <--- Tu icono personalizado
)