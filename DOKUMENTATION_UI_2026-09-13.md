# IUENNA – UI- und Institutionsnamen-Update vom 13.09.2026

## Anlass

Die Projektübersicht der IUENNA-Website wurde redaktionell und visuell gestrafft. Ziel war insbesondere, die Projektleitung kompakter darzustellen, die Förderung deutlicher hervorzuheben und die aktuellen institutionellen Kurzformen konsistent in der Benutzeroberfläche zu verwenden.

## Project Leadership

Der bisherige Fließtext mit den Namen und institutionellen Zuordnungen der Projektleitung wurde auf einen kurzen Einleitungssatz reduziert. Die relevanten Angaben stehen nun unmittelbar in den beiden Profilkarten:

- **Dominik Hagmann** – Project Coordinator · Principal Investigator – **kärnten.museum**
- **Franziska Waldhart** – Principal Investigator – **OeAI / OeAW**

Die Profilkarten wurden zugleich kompakter gestaltet. Insbesondere wurde die bisherige `flex-basis`-Wirkung auf schmalen Viewports überschrieben, damit die Karten mobil nicht unnötig hoch werden.

## Funding

Der bisher innerhalb der Leadership-Karte platzierte Funding-Block wurde entfernt. Stattdessen wird die Förderung als eigenständiger, visuell dominanter Abschnitt unmittelbar **vor „Activating Legacy Data: The Curation Workflow“** ausgegeben.

Der Abschnitt nennt:

- **Austrian Academy of Sciences (OeAW)** als Fördergeberin,
- das **Go!Digital 3.0 programme**,
- die Projektnummer **GD3.0_2021-24_IUENNA**,
- die Host Institutions **kärnten.museum** und **Austrian Archaeological Institute (OeAI) / OeAW**.

Damit werden Förderung und institutionelle Trägerschaft klar von der individuellen Projektleitung getrennt.

## Institutionelle Bezeichnungen

Für die aktuelle Website-Darstellung gelten folgende Kurzformen:

- `ÖAI` → **OeAI**
- `ÖAW` → **OeAW**
- `ACDH-CH` → **ACDH**
- ausgeschrieben: **Austrian Centre for Digital Humanities (ACDH)**

Die Normalisierung erfolgt in der sichtbaren Weboberfläche auch für dynamisch erzeugte Inhalte. Historische bzw. autoritative ARCHE-Metadaten werden dadurch nicht verändert; die Anpassung betrifft die Präsentationsschicht. Dadurch bleibt die Provenienz der archivierten Quelldaten erhalten, während die Website die aktuellen Institutionsnamen verwendet.

## Technische Umsetzung

Die bestehende Funktionalität von `scripts/nav.js` wurde ohne Verlust der bisherigen Navigations- und Ask-IUENNA-Erweiterungen erhalten:

- der bisherige Code liegt nun in `scripts/nav-base.js`;
- `scripts/nav.js` fungiert als schlanker Loader;
- die neuen projektbezogenen Darstellungsregeln liegen in `scripts/project-ui.js`;
- `README.md` und `llms.txt` wurden auf **OeAI**, **OeAW** und **ACDH** sowie die gemeinsame Trägerschaft durch **kärnten.museum** und **OeAI/OeAW** aktualisiert.

Diese Trennung hält die redaktionellen UI-Anpassungen von der bestehenden Navigations- und Assistant-Logik getrennt und erleichtert spätere Änderungen.
