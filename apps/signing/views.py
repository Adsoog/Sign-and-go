import json
import uuid
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from apps.certificates.models import CertificateProfile
from apps.documents.models import Document
from .models import SigningOperation
from .services import execute_document_signature


@login_required
def signing_editor_view(request, doc_id):
    workspace = request.workspace
    document = get_object_or_404(Document, pk=doc_id, workspace=workspace)
    certificates = CertificateProfile.objects.filter(workspace=workspace, is_active=True)
    idempotency_key = uuid.uuid4().hex

    return render(
        request,
        "signing/editor.html",
        {
            "doc": document,
            "certificates": certificates,
            "idempotency_key": idempotency_key,
        },
    )


@login_required
def signing_execute_view(request, doc_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Método no permitido."}, status=405)

    workspace = request.workspace
    document = get_object_or_404(Document, pk=doc_id, workspace=workspace)

    # Support JSON or POST form data
    if request.content_type == "application/json":
        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({"success": False, "error": "JSON inválido."}, status=400)
    else:
        data = request.POST

    cert_id = data.get("certificate_id")
    passphrase = data.get("passphrase")
    page_number = int(data.get("page_number", 1))
    norm_x = float(data.get("x", 0.1))
    norm_y = float(data.get("y", 0.75))
    norm_w = float(data.get("width", 0.4))
    norm_h = float(data.get("height", 0.15))
    reason = data.get("reason", "Firmado electrónicamente con Sign & Go")
    location = data.get("location", "Sign & Go Vault")
    idempotency_key = data.get("idempotency_key") or uuid.uuid4().hex

    if not cert_id:
        return JsonResponse({"success": False, "error": "Debe seleccionar un certificado."}, status=400)

    if not passphrase:
        return JsonResponse({"success": False, "error": "Debe introducir la contraseña del certificado."}, status=400)

    certificate = get_object_or_404(CertificateProfile, pk=cert_id, workspace=workspace)

    try:
        result = execute_document_signature(
            document=document,
            certificate_profile=certificate,
            passphrase=passphrase,
            page_number=page_number,
            norm_x=norm_x,
            norm_y=norm_y,
            norm_w=norm_w,
            norm_h=norm_h,
            reason=reason,
            location=location,
            idempotency_key=idempotency_key,
            user=request.user,
        )
        return JsonResponse(result)
    except Exception as exc:
        return JsonResponse({
            "success": False,
            "error": str(exc),
            "error_type": type(exc).__name__,
        }, status=400)


@login_required
def signing_history_view(request, doc_id):
    workspace = request.workspace
    document = get_object_or_404(Document, pk=doc_id, workspace=workspace)
    operations = document.signing_operations.all().order_by("-started_at")
    return render(
        request,
        "signing/history.html",
        {
            "doc": document,
            "operations": operations,
        },
    )
