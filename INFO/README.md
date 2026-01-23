# VainillaGA - Gestor de Lectura de Manga

> Un lector de manga personalizado con API RESTful desarrollado con FastAPI


## Características Principales

- **Autenticación JWT** con soporte para usuarios
- **Gestión completa** de mangas, capítulos y páginas
- **Sistema de comentarios** y valoraciones
- **Búsqueda avanzada** con filtros
- **Subida de archivos** para portadas y capítulos
- **API RESTful** documentada con OpenAPI/Swagger
- **Docker Compose** para despliegue simplificado
- **Nginx** como proxy inverso
- **Base de datos SQLite** para desarrollo, (en el futuro se puede cambiar a postgresql)


## Requisitos previos

- Python 3.8+
- pip (gestor de paquetes de Python)
- Docker y Docker Compose (recomendado)
- Nginx (ya incluido en Docker Compose)

## Instalación con Docker (Recomendado)

1. Clona el repositorio:
   ```bash
   git clone x
   cd vanillaga
   ```

2. Configura las variables de entorno:
   ```bash
   cp .env.example .env
   # Edita el archivo .env según sea necesario
   ```

3. Construye y levanta los contenedores:
   ```bash
   docker-compose up --build -d
   ```

4. La aplicación estará disponible en:
   - API: http://localhost:8001
   - Documentación Swagger: http://localhost:8001/docs
   - Interfaz web: http://localhost

## Instalación Manual

1. Crea y activa un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: .\venv\Scripts\activate
   ```

2. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Inicializa la base de datos:
   ```bash
   python -m app.db.init_db
   ```

4. Ejecuta la aplicación:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8001 --reload
   ```

## Variables de Entorno

Crea un archivo `.env` con las siguientes variables:

```env
# Configuración de la aplicación
APP_NAME=VanillaGA
APP_ENV=development
DEBUG=True
SECRET_KEY=tu_clave_secreta_aqui

# Base de datos
DATABASE_URL=sqlite:///./app/db/vanillaga.db

# CORS
CORS_ORIGINS=["http://localhost:3000","http://192.168.18.193:3000"]

# Rutas de recursos
RESOURCES_PORTADAS_DIR=resources/portadas
RESOURCES_CAPITULOS_DIR=resources/capitulos
```

## Documentación de la API

La API sigue el estándar OpenAPI y está documentada con Swagger. Está disponible en:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

### Endpoints Principales

- `POST /auth/token` - Autenticación de usuarios
- `GET /mangas` - Lista todos los mangas
- `POST /mangas` - Crea un nuevo manga
- `GET /mangas/{id}` - Obtiene detalles de un manga
- `GET /capitulos/{manga_id}` - Lista capítulos de un manga
- `POST /comentarios` - Añade un comentario

## Estructura del Proyecto

```
vanillaga/
├── app/
│   ├── core/            # Configuración central
│   │   ├── config.py    # Configuración de la aplicación
│   │   └── security.py  # Utilidades de seguridad
│   │
│   ├── db/              # Base de datos
│   │   ├── init_db.py   # Inicialización de la DB
│   │   └── models/      # Modelos SQLAlchemy
│   │
│   ├── models/          # Modelos Pydantic
│   ├── rutas/           # Endpoints de la API
│   │   ├── auth.py      # Autenticación
│   │   ├── mangas.py    # Rutas de mangas
│   │   ├── capitulos.py # Rutas de capítulos
│   │   └── ...
│   │
│   └── utils/           # Utilidades
│
├── resources/           # Archivos estáticos
│   ├── portadas/        # Portadas de los mangas
│   └── capitulos/       # Archivos de capítulos
│
├── .env.example         # Plantilla de variables de entorno
├── docker-compose.yml   # Configuración de Docker
├── main.py              # Punto de entrada
└── requirements.txt     # Dependencias
```

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo LICENSE para más detalles.


> "Hecho por un lector para lectores, que pases un buen día y espero que te sirva el proyecto."

Última actualización: Enero 2026
