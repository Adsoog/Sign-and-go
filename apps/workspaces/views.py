from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from apps.certificates.models import CertificateProfile
from apps.documents.models import Document
from apps.tracking.models import DocumentEvent


@login_required
def dashboard_view(request):
    workspace = request.workspace

    total_docs = Document.objects.filter(workspace=workspace).count()
    signed_docs = Document.objects.filter(workspace=workspace, status=Document.STATUS_SIGNED).count()
    pending_docs = Document.objects.filter(workspace=workspace, status=Document.STATUS_UPLOADED).count()
    active_certs = CertificateProfile.objects.filter(workspace=workspace, is_active=True).count()

    recent_documents = Document.objects.filter(workspace=workspace).order_by("-created_at")[:5]
    recent_events = DocumentEvent.objects.filter(document__workspace=workspace).order_by("-occurred_at")[:8]

    return render(
        request,
        "dashboard/home.html",
        {
            "total_docs": total_docs,
            "signed_docs": signed_docs,
            "pending_docs": pending_docs,
            "active_certs": active_certs,
            "recent_documents": recent_documents,
            "recent_events": recent_events,
        },
    )
