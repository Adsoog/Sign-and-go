from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from apps.audit.services import log_audit_event
from .forms import DocumentUploadForm
from .models import Document
from .services import process_uploaded_document
from .storage import get_document_storage


@login_required
def document_list_view(request):
    workspace = request.workspace
    queryset = Document.objects.filter(workspace=workspace)

    # Search filter
    q = request.GET.get("q", "").strip()
    if q:
        queryset = queryset.filter(title__icontains=q)

    # Status filter
    status = request.GET.get("status", "").strip()
    if status in dict(Document.STATUS_CHOICES):
        queryset = queryset.filter(status=status)

    # Pagination
    paginator = Paginator(queryset, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "documents/list.html",
        {
            "documents": page_obj,
            "page_obj": page_obj,
            "q": q,
            "status": status,
            "status_choices": Document.STATUS_CHOICES,
        },
    )


@login_required
def document_upload_view(request):
    workspace = request.workspace

    if request.method == "POST":
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                doc = process_uploaded_document(
                    workspace=workspace,
                    user=request.user,
                    uploaded_file=request.FILES["pdf_file"],
                    title=form.cleaned_data.get("title"),
                )
                messages.success(request, f"Documento '{doc.title}' subido con éxito. Puedes proceder a firmarlo.")
                return redirect("signing:editor", doc_id=doc.id)
            except Exception as e:
                messages.error(request, f"Error al procesar el archivo: {str(e)}")
    else:
        form = DocumentUploadForm()

    return render(request, "documents/upload.html", {"form": form})


@login_required
def document_detail_view(request, pk):
    workspace = request.workspace
    doc = get_object_or_404(Document, pk=pk, workspace=workspace)
    # Single active public verification link (one link per document)
    active_share_link = doc.share_links.filter(revoked_at__isnull=True).order_by("-created_at").first()

    # Metrics
    total_views = doc.events.filter(event_type__in=["web_visit", "web_preview"]).count()
    total_downloads = doc.events.filter(event_type="web_download").count()

    # Deduplicate consecutive visit/preview events
    raw_events = list(doc.events.all().order_by("-occurred_at")[:20])
    clean_events = []
    seen = set()
    for ev in raw_events:
        min_key = (ev.event_type, ev.occurred_at.strftime("%Y-%m-%d %H:%M"))
        if min_key not in seen:
            seen.add(min_key)
            clean_events.append(ev)

    return render(
        request,
        "documents/detail.html",
        {
            "doc": doc,
            "active_share_link": active_share_link,
            "recent_events": clean_events[:6],
            "total_views": total_views,
            "total_downloads": total_downloads,
        },
    )


@login_required
def document_download_view(request, pk, file_type):
    """
    Authorized streaming download for private documents.
    file_type: 'source' or 'signed'
    """
    workspace = request.workspace
    doc = get_object_or_404(Document, pk=pk, workspace=workspace)
    storage = get_document_storage()

    if file_type == "signed":
        if not doc.signed_file:
            raise Http404("El documento no tiene versión firmada.")
        file_path = storage.get_signed_absolute_path(doc.signed_file)
        filename = f"signed_{doc.original_filename}"
    else:
        file_path = storage.get_source_absolute_path(doc.source_file)
        filename = doc.original_filename

    if not file_path.exists():
        raise Http404("El archivo no existe en el almacenamiento.")

    log_audit_event(
        workspace=workspace,
        actor=request.user,
        action=f"document_download_{file_type}",
        target_type="Document",
        target_id=str(doc.id),
        metadata={"filename": filename},
    )

    response = FileResponse(open(file_path, "rb"), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
def document_view_file(request, pk, file_type):
    """
    Authorized inline stream for PDF.js viewer.
    """
    workspace = request.workspace
    doc = get_object_or_404(Document, pk=pk, workspace=workspace)
    storage = get_document_storage()

    if file_type == "signed":
        if not doc.signed_file:
            raise Http404("El documento no está firmado.")
        file_path = storage.get_signed_absolute_path(doc.signed_file)
    else:
        file_path = storage.get_source_absolute_path(doc.source_file)

    if not file_path.exists():
        raise Http404("El archivo solicitado no existe.")

    response = FileResponse(open(file_path, "rb"), content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="preview.pdf"'
    return response


@login_required
def document_delete_view(request, pk):
    workspace = request.workspace
    doc = get_object_or_404(Document, pk=pk, workspace=workspace)

    if request.method == "POST":
        title = doc.title
        doc_id = str(doc.id)
        doc.delete()
        log_audit_event(
            workspace=workspace,
            actor=request.user,
            action="document_deleted",
            target_type="Document",
            target_id=doc_id,
            metadata={"title": title},
        )
        messages.success(request, f"Documento '{title}' eliminado.")
        return redirect("documents:list")

    return render(request, "documents/delete_confirm.html", {"doc": doc})
