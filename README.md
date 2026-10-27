# Kryptowaluta – Etap 1: sieć peer-to-peer i bezpieczny portfel

Projekt składa się z dwóch niezależnych programów:

- **Węzeł (node)**: serwer Flask, który zna innych peerów i rejestruje nowe węzły.
- **Portfel (wallet)**: klient w terminalu, który tworzy tożsamość, bezpiecznie przechowuje klucz prywatny i komunikuje się z węzłem wyłącznie przez HTTP/JSON (nie importuje kodu węzła).

## Struktura projektu

```
common/crypto.py     # kryptografia (klucze, podpisy, szyfrowanie klucza)
wallet/wallet.py     # portfel (CLI)
node/node.py         # węzeł sieci (Flask)
tests/               # testy pytest
```

## Instalacja

```
pip install cryptography requests flask pytest
```

Wszystkie polecenia powinny być uruchamiane z głównego folderu projektu.

## Portfel

```
python -m wallet.wallet create # nowy portfel
python -m wallet.wallet info # adres i klucz publiczny
python -m wallet.wallet sign "tekst" # podpis tekstu
python -m wallet.wallet peers --node http://127.0.0.1:5001
```

Inny plik portfela:

```
python -m wallet.wallet --file wallet_data/drugi.json create
```

Portfel zapisuje się w `wallet_data/wallet.json`. Klucz prywatny jest w pliku tylko w postaci zaszyfrowanej. Zgubionego hasła nie da się odzyskać.

## Węzeł

Każdy węzeł w osobnym terminalu:

```
python -m node.node --port 5001
python -m node.node --port 5002 --bootstrap http://127.0.0.1:5001
python -m node.node --port 5003 --bootstrap http://127.0.0.1:5001
```

`--bootstrap` to adres węzła startowego. Nowy węzeł rejestruje się u niego, pobiera jego listę peerów i przedstawia się pozostałym. Po chwili wszystkie węzły znają się nawzajem.

Endpointy:

| Endpoint | Opis |
|---|---|
| `GET /peers` | lista znanych peerów |
| `POST /register` | rejestracja węzła (`{"url": "..."}`), zwraca listę peerów |
| `GET /info` | adres i klucz publiczny węzła |

## Algorytmy kryptograficzne

| Element | Algorytm |
|---|---|
| Klucze | ECDSA, krzywa secp256k1 |
| Podpis | ECDSA z SHA-256 |
| Adres | pierwsze 40 znaków hex z SHA-256 klucza publicznego |
| Wyprowadzanie klucza z hasła | scrypt (n=2^15, r=8, p=1, sól 16 B) |
| Szyfrowanie klucza prywatnego | AES-256-GCM (nonce 12 B) |

Sól i nonce są losowe przy każdym szyfrowaniu, a parametry scrypt zapisywane w pliku portfela.

## Testy

```
pytest
```

## Ograniczenia

- Lista peerów i klucz węzła są tylko w pamięci (znikają po restarcie).
- Brak sprawdzania, czy peer nadal działa.
- Rejestracja węzłów nie jest uwierzytelniona, a komunikacja nie jest szyfrowana (HTTP na localhost).
