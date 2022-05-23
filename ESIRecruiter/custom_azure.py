from storages.backends.azure_storage import AzureStorage
from django.conf import settings

class AzureMediaStorage(AzureStorage):
    location = 'media'
    file_overwrite = True
    expiration_secs = None