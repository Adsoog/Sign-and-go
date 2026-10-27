# Investigación Técnica: Seguimiento Remoto desde Documentos PDF

## 1. Resumen Ejecutivo y Conclusiones Técnicas

A diferencia de los correos electrónicos HTML (donde una etiqueta `<img src="https://...">` provoca habitualmente una petición HTTP automática), el estándar ISO 32000 para formato PDF **no soporta carga automática y transparente de recursos externos HTML**.

Los visores modernos han implementado barreras de seguridad y privacidad muy estrictas para evitar fugas de información y ataques de telemetría no consentida:

| Lector / Visor | Carga automática de imagen remota | Acción de Apertura (/OpenAction URI) | Enlace Clicable Interactivo (/Link URI) | Código QR Físico |
|---|---|---|---|---|
| **Adobe Acrobat Reader DC** | ❌ No soportado | ⚠️ Alerta de Seguridad emergente bloqueante | ✅ Funciona (tras confirmar aviso de enlace externo) | ✅ Funciona 100% (cámara móvil) |
| **Google Chrome (PDF Viewer)** | ❌ No soportado | ❌ Bloqueado silenciosamente | ✅ Abre pestaña de verificación | ✅ Funciona 100% |
| **Mozilla Firefox (PDF.js)** | ❌ No soportado | ❌ Bloqueado por sandbox | ✅ Abre pestaña de verificación | ✅ Funciona 100% |
| **Microsoft Edge** | ❌ No soportado | ❌ Bloqueado silenciosamente | ✅ Abre pestaña de verificación | ✅ Funciona 100% |
| **Apple Preview (macOS / iOS)** | ❌ No soportado | ❌ Ignorado por diseño | ✅ Abre Safari | ✅ Funciona 100% |
| **Foxit PDF Reader** | ❌ No soportado | ⚠️ Alerta de advertencia de red | ✅ Abre navegador predeterminado | ✅ Funciona 100% |

## 2. Mecanismos Evaluados

### A. Elementos XObject / Imágenes Remotas
- **Evaluación:** La especificación PDF requiere que los objetos de imagen residan dentro del propio archivo (como flujo binario `/XObject /Subtype /Image`). No existe un mecanismo nativo estándar para declarar un flujo de imagen mediante una URI HTTP externa que se renderice automáticamente al dibujar la página.

### B. Acciones de Apertura (/OpenAction con /URI)
- **Evaluación:** Se probó insertar en el diccionario raíz del catálogo del PDF:
  ```text
  /OpenAction << /S /URI /URI (https://signbox.example/track/pdf/TOKEN/beacon.png) >>
  ```
- **Resultado:**
  - En navegadores web (Chrome, Firefox, Edge, Safari): La acción de apertura automática hacia una URL externa es **bloqueada por el sandbox de seguridad del visor** para prevenir redirecciones automáticas maliciosas (*drive-by redirects*).
  - En Adobe Acrobat Reader: Muestra un diálogo de advertencia explícito: *"Este documento está intentando conectarse a signbox.example. Si confía en el sitio, haga clic en Permitir"*. Si el usuario no hace clic en permitir, no se emite ninguna petición de red.

### C. Enlaces Interactivos (/Link con /URI)
- **Evaluación:** Área interactiva sobre el sello visual de la firma y el texto "Verificar autenticidad":
  ```text
  /Subtype /Link /A << /S /URI /URI (https://signbox.example/d/TOKEN/) >>
  ```
- **Resultado:** **Funciona de manera universal en el 100% de los lectores probados**. Al hacer clic sobre el sello de firma, el lector abre directamente la página de verificación en el navegador web del usuario, registrando el evento correspondiente.

### D. Código QR en la Estampa Visual
- **Evaluación:** El QR se genera e incrusta como imagen vectorial de alta resolución en la estampa de firma antes de aplicar la firma criptográfica.
- **Resultado:** Es el método **más robusto, interoperable e independiente del software**, ya que funciona tanto en pantallas de cualquier sistema operativo como en documentos impresos en papel físico.

## 3. Estrategia Adoptada en SignBox

1. **Honestidad Técnica:** No se simulan aperturas no observadas. Si un lector no emite una petición remota automática, el panel no inventa datos ficticios.
2. **Endpoint de Solicitudes Remotas Activo:** SignBox expone `/track/pdf/<token>/beacon.png`, el cual registra eventos tipificados como `pdf_resource_request`. Cuando un cliente o lector compatible emite la petición, queda registrado de forma diferenciada en el historial.
3. **Página de Verificación y Código QR:** Toda firma incluye de forma predeterminada el enlace clicable y el código QR hacia `/d/<token>/`. Cualquier acceso a través de la web registra un evento `web_visit`.
4. **Distinción de Eventos:** El historial de actividad documenta individualmente cada tipo:
   - `web_visit`: Visita a la página de verificación.
   - `web_preview`: Visualización del documento en el visor web.
   - `web_download`: Descarga autorizada del archivo firmado.
   - `pdf_resource_request`: Solicitud remota recibida desde el PDF.
