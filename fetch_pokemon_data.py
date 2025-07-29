import json
import time
from urllib.request import urlopen

BASE_URL = 'https://pokeapi.co/api/v2'

def fetch_all_pokemon_urls():
    with urlopen(f'{BASE_URL}/pokemon?limit=100000&offset=0') as response:
        data = json.load(response)
    return [entry['url'] for entry in data['results']]

def fetch_pokemon_data(url):
    with urlopen(url) as response:
        return json.load(response)

def main():
    pokemon_urls = fetch_all_pokemon_urls()
    pokemon_data = []
    for idx, url in enumerate(pokemon_urls, start=1):
        print(f'Fetching {idx}/{len(pokemon_urls)}: {url}')
        pokemon_data.append(fetch_pokemon_data(url))
        time.sleep(0.2)
    with open('pokemon.json', 'w') as f:
        json.dump(pokemon_data, f, indent=2)

if __name__ == '__main__':
    main()
