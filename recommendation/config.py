# recommendation/config.py

TMDB_API_KEY = "TU_CLAVE_AQUI"

# Pesos para cada tipo de feature
WEIGHTS = {
    "genre": 0.11004030138426493,
    "overview": 0.20413527247240232,
    "availability": 0.3194322761520939,
    "year": 0.010513404590853339,
    "collection": 0.016996670755212898,
    "country": 0.05484492728228492,
    "company": 0.18801471876642722,
    "popularity": 0.007008936393902225,
    "vote_avg": 0.008761170492377781,
    "revenue": 0.00998773436131067,
    "orig_lang": 0.05081478885579114,
    "seasons": 0.008585947082530226,
    "episodes": 0.01086385141054845
}

REFERENCE_MOVIES = {
    278:    "The Shawshank Redemption",       
    496243: "Parasite",
    129:    "Spirited Away",
    545611: "Everything Everywhere All at Once",
    600354: "The Father",
    194:    "Amélie",
    58496:  "Senna",
    598:    "City of God",
    550:    "Fight Club",
    155:    "The Dark Knight"
}

REFERENCE_SERIES = {
    87739: "The Queen's Gambit",
    71446: "Money Heist",
    70523: "Dark",
    87108: "Chernobyl",
    1429:  "Attack on Titan",
    1396:  "Breaking Bad",
    42009: "Black Mirror",
    1438:  "The Wire",
    96677: "Lupin",
    1920:  "Twin Peaks"
}
