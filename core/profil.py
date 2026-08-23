from dataclasses import dataclass, field
from datetime import date
from typing import List

@dataclass
class NutzerProfil:
    geburtsdatum: str
    renteneintrittsdatum: str
    wunschrente_heutige_kaufkraft: float
    aktuelles_brutto_monat: float  # NEW: Aktuelles monatliches Bruttogehalt
    inflation_prozent: float = 2.0
    gehaltssteigerung_prozent: float = 2.0  # Globale Gehaltssteigerung p.a.
    anzahl_kinder: int = 0
    kindergeburtsjahre: List[int] = field(default_factory=list)
    _geburtsdatum_obj_cache: date = field(init=False, repr=False)
    _renteneintrittsdatum_obj_cache: date = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._geburtsdatum_obj_cache = date.fromisoformat(self.geburtsdatum)
        self._renteneintrittsdatum_obj_cache = date.fromisoformat(self.renteneintrittsdatum)

    @property
    def _geburtsdatum_obj(self) -> date:
        return self._geburtsdatum_obj_cache

    @property
    def _renteneintrittsdatum_obj(self) -> date:
        return self._renteneintrittsdatum_obj_cache

    @property
    def jahre_bis_rente(self) -> float:
        taegliche_differenz = (self._renteneintrittsdatum_obj - date.today()).days
        if taegliche_differenz < 0:
            return 0.0
        return taegliche_differenz / 365.25

    @property
    def monate_bis_rente(self) -> int:
        heute = date.today()
        rente = self._renteneintrittsdatum_obj
        if rente <= heute:
            return 0
        monate = (rente.year - heute.year) * 12 + (rente.month - heute.month)
        if rente.day < heute.day:
            monate -= 1
        return max(0, monate)

    def berechne_monate_fuer_zeitraum(self, start_datum_str: str) -> int:
        """Berechnet die exakte Anzahl der Monate von einem Startdatum bis zum Renteneintritt."""
        start = date.fromisoformat(start_datum_str)
        rente = self._renteneintrittsdatum_obj
        if rente <= start:
            return 0
        monate = (rente.year - start.year) * 12 + (rente.month - start.month)
        if rente.day < start.day:
            monate -= 1
        return max(0, monate)

    def in_heutige_kaufkraft_umrechnen(self, zukunfts_wert_nominal: float) -> float:
        faktor = (1 + self.inflation_prozent / 100) ** self.jahre_bis_rente
        return zukunfts_wert_nominal / faktor
