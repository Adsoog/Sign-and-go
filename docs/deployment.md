# Guía de Despliegue y Operación en Producción

## 1. Requisitos del Sistema

- **Python:** 3.11 o superior.
- **Base de Datos:** PostgreSQL 15+ (recomendada para producción) o SQLite 3.35+ (para entornos de prueba/desarrollo).
- **Servidor Web:** Gunicorn o Uvicorn detrás de Nginx / Caddy.

## 2. Variables de Entorno

Configurar las siguientes variables en el servidor o gestor de secretos:

```bash
# Django
DJANGO_SECRET_KEY=clave-secreta-larga-y-aleatoria-generada-para-produccion
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=signbox.tudominio.com,www.signbox.tudominio.com

# Base de datos
DATABASE_URL=postgresql://signbox_user:contrasena_fuerte@localhost:5432/signbox_db

# Clave Maestra de Bóveda (Fernet / AES-128-CBC + HMAC-SHA256)
# IMPORTANTE: 32 bytes codificados en Base64. ¡Custodiar fuera del servidor!
SIGNBOX_ENCRYPTION_KEY=tu-clave-fernet-base64-aqui

# Dominio público para Códigos QR y Enlaces
SIGNBOX_BASE_URL=https://signbox.tudominio.com

# Límites de tamaño de archivo (en bytes)
MAX_DOCUMENT_SIZE_BYTES=26214400      # 25 MB
MAX_CERTIFICATE_SIZE_BYTES=10485760    # 10 MB
```

## 3. Instalación Paso a Paso

```bash
# 1. Clonar el repositorio
git clone <url-repositorio> signbox
cd signbox

# 2. Crear y activar entorno virtual
python -m venv venv
source venv/bin/activate  # En Linux/macOS
# venv\Scripts\activate   # En Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
nano .env

# 5. Ejecutar migraciones
python manage.py migrate

# 6. Recopilar archivos estáticos
python manage.py collectstatic --noinput

# 7. Crear superusuario inicial
python manage.py createsuperuser
```

## 4. Configuración del Servidor de Aplicación (Gunicorn + Systemd)

Crear el servicio `/etc/systemd/system/signbox.service`:

```ini
[Unit]
Description=SignBox Gunicorn Daemon
After=network.target

[Service]
User=signbox
Group=www-data
WorkingDirectory=/var/www/signbox
EnvironmentFile=/var/www/signbox/.env
ExecStart=/var/www/signbox/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/var/www/signbox/signbox.sock \
          config.wsgi:application

[Install]
WantedBy=multi-user.target
```

## 5. Configuración del Proxy Inverso (Nginx)

```nginx
server {
    listen 80;
    server_name signbox.tudominio.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name signbox.tudominio.com;

    ssl_certificate /etc/letsencrypt/live/signbox.tudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/signbox.tudominio.com/privkey.pem;

    client_max_body_size 30M;

    location /static/ {
        alias /var/www/signbox/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }

    # IMPORTANTE: NUNCA exponer la carpeta private_storage directamente.
    location /private_storage/ {
        deny all;
        return 404;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/signbox/signbox.sock;
    }
}
```

## 6. Procedimiento de Copia de Seguridad y Restauración

1. **Copia de Base de Datos:**
   ```bash
   pg_dump -U signbox_user -h localhost -d signbox_db -Fc > backup_db_$(date +%F).dump
   ```
2. **Copia de Archivos Privados:**
   ```bash
   tar -czf backup_storage_$(date +%F).tar.gz private_storage/
   ```
3. **Copia de Clave Maestra:**
   Asegurar que la variable `SIGNBOX_ENCRYPTION_KEY` esté respaldada en un almacén seguro e independiente.
4. **Restauración:**
   - Restaurar el volcado PostgreSQL con `pg_restore`.
   - Extraer `private_storage/`.
   - Restablecer la misma variable `SIGNBOX_ENCRYPTION_KEY`.
