from datetime import datetime

from matplotlib import pyplot as plt
import numpy as np
import pytz
import streamlit as st

from tools import *


# --- Streamlit Seite zusammenstellen ---
st.title('COVID19 lokale Fallzahlen')

# Allgemeine Nutzungshinweise
hinweis = st.empty()
hinweise_anzeigen = st.sidebar.checkbox("Allgemeine Hinweise zeigen?", True)
if hinweise_anzeigen:
    hinweis.markdown('''
    Diese Seite stellt den Verlauf gemeldeter COVID19 Fälle dar.
    Die Meldungen werden von der Datenschnittstelle des [Robert-Koch-Instituts](https://www.rki.de/) abgerufen und tageweise gesammelt dargestellt.

    Um einen Land- oder Stadtkreis auszuwählen kann im folgenden Eingabefeld ein Kreis ausgewählt werden.
    Es reicht dazu im Eingabefeld mit der Eingabe eines Kreises zu beginnen, bswp. "Dortmund".
    Anschließend kann ein Vorschlag ("SK Dortmund") ausgewählt werden, worauf die passenden Daten visualisiert werden.

    Es ist nicht notwendig vorherige Eingaben zu löschen, es kann jeweils direkt eine neue Eingabe erfolgen.

    Zusätzliche Einstellungen sind links in der Seitenleiste verfügbar.
    ''')

# Region auswählen:
# Mögliche Landkreise abrufen, um sie als Auswahl bereitzustellen
landkreise = landkreise_abrufen()
if (landkreise is None):
    st.error("Es konnte keine Verbindung zum Daten-Serive hergestellt werden.")
# Dortmund raussuchen, um es als Startwert zu setzen.
dortmund = np.where(landkreise['attributes.Landkreis']=='SK Dortmund')[0][0]
dortmund = int(dortmund)
# Landkreise zur Wahl stellen
nutzer_region = st.selectbox("Land- bzw. Stadtkreis wählen:", landkreise,
    index=dortmund)

# Aktuelles Datum abrufen, um an einem neuen Tag, die Daten frisch zu laden und
# nicht den Cache zu nutzen.
heute = datetime.now(pytz.timezone('Europe/Berlin')).day

# Regionale Daten abrufen:
# Wir müssen eine Kopie anlegen, da es ein veränderliches Datenobjekt ist,
# und dies bei direktem Zugriff den Streamlit Cache beeinträchtigen würde.
daten = lokale_daten_abrufen(region=nutzer_region, heutiger_tag=heute).copy()
if (daten is None):
    st.error("Beim Datenabruf ist ein Fehler aufgetreten.")

# Fallzahlen aus den abgerufenen Meldungen extrahieren
fallzahlen = fallzahlen_extrahieren(daten)

# Weitere Kennzahlen berechnen:
# Zunächst wurden die gesammelten Meldungen pro Tag gesammelt. Häufig werden 
# jedoch Mittelwerte über die letzten 7 Tage berichtet, diese und potentielle
# weitere Kennzahlen sollen im Folgenden berechnet und visualisiert werden.
kennzahlen = {}
# Auswahl der Tage, die zur Mittelwertbildung verwendet werden sollen.
# Bei 7 Tagen werden bswp. der aktuelle Tag, sowie die 6 vorherigen genutzt.
periode = st.sidebar.number_input("Anzahl Tage für eine Periode zur Mittelwertsbestimmung:", min_value=2,
    max_value=365, value=7)

# Einwohnerzahlen laden und visualisieren, falls gewünscht:
woechentliche_faelle = 'Fallzahlen pro 100t Einwohner und 7-Tage-Woche berechnen?'
schranken = False
if st.sidebar.checkbox(woechentliche_faelle, True):
    try:
        # Einwohnerzahlen laden, um diese im Anschluss zur Normierung auf
        # 100 000 Einwohner nutzen zu können.
        einwohnerzahlen = einwohnerzahlen_laden()
        nutzer_einwohner = int(einwohnerzahlen.loc[nutzer_region])
    except:
        # falls es Probleme gibt (z.B. Landkreis konnte nicht gefunden werden)
        # wird eine Ersatzzahl gewählt
        nutzer_einwohner = 100000
    # Einwohnerzahl in der Seitenleiste anzeigen und ggfs. abrufen.
    einwohner = st.sidebar.number_input("Einwohner gewählter Stadt:",
        min_value=1, max_value=10000000, value=nutzer_einwohner)
    # Anzahl Fälle pro Woche und 100 000 Einwohner berechnen, da dieser Wert
    # aktuell von Ländern zur Bewertung der Lage genutzt wird.
    rel_woechentliche_faelle = fallzahlen.rolling(7).sum() / (einwohner / 1e5)
    kennzahlen["pro 7-Tage-Woche & 100t Einwohner"] = rel_woechentliche_faelle

    # Abfrage, ob aktuelle Grenzwerte eingezeichnet werden sollen
    grenzwert_text = 'Wöchentliche Grenzwerte einzeichnen?'
    schranken = st.sidebar.checkbox(grenzwert_text, False)

perioden_mittel = fallzahlen.rolling(periode).mean()
kennzahlen["{} Tage(s) Mittel".format(periode)] = perioden_mittel

# Visualisierung erstellen:
# Aktualisierungsdatum der Meldungen aus der letzten genutzten Meldung auslesen
daten_stand = daten["Datenstand"].iloc[-1]

# Visualisierung erstellen lassen
fig = visualisieren(fallzahlen, nutzer_region, daten_stand, schranken,
    kennzahlen)
# und in der Web-App darstellen
st.pyplot(fig)

# Inzidenzwert benennen und den letzten anzeigen.
st.header('Inzidenzwert des vorherigen Tages {:.0f}\*'.format(
    kennzahlen["pro 7-Tage-Woche & 100t Einwohner"][-1]))
if hinweise_anzeigen:
    st.write('Aktuell werden die Fallzahlen der letzten 7 Tage normiert auf 100.000 Einwohner oft als Inzidenzwert bezeichnet. Dieser Wert wird als einheitliche Grenze genutzt, um etwaige Gegenmaßnahmen beim Überschreiten einer Grenze einzuleiten. Bisher wurden als Grenzwerte 35 und 50 verwendet. Diese können links über das seitliche Menü auch angezeigt werden.')
st.write('\* Der angezeigte Wert ist gerundet.')

# Auflistung der Fallzahlen des letzten Zeitfensters darstellen
st.header('Fallzahlen der letzten {} Tage:'.format(periode))
st.dataframe(fallzahlen[-periode:][::-1])

# Quellangaben zu den Daten darstellen
st.header('Datenquellen:')
st.write('- Fallzahlen: [Robert Koch-Institut (RKI)](https://npgeo-corona-npgeo-de.hub.arcgis.com/datasets/dd4580c810204019a7b8eb3e0b329dd6_0/data), dl-de/by-2-0.')
st.write('- Einwohnerzahlen: "**Statistisches Bundesamt (Destatis), 2020**" - "*Daten aus dem Gemeindeverzeichnis Kreisfreie Städte und Landkreise nach Fläche, Bevölkerung und Bevölkerungsdichte*", [Kreisfreie Städte und Landkreise am 31.12.2019](https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/Administrativ/04-kreise.html)')
st.write('- Einwohnerzahlen Berliner Bezirke: [Wikpedia](https://de.wikipedia.org/wiki/Berlin#Stadtgliederung) basierend auf Daten des "**Amt für Statistik** Berlin-Brandenburg" aus dem Bericht "*Statistischer Bericht - A I 5 – hj 2 / 19*", abgerufen am 15.10.2020')
