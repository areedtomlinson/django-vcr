## OUTDATED: This package is maintained [here](https://github.com/bellhops/DjangoVCR)

# django-vcr
A Django-specific implementation of VCR. Ties in with iOS-VCR and Android-VCR.

## Installation:
Add this to your MIDDLEWARE_CLASSES:
```
'django_vcr.middleware.VCRMiddleware',
```

And add this to your INSTALLED_APPS:
```
'django_vcr'
```

In settings, add the following keys:
```python
VCR_CASSETTE_PATH  # full path to the directory where tapes will be stored
VCR_STATE  # "recording", "replaying" or "stopped"
```

## Implementation
```
from django_vcr.middleware import VCRMiddleware

VCRMiddleware.start("cassetteFileName", "replaying")
```
