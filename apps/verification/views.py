from django.contrib import messages
from django.shortcuts import render
from apps.core.validators import validate_pdf_file
from apps.documents.models import Document
from .services import compare_and_verify_pdf


def compare_tool_view(request):
    """
    Interactive PDF verification and comparison tool.
    Accepts an uploaded PDF and tests cryptographic signatures and hash matches.
    """
    report = None
    user_docs = []

    if request.user.is_authenticated and hasattr(request, "workspace") and request.workspace:
        user_docs = Document.objects.filter(workspace=request.workspace, status=Document.STATUS_SIGNED)

    if request.method == "POST" and request.FILES.get("pdf_file"):
        uploaded_file = request.FILES["pdf_file"]
        ref_doc_id = request.POST.get("reference_doc_id")

        try:
            validate_pdf_file(uploaded_file)
            file_bytes = uploaded_file.read()
            report = compare_and_verify_pdf(
                uploaded_pdf_bytes=file_bytes,
                reference_document_id=ref_doc_id if ref_doc_id else None,
            )
        except Exception as exc:
            messages.error(request, f"Error al procesar el archivo: {str(exc)}")

    return render(
        request,
        "verification/compare.html",
        {
            "report": report,
            "user_docs": user_docs,
        },
    )
