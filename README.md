# Pokedex

This repository contains scripts for building a web-based Pokedex.

## Fetching Pokémon Data

`fetch_pokemon_data.py` downloads Pokémon information from the public [PokeAPI](https://pokeapi.co/) and stores the results in `pokemon.json`.

```bash
python3 fetch_pokemon_data.py
```

The script uses only Python's standard library and will request all available Pokémon entries, which can take some time to complete.
