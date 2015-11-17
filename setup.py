# Credit to Guillaume Piot: http://gpiot.com/blog/creating-a-python-package-and-publish-it-to-pypi/

import os
from distutils.core import setup

VERSION = __import__("django_vcr").__version__

CLASSIFIERS = [
    'Framework :: Django',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Topic :: Software Development',
]

install_requires = [
    'django>=1.8.0',
    'djangorestframework>=3.1.0',
]

# taken from django-registration
# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)

if root_dir:
    os.chdir(root_dir)
for dirpath, dirnames, filenames in os.walk('admin_tools'):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'):
            del dirnames[i]
    if '__init__.py' in filenames:
        pkg = dirpath.replace(os.path.sep, '.')
        if os.path.altsep:
            pkg = pkg.replace(os.path.altsep, '.')
        packages.append(pkg)
    elif filenames:
        prefix = dirpath[12:]  # Strip "django_vcr/" or "django_vcr\"
        for f in filenames:
            data_files.append(os.path.join(prefix, f))

setup(
    name="django-vcr",
    description="A Django-specific implementation of VCR. Ties in with iOS-VCR and Android-VCR.",
    version=VERSION,
    author="Reed Tomlinson",
    author_email="reed.tomlinson@getbellhops.com",
    url="https://github.com/areedtomlinson/django-vcr",
    download_url="git@github.com:areedtomlinson/django-vcr.git",
    package_dir={'django_vcr': 'django_vcr'},
    packages=packages,
    package_data={'django_vcr': data_files},
    include_package_data=True,
    install_requires=install_requires,
    classifiers=CLASSIFIERS,
)
