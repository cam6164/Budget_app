import calendar
import unicodedata
from datetime import date, datetime


MOIS_FR = [
    "janv", "févr", "mars", "avr", "mai", "juin",
    "juil", "août", "sept", "oct", "nov", "déc",
]


def mois_canonique(valeur: str | date | datetime) -> str:
    if isinstance(valeur, (date, datetime)):
        return valeur.strftime("%Y-%m")
    valeur = valeur.strip()
    if len(valeur) == 7 and valeur[4] == "-" and valeur[:4].isdigit():
        return valeur
    for numero, nom in enumerate(MOIS_FR, start=1):
        if valeur.lower().startswith(nom) and "-" in valeur:
            annee_courte = int(valeur.rsplit("-", 1)[1])
            return f"{2000 + annee_courte:04d}-{numero:02d}"
    raise ValueError(f"Mois non reconnu : {valeur}")


def libelle_mois(mois: str) -> str:
    annee, numero = map(int, mois_canonique(mois).split("-"))
    return f"{MOIS_FR[numero - 1]}-{annee % 100:02d}"


def ajouter_mois(mois: str, decalage: int) -> str:
    annee, numero = map(int, mois_canonique(mois).split("-"))
    index = annee * 12 + numero - 1 + decalage
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def choix_mois_autour(mois_reference: str) -> dict[str, str]:
    return {
        "M-2": ajouter_mois(mois_reference, -2),
        "M-1": ajouter_mois(mois_reference, -1),
        "M": mois_canonique(mois_reference),
        "M+1": ajouter_mois(mois_reference, 1),
        "M+2": ajouter_mois(mois_reference, 2),
    }


def mois_budget_automatique(
    date_reelle: date | datetime,
    type_transaction: str,
    categorie: str | None,
    libelle: str | None,
) -> str:
    mois_reel = mois_canonique(date_reelle)
    texte = f"{categorie or ''} {libelle or ''}".lower()
    texte = "".join(
        caractere for caractere in unicodedata.normalize("NFD", texte)
        if unicodedata.category(caractere) != "Mn"
    )
    mots_salaire = ("salaire", "paie", "paye")
    if (
        type_transaction == "Revenu"
        and date_reelle.day >= 18
        and any(mot in texte for mot in mots_salaire)
    ):
        return ajouter_mois(mois_reel, 1)
    return mois_reel


def mois_de_l_annee(annee: int) -> list[str]:
    return [f"{annee:04d}-{mois:02d}" for mois in range(1, 13)]


def jours_du_mois(mois: str) -> int:
    annee, numero = map(int, mois_canonique(mois).split("-"))
    return calendar.monthrange(annee, numero)[1]


def euros(valeur: float) -> str:
    return f"{valeur:,.2f} €".replace(",", " ").replace(".", ",")

