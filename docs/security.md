# Modelo de Seguridad y Protección de Datos en SignBox

## 1. Bóveda de Certificados y Cifrado en Reposo

La protección de los archivos PKCS#12 (.p12 / .pfx) que contienen claves privadas es crítica en SignBox.

1. **Cifrado Autenticado:** Los archivos binarios de certificados se cifran con Fernet (AES-128-CBC autenticado mediante HMAC-SHA256) antes de ser guardados en el almacenamiento privado en disco (`private_storage/certificates/<uuid>.enc`).
2. **Separación de la Clave Maestra:** La clave de cifrado (`SIGNBOX_ENCRYPTION_KEY`) se almacena en variables de entorno, **nunca** en la base de datos ni en el repositorio git.
3. **Contraseña Efímera en Memoria:**
   - La contraseña del contenedor P12 **jamás se guarda** en la base de datos ni en los registros.
   - Solo se solicita al usuario en el momento exacto de firmar y se destruye en memoria una vez completada la invocación del motor criptográfico.
4. **Procedimiento de Recuperación de Clave:**
   - Si la clave `SIGNBOX_ENCRYPTION_KEY` se pierde, los certificados almacenados no podrán ser descifrados.
   - En entornos de producción, la clave debe custodiarse en un gestor de secretos (AWS Secrets Manager, HashiCorp Vault, Azure Key Vault o Google Secret Manager).

## 2. Aislamiento Multitenant (Workspaces)

- Cada usuario dispone de su propio espacio de trabajo privado (`Workspace`).
- Todas las consultas de listado, detalle y descarga filtran obligatoriamente por `workspace=request.workspace`.
- El middleware `WorkspaceMiddleware` garantiza que las vistas autenticadas operen únicamente sobre el tenant legítimo.
- Intentos de manipulación de identificadores UUID en URLs devuelven respuestas `404 Not Found` en lugar de fugas de metadatos.

## 3. Enlaces Públicos y Tokens Seguros

- Los enlaces de verificación (`/d/<token>/`) utilizan tokens aleatorios de 32 bytes con codificación URL-safe (entropía criptográfica mediante `secrets.token_urlsafe`).
- En la base de datos **solo se almacena el hash SHA-256 del token** (`token_hash`). Si la base de datos fuese comprometida, los atacantes no obtendrán tokens válidos en texto plano.
- Los enlaces pueden configurarse con caducidad temporal (`expires_at`) o revocación inmediata (`revoked_at`).

## 4. Privacidad y Anonimización de Registros (RGPD)

- Las direcciones IP de visitas web y solicitudes de recursos se anonimizan automáticamente antes de persistirse:
  - IPv4: Se enmascara el último octeto (ejemplo: `192.168.1.0`).
  - IPv6: Se conservan únicamente los primeros 48 bits.
- El User-Agent se recorta y sanea para evitar inyecciones de encabezados o almacenamiento innecesario de huellas digitales intrusivas.

## 5. Prevención de Ataques Web

- **CSRF:** Protección activa en todos los formularios mediante tokens CSRF de Django.
- **XSS & Clickjacking:** Cabeceras HTTP `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN` y `Referrer-Policy: strict-origin-when-cross-origin`.
- **Validación de Archivos:** Validación de tamaño máximo (25MB para documentos, 10MB para certificados) e inspección de encabezados binarios (`%PDF-` para PDF y estructuras ASN.1/PKCS#12 para certificados).
