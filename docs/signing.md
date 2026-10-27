# Motor de Firma Criptográfica y Validación PAdES

## 1. Principio Criptográfico

SignBox implementa firmas digitales basadas en el estándar internacional **PAdES (PDF Advanced Electronic Signatures)** mediante la biblioteca especializada **pyHanko** y la suite criptográfica de Python.

> [!IMPORTANT]
> **Diferencia entre Apariencia Visual y Firma Criptográfica:**
> Una estampa visual o imagen colocada en el PDF **no constituye una firma legal ni criptográfica**. La firma real es una estructura binaria CMS/PKCS#7 embebida en el diccionario del documento que cifra el resumen digital (hash SHA-256) del contenido mediante la clave privada del firmante.

## 2. Flujo de Preparación e Inmutabilidad

Para garantizar que el archivo resultante no sea invalidado posteriormente:

1. **Preparación Pre-Firma:** Todos los elementos visibles (recuadro de firma, datos del firmante, QR de verificación y enlaces clicables) se combinan en la página seleccionada **antes** de aplicar la firma criptográfica.
2. **Firma Criptográfica:** pyHanko genera la firma digital utilizando el flujo `IncrementalPdfFileWriter`, asegurando que el rango de bytes (`/ByteRange`) cubra íntegramente el archivo.
3. **Cálculo SHA-256:** Inmediatamente tras firmar, se calcula la huella SHA-256 del documento final firmado.
4. **Inmutabilidad Absoluta:** Tras la firma, **no se permite** insertar marcas de agua, combinar páginas ni modificar metadatos que alteren el archivo firmado. Cualquier cambio posterior alteraría el hash y rompería la integridad criptográfica.

## 3. Niveles de Validación

Al verificar una firma, SignBox evalúa y reporta con honestidad técnica tres aspectos independientes:

1. **Integridad del Documento (`intact`):**
   - Comprueba que los bytes cubiertos por el `ByteRange` no hayan sufrido modificaciones desde que se aplicó la firma.
   - Si un solo carácter o píxel cambia, la integridad se declara rota.

2. **Validez Matemática (`valid`):**
   - Comprueba que la firma fue matemáticamente calculada por la clave privada correspondiente al certificado público adjunto.

3. **Confianza de la Cadena (`trusted`):**
   - Determina si el certificado proviene de una Autoridad de Certificación (CA) de confianza pública reconocida por el sistema operativo, o si es un certificado autofirmado / de prueba.
   - *Nota legal:* Una firma matemáticamente válida producida con un certificado autofirmado es técnicamente íntegra, pero no sustituye un certificado cualificado eIDAS para fines legales públicos. SignBox reporta esta distinción con total transparencia.
