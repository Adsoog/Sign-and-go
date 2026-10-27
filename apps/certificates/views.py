from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from apps.audit.services import log_audit_event
from .forms import CertificateGenerateForm, CertificateUploadForm
from .models import CertificateProfile
from .services import generate_self_signed_certificate, save_certificate_profile


@login_required
def certificate_list_view(request):
    workspace = request.workspace
    certificates = CertificateProfile.objects.filter(workspace=workspace)
    return render(request, "certificates/list.html", {"certificates": certificates})


@login_required
def certificate_upload_view(request):
    workspace = request.workspace

    if request.method == "POST":
        form = CertificateUploadForm(request.POST, request.FILES)
        if form.is_valid():
            p12_file = request.FILES["certificate_file"]
            password = form.cleaned_data["password"]
            name = form.cleaned_data["name"]

            try:
                p12_bytes = p12_file.read()
                profile = save_certificate_profile(
                    workspace=workspace,
                    name=name,
                    p12_bytes=p12_bytes,
                    password=password,
                )
                log_audit_event(
                    workspace=workspace,
                    actor=request.user,
                    action="certificate_created",
                    target_type="CertificateProfile",
                    target_id=str(profile.id),
                    metadata={"name": profile.name, "subject": profile.subject_name},
                )
                messages.success(request, f"Certificado '{profile.name}' añadido y cifrado con éxito en la bóveda.")
                return redirect("certificates:list")
            except Exception as e:
                messages.error(request, f"Error al procesar el certificado: {str(e)}")
    else:
        form = CertificateUploadForm()

    return render(request, "certificates/upload.html", {"form": form})


@login_required
def certificate_generate_view(request):
    workspace = request.workspace

    if request.method == "POST":
        form = CertificateGenerateForm(request.POST)
        if form.is_valid():
            try:
                profile = generate_self_signed_certificate(
                    workspace=workspace,
                    profile_name=form.cleaned_data["name"],
                    common_name=form.cleaned_data["common_name"],
                    organization=form.cleaned_data["organization"],
                    country=form.cleaned_data["country"],
                    password=form.cleaned_data["password"],
                    valid_days=form.cleaned_data["valid_days"],
                )
                log_audit_event(
                    workspace=workspace,
                    actor=request.user,
                    action="certificate_generated_test",
                    target_type="CertificateProfile",
                    target_id=str(profile.id),
                    metadata={"name": profile.name, "subject": profile.subject_name},
                )
                messages.success(request, f"Certificado de prueba '{profile.name}' generado y cifrado exitosamente.")
                return redirect("certificates:list")
            except Exception as e:
                messages.error(request, f"Error al generar certificado: {str(e)}")
    else:
        form = CertificateGenerateForm()

    return render(request, "certificates/generate.html", {"form": form})


@login_required
def certificate_detail_view(request, pk):
    workspace = request.workspace
    cert = get_object_or_404(CertificateProfile, pk=pk, workspace=workspace)
    return render(request, "certificates/detail.html", {"cert": cert})


@login_required
def certificate_toggle_view(request, pk):
    workspace = request.workspace
    cert = get_object_or_404(CertificateProfile, pk=pk, workspace=workspace)
    if request.method == "POST":
        cert.is_active = not cert.is_active
        cert.save()
        status_str = "activado" if cert.is_active else "desactivado"
        messages.info(request, f"Certificado '{cert.name}' {status_str}.")
    return redirect("certificates:list")


@login_required
def certificate_delete_view(request, pk):
    workspace = request.workspace
    cert = get_object_or_404(CertificateProfile, pk=pk, workspace=workspace)
    if request.method == "POST":
        cert_name = cert.name
        cert_id = str(cert.id)
        # Note: can delete file or retain for audit
        cert.delete()
        log_audit_event(
            workspace=workspace,
            actor=request.user,
            action="certificate_deleted",
            target_type="CertificateProfile",
            target_id=cert_id,
            metadata={"name": cert_name},
        )
        messages.success(request, f"Certificado '{cert_name}' eliminado de la bóveda.")
        return redirect("certificates:list")
    return render(request, "certificates/delete_confirm.html", {"cert": cert})
