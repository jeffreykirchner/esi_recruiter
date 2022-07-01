from storages.backends.azure_storage import AzureStorage
from django.conf import settings

class AzureMediaStorage(AzureStorage):
    location = 'media'
    #custom_domain = 'chapman-esi-cdn.azureedge.net'

class AzureStaticStorage(AzureStorage):
    location = 'static'
    #custom_domain = 'chapman-esi-cdn.azureedge.net'