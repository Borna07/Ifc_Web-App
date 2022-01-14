from django import forms
from django.forms import widgets
from Ifc2Data.models import Document



class DocumentForm(forms.ModelForm):
    
    class Meta:
        model = Document
        fields = ("document",)


DOWNLOAD_CHOICES = [("all", "All values"), 
    ("all_divide", "All values separated per IfcType"),
    ("unique", "Unique values"), 
    ("unique_divide", "Unique values separated per IfcType")]


FORMAT_CHOICES = [("xlsx", "Excel (.xlsx)"),
    ("csv", "comma-separated values (.csv)")]

class DownloadForm(forms.Form):
    file_format = forms.ChoiceField(choices=FORMAT_CHOICES, widget=forms.RadioSelect())
    file_download = forms.ChoiceField(choices=DOWNLOAD_CHOICES, widget=forms.RadioSelect())