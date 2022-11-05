# Ordered URLs for requests to look for the cheapest prices around my city
IDEALISTA_URL = 'https://www.idealista.com/alquiler-viviendas/vitoria-gasteiz-alava/?ordenado-por=precios-asc'
FOTOCASA_URL = 'https://www.fotocasa.es/es/alquiler/viviendas/vitoria-gasteiz/todas-las-zonas/l?sortType=price&sortOrderDesc=false&latitude=42.8517&longitude=-2.67141&combinedLocationIds=724,18,1,439,0,1059,0,0,0'

# Default top price for channel messages and when no prices is specified
DEFAULT_TOP_PRICE = 700

# Update flags to enable/disable portals from the channel updater
UPDATE_IDEALISTA = True
UPDATE_FOTOCASA = False

# Messages
INITIAL_MESSAGE = 'Emaidazu minutu bat!'
SEARCHING_IDEALISTA_MESSAGE = 'Idealistan bilatzen...'
SEARCHING_FOTOCASA_MESSAGE = 'Fotocasan bilatzen...'
INITIAL_AUTO_MESSAGE = 'Kaixo! Hamen dauzkazu oraintxe bertan dauden pisuak:'
OLD_FLATS_MESSAGE = 'Pisu hauek oraindik eskuragai daude:'
NEW_FLATS_MESSAGE = 'ADI!!\nPisu hauek berriak dira!'
NO_FLATS_MESSAGE = 'Barkatu, baina oraintxe bertan ez daude alokatzeko pisurik...'
FINAL_MESSAGE = 'Hortxe dauzkazu!'
START_MESSAGE = ('Kaixo!\n\n'
                 'Pisuak bilatzeko /bilatu komandoa erabili, mesedez!\n\n'
                 'Zerbitzu bakar bat erabiltezko, hurrengo komandoak dauzkazu:\n\n'
                 '    /idealista\n'
                 '    /fotocasa\n\n'
                 'Komandoak pisua alokatzeko gastatu nahi duzun gehiena onartzen dute, adibidez:\n\n'
                 '    /bilatu [euro]\n\n'
                 'Balio lehenetsia aldatzeko edo ikusteko, erabili hurrengo komandoa:\n\n'
                 '    /gehienekoa [euro]\n\n'
                 'Mila esker erabiltzeagatik!')
