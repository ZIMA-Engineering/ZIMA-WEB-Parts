#!/usr/bin/env python
from setuptools import find_packages, setup


setup(
    name='django-zwp',
    version='0.1.0',
    description='Django app for browsing data directories used by ZIMA-CAD-Parts.',
    url='https://github.com/ZIMA-Engineering/ZIMA-WEB-Parts',
    author='Jakub Skokan',
    author_email='aither@havefun.cz',
    license='GPL',
    packages=find_packages(),
    package_data={
        'zwp': [
            'static/zwp/css/jstree/*.css',
            'static/zwp/css/jstree/*.png',
            'static/zwp/css/jstree/*.gif',
            'static/zwp/js/*.js',
            'templates/zwp/*.html',
        ],
    },
    install_requires=[
        'Django>=3.0',
        'django-formtools>=1.0',
        'django-form-utils>=1.0',
        'easy-thumbnails>=2.7',
        'python-pam',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.11',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
