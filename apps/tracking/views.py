import base64
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from apps.documents.models import Document
from apps.sharing.tokens import resolve_share_link
from .models import DocumentEvent
from .services import record_document_event

# 1x1 transparent PNG in base64
TRANSPARENT_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)


def pdf_remote_beacon_view(request, token):
    """
    Remote tracking beacon endpoint requested by PDF readers or external clients.
    Records a 'pdf_resource_request' event and returns a 1x1 transparent image.
    """
    link = resolve_share_link(token)
    if link and link.document:
        record_document_event(
            document=link.document,
            share_link=link,
            event_type=DocumentEvent.EVENT_PDF_RESOURCE_REQUEST,
            request=request,
            metadata={"endpoint": "pdf_remote_beacon"},
        )

    response = HttpResponse(TRANSPARENT_PNG_BYTES, content_type="image/png")
    response["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response


@login_required
def document_events_view(request, doc_id):
    """
    Detailed audit and tracking timeline for a document.
    """
    workspace = request.workspace
    document = get_object_or_404(Document, pk=doc_id, workspace=workspace)

    events_qs = document.events.all()

    # Filter by event type
    event_type = request.GET.get("type", "").strip()
    if event_type:
        events_qs = events_qs.filter(event_type=event_type)

    paginator = Paginator(events_qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Calculate summary metrics
    total_visits = document.events.filter(event_type=DocumentEvent.EVENT_WEB_VISIT).count()
    total_previews = document.events.filter(event_type=DocumentEvent.EVENT_WEB_PREVIEW).count()
    total_downloads = document.events.filter(event_type=DocumentEvent.EVENT_WEB_DOWNLOAD).count()
    total_pdf_requests = document.events.filter(event_type=DocumentEvent.EVENT_PDF_RESOURCE_REQUEST).count()

    return render(
        request,
        "documents/events.html",
        {
            "doc": document,
            "events": page_obj,
            "page_obj": page_obj,
            "current_type": event_type,
            "event_type_choices": DocumentEvent.EVENT_TYPE_CHOICES,
            "stats": {
                "visits": total_visits,
                "previews": total_previews,
                "downloads": total_downloads,
                "pdf_requests": total_pdf_requests,
            },
        },
    )
