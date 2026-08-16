# SAVNO Raccolta Rifiuti

[![GitHub Release](https://img.shields.io/github/v/release/robertoamd90/savno-integration?style=flat-square)](https://github.com/robertoamd90/savno-integration/releases)
[![HACS validation](https://img.shields.io/github/actions/workflow/status/robertoamd90/savno-integration/validate.yml?label=HACS&style=flat-square)](https://github.com/robertoamd90/savno-integration/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](LICENSE)

Integrazione custom per Home Assistant che espone il calendario della raccolta porta a porta SAVNO, i prossimi ritiri e una card dashboard dedicata.

> Questo progetto non è affiliato né approvato da SAV.NO. S.p.A. I nomi e i marchi appartengono ai rispettivi proprietari.

## Installazione con HACS

[![Apri il repository in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=robertoamd90&repository=savno-integration&category=integration)

1. Apri il link qui sopra oppure, in HACS, vai su **Integrazioni → Repository personalizzati**.
2. Aggiungi `https://github.com/robertoamd90/savno-integration` come categoria **Integrazione**.
3. Cerca **SAVNO Raccolta Rifiuti** e installala.
4. Riavvia Home Assistant.

## Installazione manuale

1. Copia `custom_components/savno_rifiuti` nella directory `custom_components` della configurazione di Home Assistant.
2. Riavvia Home Assistant.

## Configurazione

[![Aggiungi l'integrazione a Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=savno_rifiuti)

Vai in **Impostazioni → Dispositivi e servizi → Aggiungi integrazione**, cerca **SAVNO Raccolta Rifiuti** e seleziona comune, indirizzo, civico e tipo di utenza richiesti.

## Entità

- Calendario **Raccolta rifiuti**.
- Sensore **Ritiro domani**.
- Sensore **Prossimi ritiri**, con l'elenco completo nell'attributo `ritiri`.

I dati vengono aggiornati ogni tre ore tramite i servizi pubblici del sito SAVNO.

## Card dashboard

L'integrazione registra automaticamente la card **SAVNO - Tabella prossimi ritiri**.

Per usarla vai in **Dashboard → Modifica dashboard → Aggiungi scheda**, cerca `SAVNO` e scegli la card. La tabella mostra **Giorno | Quando | Fra | Cosa** e usa le icone dei materiali.

| Giorno | Quando | Fra | Cosa |
|---|---|---|---|
| Lunedì | Domani | 1 giorno | Umido |
| Mercoledì | 19/08 | 3 giorni | Vetro |

Ogni riga espone anche `giorno_settimana`, `data`, `giorni_mancanti`, `cosa` e `rifiuti`, così i dati sono utilizzabili in automazioni e altre card.

## Compatibilità

L'integrazione usa una sorgente cloud e può smettere di funzionare se SAVNO modifica il proprio sito. Le immagini brand locali vengono mostrate nativamente da Home Assistant 2026.3 e versioni successive; il resto dell'integrazione continua a funzionare anche sulle versioni precedenti compatibili.

## Problemi e contributi

Prima di aprire una segnalazione, verifica i log di Home Assistant. Per bug o richieste usa le [GitHub Issues](https://github.com/robertoamd90/savno-integration/issues).
