import io
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from apps.accounts.models import User
from apps.certificates.services import generate_self_signed_certificate
from apps.documents.services import process_uploaded_document
from apps.workspaces.permissions import get_user_workspace


class Command(BaseCommand):
    help = "Seeds demo user, certificate profile, and initial document for testing Sign & Go."

    def handle(self, *args, **options):
        self.stdout.write("Configurando entorno demo...")

        email = "demo@signandgo.es"
        password = "SignBox2026!"
        cert_passphrase = "demopassword"

        user = User.objects.filter(email=email).first()
        if not user:
            user = User.objects.create_superuser(
                email=email,
                password=password,
                full_name="Usuario Demo Sign & Go",
            )
            self.stdout.write(self.style.SUCCESS(f"Usuario demo creado: {email} / {password}"))
        else:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Usuario demo actualizado: {email}"))

        workspace = get_user_workspace(user)
        workspace.name = "Espacio Personal"
        workspace.save()

        # Certificate profile
        if not workspace.certificate_profiles.exists():
            cert = generate_self_signed_certificate(
                workspace=workspace,
                profile_name="Certificado Corporativo Demo",
                common_name="Sign & Go Demo Signer",
                organization="Sign & Go Technologies S.L.",
                country="ES",
                password=cert_passphrase,
                valid_days=365,
            )
            self.stdout.write(self.style.SUCCESS(f"Certificado creado: {cert.name} (Contraseña: '{cert_passphrase}')"))

        # Sample Document
        if not workspace.documents.exists():
            pdf_buf = io.BytesIO()
            c = canvas.Canvas(pdf_buf, pagesize=(595.28, 841.89))  # A4
            
            # Header
            c.setFillColor(HexColor("#0284C7"))
            c.rect(0, 800, 595.28, 41.89, fill=1, stroke=0)
            c.setFillColor(HexColor("#FFFFFF"))
            c.setFont("Helvetica-Bold", 14)
            c.drawString(40, 815, "CONTRATO MARCO DE PRESTACIÓN DE SERVICIOS")

            # Content
            c.setFillColor(HexColor("#0F172A"))
            c.setFont("Helvetica-Bold", 16)
            c.drawString(40, 740, "Acuerdo Comercial de Servicios Tecnológicos 2026")

            c.setFont("Helvetica", 10)
            c.setFillColor(HexColor("#334155"))
            c.drawString(40, 710, "Entre las partes intervinientes, se acuerdan las condiciones para el despliegue del SaaS.")
            c.drawString(40, 690, "El presente documento requiere la firma digital de las partes autorizadas para tener vigencia.")
            c.drawString(40, 670, "Documento de prueba generado automáticamente por el sistema Sign & Go.")

            c.drawString(40, 300, "En prueba de conformidad, se procede a su firma criptográfica en el recuadro inferior:")

            c.showPage()
            c.save()
            pdf_buf.seek(0)

            sample_file = SimpleUploadedFile(
                "Contrato_Servicios_SignAndGo_2026.pdf",
                pdf_buf.getvalue(),
                content_type="application/pdf",
            )
            doc = process_uploaded_document(
                workspace=workspace,
                user=user,
                uploaded_file=sample_file,
                title="Contrato Marco de Servicios 2026",
            )
            self.stdout.write(self.style.SUCCESS(f"Documento de prueba creado: {doc.title}"))

        self.stdout.write(self.style.SUCCESS(
            "\n¡Listo! Puedes iniciar sesión con:\n"
            f"  - Correo: {email} (o el anterior demo@signbox.es)\n"
            f"  - Contraseña de usuario: {password}\n"
            f"  - Contraseña del certificado P12: {cert_passphrase}\n"
        ))
