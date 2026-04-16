# 🌙 Local Web Agent – Erftstadt

Findet automatisch lokale Betriebe in Erftstadt ohne Website, generiert professionelle Websites mit KI und hostet sie auf Netlify. Läuft jede Nacht und sendet dir morgens einen Report.

## Was der Agent macht

1. **Scraping**: Sucht auf Google Maps nach Friseuren, Handwerkern, Restaurants, Kosmetikstudios und Physiotherapeuten in Erftstadt
2. **Filtern**: Behält nur Betriebe ohne eigene Website
3. **Generieren**: Erstellt für jeden Betrieb eine individuelle, professionelle Website mit Claude AI
4. **Hosten**: Lädt jede Website auf Netlify hoch (eigene Subdomain pro Betrieb)
5. **Reporten**: Sendet dir morgens eine E-Mail mit allen Links

---

## Einrichtung (einmalig, ~15 Minuten)

### Schritt 1: Repository auf GitHub erstellen

1. Gehe zu [github.com/new](https://github.com/new)
2. Repository-Name: `local-web-agent`
3. Privat oder öffentlich – egal
4. Klicke **Create repository**
5. Lade alle Dateien aus diesem Ordner hoch

### Schritt 2: API-Keys besorgen

#### Anthropic API Key (Claude)
1. Gehe zu [console.anthropic.com](https://console.anthropic.com)
2. Klicke auf **API Keys** → **Create Key**
3. Key kopieren und sicher aufbewahren

#### Netlify Token
1. Gehe zu [app.netlify.com/user/applications](https://app.netlify.com/user/applications)
2. Unter **Personal access tokens** → **New access token**
3. Name: `local-web-agent`
4. Token kopieren

#### Gmail App-Passwort
1. Gehe zu deinem Google-Konto: [myaccount.google.com/security](https://myaccount.google.com/security)
2. **2-Schritt-Verifizierung** aktivieren (falls noch nicht)
3. Suche nach **App-Passwörter**
4. App: `Mail`, Gerät: `Sonstiges` → Name: `local-web-agent`
5. Das generierte 16-stellige Passwort kopieren

### Schritt 3: Secrets in GitHub hinterlegen

1. Gehe zu deinem GitHub Repository
2. Klicke auf **Settings** → **Secrets and variables** → **Actions**
3. Klicke auf **New repository secret** und füge diese 5 Secrets hinzu:

| Name | Wert |
|------|------|
| `ANTHROPIC_API_KEY` | Dein Anthropic API Key |
| `NETLIFY_TOKEN` | Dein Netlify Access Token |
| `GMAIL_USER` | Deine Gmail-Adresse (z.B. `dein.name@gmail.com`) |
| `GMAIL_APP_PASSWORD` | Das 16-stellige App-Passwort |
| `REPORT_TO` | E-Mail-Adresse für den Report (kann gleich wie `GMAIL_USER` sein) |

### Schritt 4: Workflow aktivieren

1. Gehe im Repository auf **Actions**
2. Klicke auf **I understand my workflows, go ahead and enable them**
3. Wähle **Nightly Local Web Agent**
4. Klicke auf **Enable workflow**

### Schritt 5: Ersten Testlauf starten

1. Gehe zu **Actions** → **Nightly Local Web Agent**
2. Klicke auf **Run workflow** → **Run workflow**
3. Warte ca. 30-60 Minuten
4. Schaue in dein E-Mail-Postfach 🎉

---

## Zeitplan

Der Agent läuft automatisch täglich um **3:00 Uhr** (MEZ) / **4:00 Uhr** (MESZ Sommerzeit).

Du erhältst die E-Mail typischerweise gegen **4:00-5:00 Uhr morgens**.

---

## Kosten

| Service | Kosten |
|---------|--------|
| GitHub Actions | Kostenlos (2.000 Minuten/Monat) |
| Netlify | Kostenlos (100 Sites, 100GB Bandwidth) |
| Anthropic Claude API | ~$0.50–2.00 pro Nacht (je nach Anzahl Betriebe) |
| Gmail | Kostenlos |

---

## Struktur

```
local-web-agent/
├── .github/
│   └── workflows/
│       └── nightly-agent.yml    # GitHub Actions Workflow
├── scripts/
│   ├── main.py                  # Orchestrator
│   ├── scraper.py               # Google Maps Scraping
│   ├── generator.py             # Website-Generierung (Claude AI)
│   ├── deployer.py              # Netlify Deployment
│   └── reporter.py              # E-Mail Report
├── requirements.txt
└── README.md
```

---

## Fehlerbehebung

**Keine E-Mail erhalten?**
- Schaue in den GitHub Actions Log (Actions → Letzter Run → Run details)
- Prüfe ob alle 5 Secrets korrekt gesetzt sind
- Gmail: Stelle sicher, dass du ein App-Passwort (nicht dein normales Passwort) nutzt

**Keine Betriebe gefunden?**
- Google Maps ändert manchmal seine HTML-Struktur – schau in den Log für Details
- Versuche den Workflow manuell zu starten

**Netlify-Fehler?**
- Prüfe ob dein Token noch gültig ist
- Kostenloser Plan: max. 500 Sites, 100 Deploys/Tag
