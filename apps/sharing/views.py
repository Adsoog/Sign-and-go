from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from apps.documents.models import Document
from apps.documents.storage import get_document_storage
from apps.tracking.models import DocumentEvent
from apps.tracking.services import record_document_event
from .models import ShareLink
from .tokens import create_share_link, resolve_share_link, revoke_share_link


@login_required
def create_link_view(request, doc_id):
    workspace = request.workspace
    document = get_object_or_404(Document, pk=doc_id, workspace=workspace)

    if request.method == "POST":
        expires_days = request.POST.get("expires_days")
        allow_preview = request.POST.get("allow_preview") == "on"
        allow_download = request.POST.get("allow_download") == "on"

        expires_val = int(expires_days) if expires_days and expires_days.isdigit() else None
        link, raw_token = create_share_link(
            document=document,
            created_by=request.user,
            expires_in_days=expires_val,
            allow_preview=allow_preview,
            allow_download=allow_download,
        )
        messages.success(request, f"Enlace público y código QR generados exitosamente.")
        return redirect("documents:detail", pk=document.id)

    return render(request, "sharing/create_link.html", {"doc": document})


@login_required
def link_created_view(request, link_id, raw_token):
    workspace = request.workspace
    link = get_object_or_404(ShareLink, pk=link_id, document__workspace=workspace)
    return render(request, "sharing/link_created.html", {"link": link, "raw_token": raw_token})


@login_required
def revoke_link_view(request, link_id):
    workspace = request.workspace
    link = get_object_or_404(ShareLink, pk=link_id, document__workspace=workspace)
    if request.method == "POST":
        revoke_share_link(link, actor=request.user)
        messages.info(request, "El enlace de verificación ha sido revocado y ya no permitirá el acceso.")
    return redirect("documents:detail", pk=link.document_id)


def public_verify_view(request, token):
    """
    Public verification landing page (/d/<token>).
    Never exposes internal IDs, passwords, private keys, or raw vault data.
    """
    link = resolve_share_link(token)
    if not link:
        return render(request, "sharing/not_found.html", status=404)

    # Check revocation & expiry
    if link.revoked_at:
        return render(request, "sharing/revoked.html", {"link": link}, status=410)

    if link.is_expired:
        return render(request, "sharing/expired.html", {"link": link}, status=410)

    # Record web visit
    record_document_event(
        document=link.document,
        share_link=link,
        event_type=DocumentEvent.EVENT_WEB_VISIT,
        request=request,
    )

    return render(
        request,
        "sharing/public_verify.html",
        {
            "link": link,
            "doc": link.document,
            "token": token,
            "cert": link.document.certificate_profile,
        },
    )


def public_stream_pdf_view(request, token):
    """
    Public PDF stream for inline viewer on verification page.
    """
    link = resolve_share_link(token)
    if not link or not link.is_active or not link.allow_preview:
        return HttpResponseForbidden("Previsualización no permitida o enlace inactivo.")

    doc = link.document
    if not doc.signed_file:
        raise Http404("Documento no disponible.")

    record_document_event(
        document=doc,
        share_link=link,
        event_type=DocumentEvent.EVENT_WEB_PREVIEW,
        request=request,
    )

    storage = get_document_storage()
    file_path = storage.get_signed_absolute_path(doc.signed_file)
    response = FileResponse(open(file_path, "rb"), content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="verified_document.pdf"'
    return response


def public_download_pdf_view(request, token):
    """
    Public download endpoint.
    """
    link = resolve_share_link(token)
    if not link or not link.is_active or not link.allow_download:
        return HttpResponseForbidden("Descarga no permitida o enlace inactivo.")

    doc = link.document
    if not doc.signed_file:
        raise Http404("Documento no disponible.")

    record_document_event(
        document=doc,
        share_link=link,
        event_type=DocumentEvent.EVENT_WEB_DOWNLOAD,
        request=request,
    )

    storage = get_document_storage()
    file_path = storage.get_signed_absolute_path(doc.signed_file)
    filename = f"signed_{doc.original_filename}"
    response = FileResponse(open(file_path, "rb"), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def public_qr_image_view(request, token):
    """
    Serves a PNG QR code for the public verification page.
    """
    from django.http import HttpResponse
    from apps.signing.appearance import generate_qr_image_bytes

    link = resolve_share_link(token)
    if not link:
        raise Http404("Enlace no encontrado.")

    base_url = request.build_absolute_uri("/").rstrip("/")
    target_url = f"{base_url}/d/{token}/"
    qr_bytes = generate_qr_image_bytes(target_url, size=240)
    return HttpResponse(qr_bytes, content_type="image/png")
