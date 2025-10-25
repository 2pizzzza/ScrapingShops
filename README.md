# Aggregator Preisvergleich

Dieses Projekt dient zum Scrapen von Produktdaten aus verschiedenen Online-Shops. Die gesammelten Daten sind für die Verwendung in einem Backend für einen Preisvergleichsaggregator vorgesehen, um eine Datenbank zu füllen.

## Unterstützte Shops

Die folgenden Shops werden derzeit unterstützt und gescraped:

*   Adidas
*   H&M
*   JD Sports
*   New Yorker
*   Nike
*   Zalando

## Datenstruktur

Die gesammelten Produktdaten haben die folgende Struktur:

*   **title**: Titel des Produkts
*   **description**: Beschreibung des Produkts
*   **category**: Produktkategorie
*   **size**: Verfügbare Größen
*   **color**: Farbe des Produkts
*   **price**: Preis des Produkts
*   **img_url**: URL zum Produktbild
*   **ref_item**: Referenz-URL zum Produkt
*   **shop_id**: Kennung des Shops
*   **sex**: Geschlecht (z.B. Herren, Damen)

## Ausführung

Um die Daten zu sammeln, können die entsprechenden Python-Skripte ausgeführt werden (z.B. `adidas_scraping.py`, `hm_scraping.py`, etc.). Die Ergebnisse werden in den entsprechenden JSON-Dateien im `jsons`-Verzeichnis gespeichert.