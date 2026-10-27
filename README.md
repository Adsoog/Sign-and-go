# Sign & Go — SaaS de Firma Digital, Gestión Documental y Seguimiento de PDF

Sign & Go es una plataforma SaaS moderna, elegante y segura para la custodia de certificados digitales, la firma criptográfica de documentos PDF según el estándar PAdES, el seguimiento de eventos y la verificación de integridad documental.

Diseñado como un monolito robusto en **Django 5.2**, sin dependencias complejas innecesarias (sin React, sin microservicios, sin Celery ni Redis en el MVP).

---

## Características Principales

1. **Bóveda Criptográfica de Certificados:**
   - Soporte para contenedores PKCS#12 (.p12 / .pfx).
   - Cifrado simétrico autenticado (Fernet / AES-128-CBC + HMAC-SHA256) en reposo.
   - Clave maestra fuera del repositorio y de la base de datos.
   - La contraseña del certificado se solicita únicamente en el momento de la firma y **nunca se almacena**.
   - Generador integrado de certificados de prueba RSA de 2048 bits para pruebas inmediatas en 1 clic.

2. **Editor Visual y Firma Criptográfica:**
   - Visor integrado con **PDF.js** y selector de páginas/zoom.
   - Recuadro de firma arrastrable y redimensionable con **Alpine.js**.
   - Conversión matemática precisa entre coordenadas del navegador y puntos reales del PDF (MediaBox).
   - Generación de estampa visual profesional con datos del firmante, QR de verificación y enlace interactivo.
   - Firma criptográfica PAdES real con **pyHanko**.
   - Inmutabilidad estricta: cálculo y persistencia del hash SHA-256 del documento final.

3. **Repositorio Documental Privado:**
   - Aislamiento estricto por usuario y espacio de trabajo (`Workspace`).
   - Búsqueda por título, filtros por estado y paginación.
   - Almacenamiento desacoplado fuera de rutas públicas (`private_storage/`).
   - Descargas autorizadas y streaming protegido.

4. **Enlaces Públicos y Códigos QR:**
   - Generación de tokens aleatorios criptográficamente seguros.
   - Almacenamiento exclusivo del hash SHA-256 del token en base de datos.
   - Control de permisos (previsualización web, descarga permitida).
   - Soporte para caducidad temporal y revocación inmediata.

5. **Seguimiento de Eventos:**
   - Registro de visitas web, previsualizaciones en visor, descargas y solicitudes remotas.
   - Anonimización de direcciones IP para cumplimiento de privacidad (RGPD).
   - Endpoint de baliza de seguimiento para lectores compatibles (`/track/pdf/<token>/beacon.png`).
   - Panel de actividad con métricas y filtros cronológicos.

6. **Verificación y Comparación de Documentos:**
   - Carga de cualquier PDF para análisis de autenticidad.
   - Distingue claramente:
     - Coincidencia exacta byte a byte con el documento archivado.
     - Firma criptográfica válida (incluso si el archivo es diferente o modificado de forma permitida).
     - Archivo alterado o firma inválida.
     - Documentos sin firma.

---

## Stack Tecnológico

| Capa | Tecnología |
|---|---|
| **Backend** | Python 3.11+ / Django 5.2 LTS |
| **Interfaz** | Django Templates, Bootstrap 5.3, Bootstrap Icons |
| **Interactividad** | Alpine.js 3.x |
| **Visor PDF** | PDF.js |
| **Criptografía de Firma** | pyHanko y pyhanko-certvalidator |
| **Cifrado en Reposo** | cryptography (Fernet AES-CBC + HMAC-SHA256) |
| **Manipulación de PDF** | pypdf y ReportLab |
| **Códigos QR** | qrcode (PIL / Pillow) |
| **Base de Datos** | SQLite (desarrollo rápido) / PostgreSQL (producción) |
| **Pruebas** | pytest y pytest-django |

---

## Estructura del Proyecto

```text
signbox/
├── manage.py
├── pyproject.toml
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── config/
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── settings/
│       ├── base.py
│       ├── development.py
│       └── production.py
│
├── apps/
│   ├── accounts/       # Modelo de Usuario personalizado y autenticación
│   ├── workspaces/     # Aislamiento multitenant y dashboard
│   ├── certificates/   # Bóveda cifrada y generador PKCS#12
│   ├── documents/      # Repositorio documental y almacenamiento desacoplado
│   ├── signing/        # Motor pyHanko, coordenadas y apariencia visual
│   ├── sharing/        # Enlaces públicos de verificación y tokens con hash
│   ├── tracking/       # Eventos de visita, descarga y baliza remota
│   ├── verification/   # Comparador y validador de integridad de PDF
│   ├── audit/          # Registro de auditoría de seguridad
│   └── core/           # Middlewares, utilidades SHA-256 y validadores
│
├── templates/          # Plantillas HTML ordenadas por módulo
├── static/             # CSS moderno (signbox.css), JavaScript y recursos
├── tests/              # Pruebas automatizadas de aislamiento, firma y verificación
└── docs/               # Documentación de arquitectura, seguridad y seguimiento
```

---

## Puesta en Marcha Local

### 1. Requisitos Previos

Tener instalado Python 3.11 o superior.

### 2. Instalación de Dependencias

```bash
pip install -r requirements.txt
```

### 3. Configuración de Entorno

Copiar el archivo de configuración de ejemplo:

```bash
cp .env.example .env
```

El archivo `.env` ya incluye una clave de cifrado generada para desarrollo local y configuración predeterminada con SQLite.

### 4. Migraciones de Base de Datos

```bash
python manage.py migrate
```

### 5. Ejecutar la Aplicación

```bash
python manage.py runserver
```

Abre tu navegador en `http://localhost:8000`.

---

## Ejecución de Pruebas Automatizadas

La suite de pruebas comprueba el aislamiento de datos entre espacios de trabajo, el cifrado de la bóveda, la firma criptográfica real con pyHanko y la detección de documentos alterados:

```bash
pytest
```

---

## Documentación Adicional

- [Arquitectura del Sistema](docs/architecture.md)
- [Modelo de Seguridad y Cifrado](docs/security.md)
- [Motor de Firma Criptográfica y PAdES](docs/signing.md)
- [Investigación de Seguimiento Remoto desde PDF](docs/tracking.md)
- [Guía de Despliegue en Producción](docs/deployment.md)
