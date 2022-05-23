from storages.backends.azure_storage import AzureStorage
from django.conf import settings

class AzureMediaStorage(AzureStorage):
    location = 'media'