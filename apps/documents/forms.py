from django import forms
from apps.core.validators import validate_pdf_file


class DocumentUploadForm(forms.Form):
    title = forms.CharField(
        label="Título del documento (opcional)",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Contrato de Arrendamiento 2026"}),
    )
    pdf_file = forms.FileField(
        label="Archivo PDF",
        validators=[validate_pdf_file],
        widget=forms.FileInput(attrs={"class": "form-control", "accept": ".pdf"}),
    )
