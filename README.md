# COVID19-Historie
Dieses Projekt ist eine Streamlit-App zur einfachen Visualisierung der Historie von COVID19-Fallzahlen deutscher Land- und Stadtkreise.

Es werden Fallzahlen vom Robert-Koch-Institut abgerufen und für einen ausgewählten Kreis dargestellt. Zudem werden aktuell zwei Kennzahlen mit geplottet:
1. Der arithmetische Mittelwert eines selbstgewählten Zeitraums, z.B. einer Woche.
2. Die Anzahl der Fälle eines Kreises pro Woche und 100 000 Einwohner.

## Nutzung

Für die Nutzung wird Python in Verbindung mit verschiedenen Bibliotheken (insbesondere der `streamlit` Bibliothek benötigt). Weitere Anforderungen sind der `requirements.txt` zu entnehmen.

1. Benötigte Bibliothekten installieren: `pip install -r requirements.txt`
2. Streamlit App starten: `streamlit run app.py`
3. Den Anweisungen im Terminal folgen und (bei Standardeinstellungen) `localhost:8501` im Browser aufrufen, um die App zu öffnen.
4. Zum Beenden im Terminal `Strg+C` eingeben und bestätigen.

Die Periodizität des Zeitraumes für die Mittelwerterstellung, sowie die Einwohnerzahl (bei Auswahl der Option *Fallzahlen pro 100t Einwohner und Woche berechnen?*) kann in der Seitenleiste (links) angepasst werden.

Für die meisten Kreise, für die vom Robert-Koch-Institut Fallzahlen vorliegen, sind auch Einwohnerzahlen hinterlegt. Ist dies nicht der Fall wird eine Einwohnerzahl von 100.000 angenommen, welche in den Optionen der Seitenleiste (links) angepasst werden kann.

## Disclaimer

Der Author hat keinen medizinischen Hintergrund und kennt sich nicht mit Virologie aus. Dieses Projekt dient lediglich der reinen Visualisierung gemeldeter Fallzahlen und etwaiger Kennzahlen aus Eigeninteresse. Eine öffentliche Bereitstellung wurde gewählt, um anderen mit gleichem Interesse potenzielle Arbeit bei der Nutzung des APIs des Robert-Koch-Institutes zu ersparen, oder einen einfachen Einstieg für eigene Visualisierungen zu geben.

## Datenquellen

- Fallzahlen: [Robert Koch-Institut (RKI)](https://npgeo-corona-npgeo-de.hub.arcgis.com/datasets/dd4580c810204019a7b8eb3e0b329dd6_0/data), dl-de/by-2-0, werden live abgerufen.
- Einwohnerzahlen: "**Statistisches Bundesamt (Destatis), 2020**" - "*Daten aus dem Gemeindeverzeichnis Kreisfreie Städte und Landkreise nach Fläche, Bevölkerung und Bevölkerungsdichte*", [Kreisfreie Städte und Landkreise am 31.12.2019](https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/Administrativ/04-kreise.html), liegen unter `data/04-kreise.xlsx` vor.
- Einwohnerzahlen Berliner Bezirke: [Wikpedia](https://de.wikipedia.org/wiki/Berlin#Stadtgliederung) basierend auf Daten des "**Amt für Statistik** Berlin-Brandenburg" aus dem Bericht "*Statistischer Bericht - A I 5 – hj 2 / 19*", abgerufen am 15.10.2020, liegen unter `data/Berlin.csv` vor.