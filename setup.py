from setuptools import setup

setup(
    name='factory',
    version='0.1',
    url='http://github.com/liquidinvestigations/factory',
    license='MIT',
    platforms='any',
    modules=['factory'],
    zip_safe=False,
    entry_points={'console_scripts': ['factory = factory:cmd']},
)
