# Changelog

## 0.2.0 - vorbereitet am 2026-10-25

- **Breaking (vor 1.0):** `/chat` und `/trace/{request_id}` verlangen Service-JWTs
  des Shopware-Proxys. Der Prozess startet nur mit gültigem `AICA_BACKEND_SECRET`
  (64 kleine Hex-Zeichen); Issuer, Audience, Zweck und maximal 60 Sekunden
  Gültigkeit werden geprüft. Das passende Plugin ist AICA 2.0.0.
- Seit der ursprünglichen 0.1.0-Metadatenbasis: Domain-Terminologie aus JSON,
  Query-Auflösung, Prompt-/History-Anpassungen und dokumentierte Antwortnormalisierung.
- Reproduzierbare Installation aus bestehendem `uv.lock`; geändert wurde darin
  ausschließlich die eigene Projektversion. Keine Dependency-Upgrades.
- Offline-Authentifizierungsprüfungen und eigenes Runtime-Quellpaket mit Prüfsumme.
- `.env.*` wird nun auch beim Docker-Build ausgeschlossen.

Details und manuelle Schritte: [docs/release.md](docs/release.md).
Keine Datenbankmigration; kein automatisches Deployment.

## 0.1.0

- Bisherige Entwicklungsversion; kein vorhandener Versionstag oder GitHub-Release.
