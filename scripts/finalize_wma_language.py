#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

# qgis2web map: translate authored UI/explanatory text, preserve source-data values.
p = ROOT / "wma/qgis2web/qgis2web-index.html"
s = p.read_text(encoding="utf-8")
old = '''    <strong>Weitere Literatur:</strong><br /><br />
    Reiner, F., & Schwaiger, H. (2022). Geophysikalische Messungen in und um Globasnitz/Globasnica. 
    <em>Rudolfinum – Jahrbuch des Landesmuseums für Kärnten 2021</em>, 66–74. 
    <a href="https://www.zobodat.at/pdf/Rudolfinum_2021_0066-0074.pdf" target="_blank">https://www.zobodat.at/pdf/Rudolfinum_2021_0066-0074.pdf</a><br /><br />

    <strong>Beschreibung:</strong><br /><br />
    Dieses GeoPackage enthält die gesammelten Daten zu den Georadar- und Magnetikprospektionen 
    sowie die vektorisierten Umzeichnungen der Ausgrabung des Gräberfeldes von Globasnitz auf 
    Basis des Gesamtplans, wie auch die Verortung bestimmter Fundzonen. Es umfasst folgende Datensätze:<br /><br />

    <ul>
        <li><strong>Georadar-Daten</strong> (<code>glo20_georadar [EPSG:32633]</code>, <code>glo24_georadar_all [EPSG:32633]</code>): 
            Enthält die prozessierten Endergebnisse der Untersuchungen mittels Georadar 
            (2020: Teilergebnisse, 2024: Gesamtergebnisse) in Globasnitz.</li>
        <li><strong>Geomagnetik-Daten</strong> (<code>glo24_geomagnetik_all [EPSG:32633]</code>): 
            Beinhaltet die prozessierten Endergebnisse der Untersuchungen mittels Geomagnetik 
            in Globasnitz mit Stand 2024.</li>
        <li><strong>Vektorisierte Ausgrabungsdaten</strong> (<code>glo_ausgrabung_features</code>): 
            Enthält die vektorisierte Umzeichnung der Grabungsergebnisse der Ausgrabungen im 
            Gräberfeld Globasnitz gemäß dem Gesamtplan von J. Eitler.</li>
        <li><strong>Interpretation der geophysikalischen Messungen</strong> (<code>glo_geophysik_features</code>): 
            Dokumentiert die interpretierten Ergebnisse der geophysikalischen Untersuchungen.</li>
        <li><strong>Fundzonendaten (Glaser 1979)</strong> (<code>glo_Glaser_1979_features</code>): 
            Teilweise veraltetes Verzeichnis der Fundzonen nach den Grabungen der Jahre 
            1913, 1914, 1922, 1923, 1924, 1925, 1928, 1968 und 1976 in Globasnitz nach 
            der von F. Glaser (1979) angefertigten Fundstellenskizze 
            (für die aktuellste Ausführung siehe Glaser 2021, S. 54, Abb. 2).</li>
    </ul><br />

    <strong>Zitieren als:</strong><br /><br />'''
new = '''    <strong>Further reading:</strong><br /><br />
    Reiner, F., & Schwaiger, H. (2022). Geophysikalische Messungen in und um Globasnitz/Globasnica. 
    <em>Rudolfinum – Jahrbuch des Landesmuseums für Kärnten 2021</em>, 66–74. 
    <a href="https://www.zobodat.at/pdf/Rudolfinum_2021_0066-0074.pdf" target="_blank">https://www.zobodat.at/pdf/Rudolfinum_2021_0066-0074.pdf</a><br /><br />

    <strong>Description:</strong><br /><br />
    This GeoPackage brings together processed ground-penetrating-radar and magnetometry results, 
    vectorized excavation documentation for the Globasnitz cemetery, and selected find-zone locations. 
    The web map presents the following source layers:<br /><br />

    <ul>
        <li><strong>Ground-penetrating-radar data</strong> (<code>glo20_georadar [EPSG:32633]</code>, <code>glo24_georadar_all [EPSG:32633]</code>): 
            processed results from the 2020 and 2024 GPR surveys in Globasnitz.</li>
        <li><strong>Magnetometry data</strong> (<code>glo24_geomagnetik_all [EPSG:32633]</code>): 
            processed magnetometry results, current to the 2024 project dataset.</li>
        <li><strong>Vectorized excavation data</strong> (<code>glo_ausgrabung_features</code>): 
            vectorized excavation features from the Globasnitz cemetery based on the project plan.</li>
        <li><strong>Geophysical interpretation</strong> (<code>glo_geophysik_features</code>): 
            interpreted features derived from the geophysical survey data.</li>
        <li><strong>Find-zone data (Glaser 1979)</strong> (<code>glo_Glaser_1979_features</code>): 
            a historical find-zone register derived from Glaser's 1979 sketch and therefore retained as a legacy layer; 
            for a later published plan, see Glaser 2021, p. 54, fig. 2.</li>
    </ul><br />

    <strong>Cite as:</strong><br /><br />'''
if old in s:
    s = s.replace(old, new, 1)
elif "<strong>Further reading:</strong>" not in s:
    raise RuntimeError("Expected qgis2web German abstract block not found")

# Use HTTPS tiles and current OpenStreetMap attribution wording.
s = s.replace("http://tile.openstreetmap.org/{z}/{x}/{y}.png", "https://tile.openstreetmap.org/{z}/{x}/{y}.png")
s = s.replace(
    '<a href="https://www.openstreetmap.org/copyright">© OpenStreetMap contributors, CC-BY-SA</a> | <a href="https://hdl.handle.net/21.11115/0000-0015-EBEF-4">IUENNA, CC BY 4.0</a>',
    '<a href="https://www.openstreetmap.org/copyright">© OpenStreetMap contributors</a> | <a href="https://hdl.handle.net/21.11115/0000-0015-EBEF-4">IUENNA dataset (ARCHE)</a>'
)

# Force English labels for the bundled leaflet-measure UI without changing the library or source data.
needle = """            secondaryAreaUnit: 'hectares'\n        });"""
replacement = """            secondaryAreaUnit: 'hectares',
            labels: {
                measure: 'Measure',
                measureDistancesAndAreas: 'Measure distances and areas',
                createNewMeasurement: 'Create a new measurement',
                startCreating: 'Add points to the map to measure distance or area.',
                finishMeasurement: 'Finish measurement',
                lastPoint: 'Last point',
                area: 'Area',
                perimeter: 'Perimeter',
                pointLocation: 'Point location',
                areaMeasurement: 'Area',
                linearMeasurement: 'Distance',
                pathDistance: 'Distance',
                centerOnArea: 'Center on this area',
                centerOnLine: 'Center on this line',
                centerOnLocation: 'Center on this location',
                cancel: 'Cancel',
                delete: 'Delete',
                kilometers: 'Kilometers',
                hectares: 'Hectares',
                meters: 'Meters',
                sqmeters: 'Square meters'
            }
        });"""
if needle in s:
    s = s.replace(needle, replacement, 1)
elif "measureDistancesAndAreas: 'Measure distances and areas'" not in s:
    raise RuntimeError("Could not inject English measurement labels")

p.write_text(s, encoding="utf-8")

# qgis2web wrapper: make clear that original source-language attributes are preserved.
p = ROOT / "wma/qgis2web-home.html"
s = p.read_text(encoding="utf-8")
needle = "These are technical characteristics of the web-delivery method rather than interpretations of the archaeological data.</p>"
addition = "These are technical characteristics of the web-delivery method rather than interpretations of the archaeological data. Original field names and attribute values from the source dataset may remain in German inside map popups; they are preserved rather than silently translated.</p>"
if needle in s:
    s = s.replace(needle, addition, 1)
p.write_text(s, encoding="utf-8")

# Privacy page: add external map/geocoder services and repair legacy HTML details.
p = ROOT / "impressum-datenschutz.html"
s = p.read_text(encoding="utf-8")
map_notice = '''
            <h4>Kartenkacheln, Geokodierung und OpenTopoMap</h4>
            <p>Interaktive Karten laden je nach Ansicht Kartenkacheln von <strong>OpenStreetMap</strong> und teilweise <strong>OpenTopoMap</strong>. Dabei wird technisch eine Verbindung zu den jeweiligen Servern hergestellt und insbesondere die IP-Adresse übertragen. Die AI-assisted Web-Mapping-Anwendung bietet außerdem eine Orts-/Adresssuche über Leaflet Control Geocoder; in der derzeitigen Standardkonfiguration werden eingegebene Suchbegriffe bei Nutzung dieser Funktion an den OpenStreetMap-Nominatim-Dienst übermittelt. Bitte geben Sie dort keine personenbezogenen oder vertraulichen Informationen ein.</p>
'''
anchor = "            <h4>Nutzung von Chart.js</h4>"
if "Kartenkacheln, Geokodierung und OpenTopoMap" not in s:
    if anchor not in s:
        raise RuntimeError("Privacy external-service anchor not found")
    s = s.replace(anchor, map_notice + "\n" + anchor, 1)
s = s.replace("<p>Zur einheitlichen Darstellung von Schriftarten verwenden wir **Google Fonts**, gehostet auf Google-Servern.", "<p>Zur einheitlichen Darstellung von Schriftarten verwenden wir <strong>Google Fonts</strong>, gehostet auf Google-Servern.")
s = s.replace("Human-reviewed AI-assisted development workflow | Go!Digital 3.0 Project IUENNA\n    </footer>", "Human-reviewed AI-assisted development workflow | Go!Digital 3.0 Project IUENNA\n        </p>\n    </footer>")
p.write_text(s, encoding="utf-8")

# Keep Markdown privacy source aligned for external map services.
p = ROOT / "impressum-datenschutz.md"
s = p.read_text(encoding="utf-8")
if "OpenStreetMap-Nominatim" not in s:
    anchor = "#### **2. Nutzung von Chart.js**"
    notice = '''#### **Kartenkacheln, Geokodierung und OpenTopoMap**

Interaktive Karten laden je nach Ansicht Kartenkacheln von **OpenStreetMap** und teilweise **OpenTopoMap**. Dabei wird technisch eine Verbindung zu den jeweiligen Servern hergestellt und insbesondere die IP-Adresse übertragen. Die AI-assisted Web-Mapping-Anwendung bietet außerdem eine Orts-/Adresssuche über Leaflet Control Geocoder; in der derzeitigen Standardkonfiguration werden eingegebene Suchbegriffe bei Nutzung dieser Funktion an den OpenStreetMap-Nominatim-Dienst übermittelt. Bitte geben Sie dort keine personenbezogenen oder vertraulichen Informationen ein.

'''
    if anchor not in s:
        raise RuntimeError("Markdown privacy external-service anchor not found")
    s = s.replace(anchor, notice + anchor, 1)
p.write_text(s, encoding="utf-8")

# Homepage is English; align machine-readable language metadata.
p = ROOT / "index.html"
s = p.read_text(encoding="utf-8")
s = s.replace('<meta name="DC.language" content="de">', '<meta name="DC.language" content="en">', 1)
p.write_text(s, encoding="utf-8")

# Validation of public WMA authored UI.
qgis = (ROOT / "wma/qgis2web/qgis2web-index.html").read_text(encoding="utf-8")
for stale in ("Weitere Literatur:", "Beschreibung:", "Zitieren als:", "CC-BY-SA", "http://tile.openstreetmap.org"):
    if stale in qgis:
        raise RuntimeError(f"Stale qgis2web UI/provenance text remains: {stale}")
for required in ("Further reading:", "Description:", "Cite as:", "Measure distances and areas"):
    if required not in qgis:
        raise RuntimeError(f"Missing qgis2web English UI text: {required}")

legal = (ROOT / "impressum-datenschutz.html").read_text(encoding="utf-8")
for required in ("OpenStreetMap", "OpenTopoMap", "Nominatim", "sessionStorage", "localStorage", "Remote MCP"):
    if required not in legal:
        raise RuntimeError(f"Privacy page missing disclosure: {required}")

print("Final WMA language/privacy pass complete.")
