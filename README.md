# PulseWatch

[English](#english) | [Español](#español)

---

## English

PulseWatch is a scalable platform for monitoring websites and HTTP APIs.

It periodically checks configured endpoints, measures availability and response
time, stores historical results, detects incidents, and notifies users when a
service fails or recovers.

### Main goals

PulseWatch will allow users to:

- Register and manage HTTP monitors.
- Configure monitoring intervals and expected responses.
- Track uptime and response-time history.
- Detect failures using configurable thresholds.
- Open and resolve incidents automatically.
- Receive notifications when services fail or recover.
- View monitoring information through a responsive dashboard.

### Planned technology stack

#### Frontend

- React
- TypeScript
- Vite
- React Router
- TanStack Query
- React Hook Form
- Zod
- CSS Modules
- Recharts
- Vitest
- Testing Library
- Playwright

#### Backend

- Python 3.13
- FastAPI
- Pydantic
- Pydantic Settings
- SQLAlchemy 2
- Alembic
- HTTPX
- Pytest

#### Data and background processing

- PostgreSQL
- Redis or a compatible native Windows alternative
- Celery
- Celery Beat

### Project status

PulseWatch is currently in its initial architecture and project-foundation
stage.

### Development environment

The initial development environment uses native Windows tools without Docker,
WSL, virtual machines, or other virtualization technologies.

### License

A license has not been selected yet.

---

## Español

PulseWatch es una plataforma escalable para monitorear sitios web y APIs HTTP.

Comprueba periódicamente los endpoints configurados, mide su disponibilidad y
tiempo de respuesta, almacena resultados históricos, detecta incidentes y
notifica a los usuarios cuando un servicio falla o se recupera.

### Objetivos principales

PulseWatch permitirá a los usuarios:

- Registrar y administrar monitores HTTP.
- Configurar intervalos de monitoreo y respuestas esperadas.
- Consultar el historial de disponibilidad y tiempos de respuesta.
- Detectar fallos mediante umbrales configurables.
- Abrir y resolver incidentes automáticamente.
- Recibir notificaciones cuando los servicios fallen o se recuperen.
- Consultar la información mediante un panel adaptable a distintos dispositivos.

### Tecnologías previstas

#### Frontend

- React
- TypeScript
- Vite
- React Router
- TanStack Query
- React Hook Form
- Zod
- CSS Modules
- Recharts
- Vitest
- Testing Library
- Playwright

#### Backend

- Python 3.13
- FastAPI
- Pydantic
- Pydantic Settings
- SQLAlchemy 2
- Alembic
- HTTPX
- Pytest

#### Datos y procesamiento en segundo plano

- PostgreSQL
- Redis o una alternativa compatible y nativa para Windows
- Celery
- Celery Beat

### Estado del proyecto

PulseWatch se encuentra actualmente en la etapa inicial de arquitectura y
preparación de sus fundamentos.

### Entorno de desarrollo

El entorno inicial de desarrollo utiliza herramientas nativas de Windows, sin
Docker, WSL, máquinas virtuales ni otras tecnologías de virtualización.

### Licencia

Todavía no se ha seleccionado una licencia.