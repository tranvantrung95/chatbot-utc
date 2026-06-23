# STACK

**Date:** 2026-06-23
**Focus:** Technology stack and dependencies

## Backend (`utc-assistant`)
- **Language:** Python
- **API Framework:** FastAPI, Uvicorn
- **Database:** PostgreSQL (via `psycopg2-binary`)
- **Vector Store:** ChromaDB (`chromadb>=0.5.0`)
- **Document Processing:** PyMuPDF, Pillow, BeautifulSoup4
- **Web Requests:** requests
- **Auth/Security:** bcrypt
- **Env config:** python-dotenv

## Frontend (`utc-assistant-web`)
- **Language:** TypeScript
- **Framework:** Next.js (App Router, React 19)
- **Styling:** Tailwind CSS, Tailwind Merge, Tailwind Animate
- **UI Components:** Radix UI primitives
- **Animation:** motion
- **Markdown Rendering:** react-markdown
- **Linting/Formatting:** ESLint, PostCSS

## Scripts (`root`)
- **Language:** Python
- **Purpose:** Automation for building/generating reports (`build_*.py`, `gen_report*.py`)
