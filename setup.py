from setuptools import setup

setup(
    name='irgui',
    version='0.1',
    packages=[
        'src',
        'src.backend',
        'src.external',
        'src.external.qtwaitingspinner',
        'src.manager',
        'src.ui',
        'src.ui.canvas',
        'src.ui.misc',
        'src.ui.sidebar',
        'src.ui.toolbar',
        'src.util'
    ],
    package_data={
        'src': [
            'icons/*'
        ]
    },
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'irgui=src.main:main'
        ]
    }
)
