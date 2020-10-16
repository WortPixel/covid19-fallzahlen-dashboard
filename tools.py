from matplotlib import dates as mdates
from matplotlib import pyplot as plt
from matplotlib import rcParams
import numpy as np
import pandas as pd
import requests as r
import streamlit as st

LANDKREIS_QUERY = "https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_COVID19/FeatureServer/0/query?where=1%3D1&outFields=Landkreis&returnGeometry=false&returnDistinctValues=true&outSR=4326&f=json"
DATEN_QUERY = "https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_COVID19/FeatureServer/0/query?where=Landkreis%20%3D%20'{}'&outFields=*&outSR=4326&f=json"


@st.cache
def landkreise_abrufen():
    """Liste aller verfügbaren Landkreise abrufen.

    Returns:
        Pandas DataFrame mit Liste aller Stadt- und Landkreise.
        Diese beginnen mit einer Abkürzung SK bzw. LK für Stadt-
        bzw. Landkreis gefolgt vom Namen der Region.
        Falls es Probleme beim Abruf gab wird None zurückgegeben."""
    req = r.get(LANDKREIS_QUERY)
    if (req.status_code == 200):
        return pd.json_normalize(req.json()['features'])
    else:
        return None


@st.cache
def lokale_daten_abrufen(region: str, heutiger_tag: int) -> pd.DataFrame:
    """Daten zur gewählten Region abrufen.
    TODO: Liegen mehr als 5000 Meldungen vor, werden mehrere Abfragen durchge-
    führt, da die Abfragengrenze bei 5000 zu liegen scheint.

    Args: 
        region: str
            Land- oder Stadtkreis für den Daten abgerufen werden sollen.
            Muss eine Region der vorhandenen Landkreise sein.
        heutiger_tag: int
            Dieses Attribut erwartet den aktuellen Tag, lediglich, um den Cache
            ungültig zu machen, damit an einem anderen Tag der Datensatz frisch
            geladen wird.
    Returns: pandas.DataFrame
        Fallzahlen, und ähnlichen Werten, die vom Robert-Koch-Institut bereit
        gestellt werden. Daten werden immer für den gesamten verfügbaren Melde-
        zeitraum abegerufen. Falls es Probleme beim Abruf gab wird None zurück-
        gegeben."""
    region = region.replace(" ", "%20")

    # TODO zunächst Anzahl der Meldungen abfragen und bei Wert über 5t,
    # mehrere Anfragen durchführen und mergen.
    req = r.get(DATEN_QUERY.format(region))
    if (req.status_code == 200):
        # JSON parsen und 'attributes.' Präfix entfernen, welches als Artefakt
        # vom Auslesen des JSON-Rückgabewertes übrig ist.
        return pd.json_normalize(req.json()['features']).rename(
            lambda name: name.replace("attributes.", ""), axis=1)
    else:
        return None


@st.cache
def fallzahlen_extrahieren(daten: pd.DataFrame) -> pd.core.series.Series:
    '''Tageweise aggregierte Fallzahlen für jeden Tag des vorhandenen Zeitraums
    extrahieren.

    Args:
        daten: pandas.DataFrame
            API Rückgabewert vom Robert-Koch-Institut mit Einzelmeldungen.

    Returns: pandas.DataFrame
        Tageweise aggregierte Fallzahlen, mit Einträgen für jeden Tag des vor-
        handenen Zeitraums. Aufgefüllte Tage (ohne Meldung) werden mit einer
        Null versehen.'''
    # Das Meldedatum liegt jeweils als UNIX-Zeitangabe in ms vor. Umwandeln.
    daten['Meldedatum'] = pd.to_datetime(daten['Meldedatum'], unit='ms')
    # Datum als Index verwenden
    daten.set_index("Meldedatum", inplace=True)
    # Tägliche Fallzahlen über mehrere Meldungen hinweg, tageweise aufsummieren
    fallzahlen = daten["AnzahlFall"].groupby(daten.index.date).sum()
    # Für eine bessere Visualisierung, sollen zudem Tage an denen keine Meldung
    # eintraf mit einer Null aufgefüllt werden.
    zeitfenster = pd.date_range(start=fallzahlen.index.min(),
        end=fallzahlen.index.max())
    
    return fallzahlen.reindex(zeitfenster).fillna(0.0)


@st.cache
def einwohnerzahlen_laden() -> pd.core.series.Series:
    ''' Lädt Einwohnerzahlen aus versch. Quellen. Laden und Aufbereiten der
    Einwohnerzahlen von DESTATIS und Wikipedia (für Berlinerbezirke, da diese
    nicht im DESTATIS Datensatz enthalten sind).

    Returns: pandas.DataFrame
        Tabelle mit zwei Spalten: Landkreis und Einwohnerzahl.
    '''
    benoetigte_spalten = [0, 1, 2, 5]
    spalten_namen = ["Schlüssel", "Region", "Kreis", "Einwohnerzahl"]
    region_umbenennung = ["SK", "LK", "LK", "SK", "LK Stadtverband"]

    # Einwohnerzahlen von DESTATIS laden.
    df = pd.read_excel('data/04-kreise.xlsx',
                       sheet_name=1,
                       skiprows=3,
                       skipfooter=16,
                       usecols=benoetigte_spalten,
                       dtype=object,
                       names=spalten_namen)
    # Manuell irrelevante Einträge entfernen (z.B. von Spaltentiteln).
    df.drop([0,1,2])
    # Alle Einträge mit zu kurzem (Länge ungleich 5) Schlüssel aussortieren
    df = df.drop(index=df[df['Schlüssel'].apply(lambda x:len(str(x)))!=5].index)
    # Regionen erheben und umbenennen
    # Regionumwandlung:
    # - Kreisfreie Stadt & Stadtkreis -> SK
    # - Kreis & Landkreis -> LK
    # - Regionalverband -> LK Stadtverband
    regionen = df['Region'].unique()
    wörterbuch = dict(zip(regionen,region_umbenennung))
    df['Region'] = df['Region'].replace(wörterbuch)
    # Einige Städte müssen gesondert benannt werden:
    df.loc[377]['Kreis'] = 'Saarbrücken'
    df.loc[98]['Region'] = 'StadtRegion'
    df.loc[98]['Kreis'] = 'Aachen'
    df.loc[35]['Region'] = 'Region'
    df.loc[35]['Kreis'] = 'Hannover'
    # übrige Städte sind als Wort(e) des Kreises vor einem Komma zu extrahieren
    # Bspw.: "Flensburg, Stadt" --> "Flensburg"
    # Kreisbezeichnungen können auch Leerzeichen oder Bindestrich enthalten
    df['Kreis'] = df['Kreis'].str.extract(r'([\w\s-]+)')
    # Landkreis passend zur Schreibweise vom RKI als Index erstellen
    # Bspw.: "SK Flensburg"
    df['Landkreis'] = df['Region'] + ' ' + df['Kreis']
    # und als Index für spätere Zusammenführung von Datensätzen bereitstellen
    df.set_index('Landkreis', inplace=True)

    # Berlin ist bei DESTATIS nicht in Bezirke aufgeteilt, daher anfügen der
    # Einwohnerzahlen pro Bezirk von Wikipedia:
    # https://de.wikipedia.org/wiki/Berlin#Stadtgliederung (15.10.2020)
    berlin = pd.read_csv('data/Berlin.csv',
                         usecols=['Bezirk', 'Einwohnerzahl'],
                         dtype=object)
    berlin.set_index('Bezirk', inplace=True)
    
    # Einwohnzerzahlen beider Quellen zusammenführen
    df = df['Einwohnerzahl'].append(berlin['Einwohnerzahl'])

    return df

def visualisieren(fallzahlen: pd.core.series.Series, bezirk: str, stand: str,
        schranken: bool=False, kennzahlen: dict=None):
    '''Fallzahlen und etwaige Kennzahlen visualisieren.
    
    Args:
        fallzahlen: pd.core.series.Series
            Pandas Serie mit dem Meldedatum als Index und den jeweiligen Fall-
            zahlen als Wert.
        bezirk: str
            Name des Bezirks, wird als Titel des Plots verwendet.
        stand:  str
            Abrufdatum gemeldeter Fallzahlen, wird im Titel des Plots verwendet.
        kennzahlen: dict
            Dictionary mit Name einer jeweiligen Fallzahl als Key (wird in der
            Legende des Plots genutzt), und zu visualisierenden Kennzahlen als 
            Value. Es wird eine Kennzahl pro Tag erwartet.'''
    # Plottingbereich leeren
    plt.close('all')
    # und Seitenverhältnis einstellen
    fig, ax = plt.subplots(figsize=(10, 5))
    # Zeitzone festlegen
    rcParams['timezone'] = 'CEST'
    
    # Fallzahlen als Stufenplot mit Schattierung unter den Stufen darstellen
    plt.fill_between(fallzahlen.index, fallzahlen.values, step="pre", alpha=0.4)
    plt.plot(fallzahlen, drawstyle='steps', label="tägl. Fallzahlen")
    
    # Kennzahlen hinzufügen, falls vorhanden
    if (kennzahlen != None):
        for kennzahl, werte in kennzahlen.items():
            plt.plot(werte, drawstyle='steps', label=kennzahl)

    if schranken:
        plt.hlines([50], fallzahlen.index.min(), fallzahlen.index.max(), "red",
            label="Grenzwert")
        plt.hlines([35], fallzahlen.index.min(), fallzahlen.index.max(), "orange",
            label="Warnwert")
    
    # X-Axen Markierung auf Monate mit Teilstrichen bei Wochen setzen
    months = mdates.MonthLocator()  # every month
    months_fmt = mdates.DateFormatter('%b\'%y')
    weeks = mdates.WeekdayLocator() # every week
    
    ax.xaxis.set_major_locator(months)
    ax.xaxis.set_major_formatter(months_fmt)
    ax.xaxis.set_minor_locator(weeks)

    datemin = np.datetime64(fallzahlen.index.min(), 'm')
    datemax = np.datetime64(fallzahlen.index.max(), 'm') + np.timedelta64(1, 'm')
    ax.set_xlim(datemin, datemax)

    # Achsen und Plot beschriften, sowie Datumslegende lesbar ausrichten
    fig.autofmt_xdate(rotation=45)
    ax.set_xlabel('Meldedatum')
    ax.set_ylabel('gemeldete Fallzahlen')
    plt.title(bezirk+", Stand: "+stand)
    
    # Legende mittig anzeigen, falls Kennzahlen vorhanden sind
    if (kennzahlen != None):
        plt.legend(loc='upper center')
    # und zur Orientierung ein Raster (im Plot) einfügen
    ax.grid(True)
    return plt