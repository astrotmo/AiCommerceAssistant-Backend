# Release-Vorbereitung: Backend 0.2.0

Stand 25.10.2026, Branch `stage`, vorgeschlagener Tag `v0.2.0`.
Eigenständiger Python-Dienst, kein Shopware-Plugin. Lokal und im erreichbaren
Remote keine Tags/GitHub-Releases. Seit der initialen Version 0.1.0 kamen
Domain-Wissen, Query-/Prompt-/History-Anpassungen und Service-Authentifizierung
hinzu. Die inkompatible Auth-Änderung wird in der bestehenden Vor-1.0-Strategie
als Minor 0.2.0 vorbereitet. Das AICA-Plugin hat seine eigene Version 2.0.0.

## Manuelle Schritte

- Python >=3.10 gemäß Projektmetadaten, geprüft wurde Python 3.12.3.
- `uv sync --locked --no-dev` installiert genau die bestehenden Lock-Abhängigkeiten.
- Vor dem Start dasselbe `AICA_BACKEND_SECRET` wie im Plugin-Laufzeitsystem setzen
  (64 kleine Hex-Zeichen). Keine bestehenden Secrets wurden hier geändert.
  Systemuhren synchronisieren. `/healthz` ist öffentlich, `/chat` und `/trace/*`
  verlangen Service-Authentifizierung; `contextToken` ersetzt diese nicht.
- Shopware-OAuth, Ollama-Modelle und MCP-Verbindung separat konfigurieren und testen.
- `compose.yaml` ist die bestehende lokale Entwicklungskonfiguration mit
  Bind-Mounts, GPU-Anforderung und einem hostabhängigen Modellpfad. Sie ist keine
  fertig geprüfte Produktionskonfiguration. Vor einem späteren Einsatz Ports,
  Netzgrenzen, Volumes und Pfade bewusst prüfen; MCP hat keinen eigenen Auth-Schutz.
- Koordiniert mit AICA 2.0.0 aktualisieren; Rückfall auf älteren Plugin-Code verlangt
  einen passenden Backend-/Konfigurationsstand. Keine Datenbankmigration enthalten.

## Paket / Workflow

```bash
uv sync --locked --no-dev
uv run --frozen --no-dev python scripts/check.py
uv run --frozen --no-dev python scripts/package.py
```

`dist/shopware-ollama-mcp-0.2.0.tar.gz` ist ein Runtime-Quellpaket für uv/Docker,
kein Wheel, kein Plugin und kein vorgebautes Containerimage. Es enthält die beiden
Server-Einstiegspunkte, das `backend`-Paket samt JSON-Daten, `pyproject.toml`,
`uv.lock`, Dockerfile, Compose-Beispiel und Betriebsanleitung. Keine `.env*`,
virtuellen Umgebungen, Git-Daten oder Caches. `BUILD-INFO.json` und SHA-256
belegen Inhalt und Version. Abhängigkeiten werden beim lokalen Betrieb bzw.
Image-Build aus dem Lock installiert und sind nicht ins Quellpaket kopiert.

Der neue Workflow `Build & Package` prüft relevante `stage`-Pushes und PRs,
baut ein Containerimage ausschließlich lokal auf dem Runner und bewahrt nur bei
passendem Versionstag oder manuellem `package=true` das Quellpaket als
Actions-Artefakt auf (30 Tage). Kein Image-Push, kein GitHub-Release, kein Deployment.
Ein späterer Tag-Push löst deshalb keinen produktiven Rollout aus.

Ein manueller `workflow_dispatch`-Start ist auf GitHub erst verfügbar, wenn
die Workflow-Datei auch im Default-Branch `main` existiert. Die AICA-Workflows
sind hier auf `stage` vorbereitet; passende Tag-Pushes funktionieren unabhängig
von einer späteren Übernahme nach `main`.

## Durchgeführte Prüfungen

`uv lock --check --offline`, Installation mit `--locked` und die Offline-Checks
bestehen. Der lokale Docker-Build und der separate Build aus dem entpackten
Runtime-Quellpaket bestehen. Ein kurzlebiger Container ohne Netzwerk prüft Import,
App-Start, `/healthz` (200), unauthorisiertes `/chat` (401) und fehlende `.env*`
im Image. Ein synthetisches Test-Secret wurde nur für diesen Prozess verwendet;
bestehende Secrets wurden weder gelesen noch geändert.

Die gestartete lokale Instanz liefert `/healthz` 200 und weist `/chat` sowie
`/trace/*` ohne Service-Token mit 401 ab. Das belegt keine vollständige Chat-Inferenz,
gültige Shopware-OAuth-Rechte oder die Qualität von Modellergebnissen.

## Isolierter End-to-End-Paketnachweis

Das Runtime-Paket wird in ein eigenes Image gebaut und ohne Quellcode-Bind-Mounts
betrieben. Eine eigene leere Shopware-Datenbank mit synthetischem Katalog und
lesender Integration, ein interner Netzwerkbereich, Mailpit und eine separate
Modellkopie verhindern Zugriffe auf Entwicklungs-/Produktionsdaten und externen
Geschäftsbetrieb. Modellantworten sind echt (`granite4.1:8b`), nicht simuliert.

Ein tatsächlicher Storefront-Widget-Aufruf wurde nach AICA-Neuinstallation und
nach dem Update 1.0.0 → 2.0.0 bis zur gerenderten Antwort geprüft. Die Trace-Nachweise
belegen beide Modellphasen, `get_product_by_number_public` und das Ergebnis aus
der jeweils zugehörigen QA-Shopware-Datenbank. Fehlende/falsche/abgelaufene Tokens,
falsche Audience/Zweck und zu lange Gültigkeit werden am laufenden Dienst geprüft.
Die finalen Prüfsummen und die Releasebewertung stehen im Workspace-Releasebericht.
