from django import forms
from apps.core.validators import validate_certificate_file


class CertificateUploadForm(forms.Form):
    name = forms.CharField(
        label="Nombre del perfil",
        max_length=120,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Firma Personal, Representante Legal"}),
    )
    certificate_file = forms.FileField(
        label="Archivo de certificado (.p12 / .pfx)",
        validators=[validate_certificate_file],
        widget=forms.FileInput(attrs={"class": "form-control", "accept": ".p12,.pfx"}),
    )
    password = forms.CharField(
        label="Contraseña del certificado",
        help_text="Se utilizará únicamente para validar el archivo y leer los metadatos. NO se guardará.",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "••••••••"}),
    )


class CertificateGenerateForm(forms.Form):
    name = forms.CharField(
        label="Nombre del perfil",
        initial="Certificado de Pruebas",
        max_length=120,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    common_name = forms.CharField(
        label="Nombre del firmante (Common Name)",
        max_length=120,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Carlos Ruiz"}),
    )
    organization = forms.CharField(
        label="Organización o Empresa",
        initial="SignBox Demo",
        max_length=120,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    country = forms.CharField(
        label="Código de País (2 letras)",
        initial="ES",
        max_length=2,
        widget=forms.TextInput(attrs={"class": "form-control", "maxlength": "2"}),
    )
    password = forms.CharField(
        label="Contraseña del contenedor P12",
        help_text="Recuerda esta contraseña. La necesitarás cada vez que vayas a firmar.",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "••••••••"}),
    )
    valid_days = forms.IntegerField(
        label="Días de validez",
        initial=365,
        min_value=1,
        max_value=3650,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
