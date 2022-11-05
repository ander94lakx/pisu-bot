from dataclasses import dataclass


@dataclass
class Flat:
    link: str
    price: str
    image: bytes
