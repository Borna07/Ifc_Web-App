from __future__ import unicode_literals
from collections import namedtuple

from django.db import models

def only_filename(instance, filename):
    return filename

class Document(models.Model):
    # description = models.CharField(max_length=255, blank=True)
    document = models.FileField(upload_to=only_filename)   
    uploaded_at = models.DateTimeField(auto_now_add=True)
    give_name = models.CharField(max_length=200, null=True)
    description = models.CharField(max_length=200, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    organization = models.CharField(max_length=200, null=True)
    author = models.CharField(max_length=200, null=True)
    time_stamp = models.DateTimeField(max_length=200, null=True)
    project_name = models.CharField(max_length=200 , null=True)
    schema_identifiers = models.CharField(max_length=200, null=True)
    software = models.CharField(max_length=200, null=True)

    def __str__(self):
        return self.document.name