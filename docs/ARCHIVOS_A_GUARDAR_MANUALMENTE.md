# Archivos a guardar manualmente (NO viajan a GitHub)

> Generado el 2026-07-23. Estos archivos están **ignorados por git** y por tanto
> **no** están en el repositorio remoto. Para usar el proyecto en otro dispositivo
> hay que copiarlos aparte.

---

## 1. CREDENCIALES — guardar SÍ o SÍ

### `.env` (raíz del proyecto)
Contiene las claves y contraseñas reales. **Nunca** se sube al repo.

Variables que contiene (solo los **nombres**, no los valores):

| Variable | Tipo |
|---|---|
| `AZURE_OPENAI_ENDPOINT` | endpoint |
| `AZURE_OPENAI_API_KEY` | **secreto** |
| `AZURE_OPENAI_API_VERSION` | config |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | config |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | config |
| `AZURE_SEARCH_SERVICE_ENDPOINT` | endpoint |
| `AZURE_SEARCH_API_KEY` | **secreto** |
| `AZURE_SEARCH_INDEX_NAME` | config |
| `SQLITE_DB_PATH` | config |
| `MAX_RETRIEVED_DOCS` | config |
| `RETRIEVAL_SCORE_THRESHOLD` | config |
| `DEBUG_MODE` | config |
| `USE_SQLITE_CHECKPOINTER` | config |
| `STUDENT_PASSWORD` | **secreto** |
| `ADMIN_PASSWORD` | **secreto** |

Plantilla vacía disponible en el repo: `.env.example`.

---

## 2. DATOS que quizá necesites en otro dispositivo

Ignorados por la regla `*.db` del `.gitignore`:

| Archivo | Tamaño | Necesario |
|---|---|---|
| `data/database/students.db` | ~372 KB | Sí (base de datos de alumnos que usa la app) |
| `data/database/students_backup_20260602.db` | ~112 KB | Backup (opcional) |

> Nota: si no copias `students.db`, puedes regenerarla en el nuevo dispositivo con
> `python scripts/generate_students.py`.

### Otros datos
- `data/alerts/*.json` — **SÍ están en el repo** (trackeados), no hay que copiarlos.
- `backups/ui_refinements_20260602/` — carpeta de backup local, ignorada. Opcional.
- `logs/` — ignorada. Son logs, capturas y scripts de verificación; **no** necesarios
  para ejecutar el proyecto. Copiar solo si quieres el histórico.

---

## 3. Recomendación de transferencia segura

- Copia el `.env` a mano mediante **gestor de contraseñas** o **USB cifrado**.
- **NUNCA** envíes el `.env` por email, chat, ni lo subas a la nube sin cifrar.
- En el dispositivo nuevo:
  1. Clona el repositorio privado.
  2. Copia `.env` en la raíz (usa `.env.example` como plantilla si lo creas de cero).
  3. Copia `data/database/students.db` (o regénerala con `generate_students.py`).

---

## Aviso de seguridad (historial de git)
Las claves Azure reales estuvieron commiteadas en `.env.example` en commits antiguos
(`dc97a6c`, `39dbb19`) y siguen presentes en la **punta de otras ramas** (master,
fase-5, etc.). Al ser un repo **privado** el riesgo está acotado, pero siguen siendo
válidas. Si en algún momento quieres cerrar esa exposición, **rota las dos claves
Azure** en el portal (`AZURE_OPENAI_API_KEY` y `AZURE_SEARCH_API_KEY`).
