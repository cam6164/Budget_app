import io
import math
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pandas as pd

from src.config import MOYENS_PAIEMENT, STATUTS_IMPORT, TYPES_TRANSACTION
from src.database import connexion_db, maintenant
from src.services.backup_service import creer_sauvegarde
from src.services.regles_affectation_service import appliquer_regle, lister_regles, normaliser_texte
from src.utils import mois_budget_automatique, mois_canonique


COLONNES_IMPORT = [
    "importer", "date_reelle", "mois_reel", "mois_budget", "type",
    "sens_remboursement", "categorie", "categorie_remboursee", "libelle",
    "libelle_bancaire_brut",
    "montant_bancaire", "montant_budget", "moyen_paiement", "commentaire",
    "statut_import",
]


class ErreurValidationImport(ValueError):
    """Erreur métier enrichie avec l'étape précise de validation."""

    def __init__(self, etape: str, message: str):
        self.etape = etape
        self.message_detail = message
        super().__init__(f"{etape} : {message}")


def _texte_cellule(valeur: object, defaut: str = "") -> str:
    if valeur is None:
        return defaut
    try:
        if bool(pd.isna(valeur)):
            return defaut
    except (TypeError, ValueError):
        pass
    texte = str(valeur).strip()
    return defaut if not texte or texte.lower() in {"nan", "none", "nat"} else texte


def nettoyer_libelle_bancaire(libelle: object) -> str:
    """Produit un libellé court tout en laissant le texte bancaire brut disponible."""
    brut = normaliser_texte(libelle)
    if not brut:
        return ""
    enseignes = (
        (r"\bLE\s+CARRE\b", "LE CARRE"),
        (r"\bCARREFOUR\b", "CARREFOUR"),
        (r"\bCOCCI\b", "COCCI"),
        (r"\bSNCF\b", "SNCF"),
        (r"\bDECATHLON\b", "DECATHLON"),
        (r"\bENGIE\b", "ENGIE"),
        (r"\bWERO\b", "WERO"),
        (r"\bMC\s*DONALD(?:S)?\b", "MC DONALDS"),
    )
    for motif, nom in enseignes:
        if re.search(motif, brut):
            return nom
    for regle in lister_regles(actives_uniquement=True):
        mot_cle = normaliser_texte(regle.get("mot_cle"))
        if mot_cle and mot_cle in brut:
            return mot_cle

    nettoye = brut
    nettoye = re.sub(r"\bUIR[0-9A-Z]+\b", " ", nettoye)
    nettoye = re.sub(r"\b[A-Z0-9]{10,}\b", " ", nettoye)
    nettoye = re.sub(
        r"\b(?:PAIEMENT|PAIEMENT CB|CARTE|CB|PSC|VIREMENT|PRLV|PRELEVEMENT)\b",
        " ", nettoye,
    )
    nettoye = re.sub(r"\b\d{2}[/-]\d{2}(?:[/-]\d{2,4})?\b", " ", nettoye)
    nettoye = re.sub(r"\b\d{4,}\b", " ", nettoye)
    nettoye = re.sub(
        r"\b(?:BORDEAUX|PARIS|LYON|MARSEILLE|TOULOUSE|NANTES|LILLE|"
        r"IVRY\s+SUR\s+SEINE?)\b(?:\s+\d{1,2})?",
        " ", nettoye,
    )
    nettoye = re.sub(r"\bSC\b", " ", nettoye)
    nettoye = re.sub(r"[^A-Z0-9]+", " ", nettoye)
    nettoye = re.sub(r"\s+", " ", nettoye).strip(" -")
    return nettoye or brut


def _contenu_fichier(uploaded_file) -> bytes:
    if hasattr(uploaded_file, "getvalue"):
        contenu = uploaded_file.getvalue()
    else:
        if hasattr(uploaded_file, "seek"):
            uploaded_file.seek(0)
        contenu = uploaded_file.read()
    if isinstance(contenu, str):
        return contenu.encode("utf-8")
    return contenu


def lire_fichier_bancaire(uploaded_file) -> pd.DataFrame:
    """Lit un CSV courant ou un classeur XLSX et renvoie ses colonnes brutes."""
    nom = getattr(uploaded_file, "name", "fichier.csv")
    extension = Path(nom).suffix.lower()
    try:
        if extension == ".xlsx":
            if hasattr(uploaded_file, "seek"):
                uploaded_file.seek(0)
            dataframe = pd.read_excel(uploaded_file, dtype=object)
        elif extension == ".csv" or not extension:
            contenu = _contenu_fichier(uploaded_file)
            candidats: list[tuple[int, pd.DataFrame]] = []
            for encodage in ("utf-8-sig", "utf-8", "latin1"):
                try:
                    texte = contenu.decode(encodage)
                except UnicodeDecodeError:
                    continue
                for separateur in (";", ",", "\t"):
                    try:
                        candidat = pd.read_csv(
                            io.StringIO(texte), sep=separateur, dtype=object
                        )
                    except Exception:
                        continue
                    candidats.append((len(candidat.columns), candidat))
                if candidats and max(score for score, _ in candidats) > 1:
                    break
            if not candidats:
                raise ValueError("Aucun séparateur ou encodage CSV reconnu.")
            dataframe = max(candidats, key=lambda element: element[0])[1]
        else:
            raise ValueError("Format non pris en charge. Utilisez un fichier CSV ou XLSX.")
    except ValueError:
        raise
    except Exception as erreur:
        raise ValueError(
            f"Le fichier bancaire est illisible : {erreur}"
        ) from erreur
    # Une colonne Crédit ou Débit peut être entièrement vide sur un petit relevé :
    # elle doit rester disponible pour l'association manuelle.
    dataframe = dataframe.dropna(axis=0, how="all")
    if dataframe.empty or not len(dataframe.columns):
        raise ValueError("Le fichier ne contient aucune ligne bancaire exploitable.")
    dataframe.columns = [str(colonne).strip() for colonne in dataframe.columns]
    return dataframe.reset_index(drop=True)


def detecter_colonnes(dataframe: pd.DataFrame) -> dict[str, str]:
    colonnes = {normaliser_texte(colonne): colonne for colonne in dataframe.columns}

    def trouver(exacts: tuple[str, ...], fragments: tuple[str, ...] = ()) -> str | None:
        for candidat in exacts:
            if candidat in colonnes:
                return colonnes[candidat]
        for normalisee, originale in colonnes.items():
            if any(fragment in normalisee for fragment in fragments):
                return originale
        return None

    suggestions = {
        "date_reelle": trouver(
            ("DATE", "DATE REELLE", "DATE OPERATION"), ("DATE OPERATION", "DATE VALEUR")
        ),
        "libelle": trouver(
            ("LIBELLE", "DESCRIPTION", "INTITULE"),
            ("LIBELLE", "DESCRIPTION", "INTITULE", "DETAIL OPERATION"),
        ),
        "montant": trouver(("MONTANT", "AMOUNT"), ("MONTANT", "AMOUNT")),
        "debit": trouver(("DEBIT",), ("DEBIT", "RETRAIT")),
        "credit": trouver(("CREDIT",), ("CREDIT", "VERSEMENT")),
    }
    return {cle: valeur for cle, valeur in suggestions.items() if valeur is not None}


def normaliser_montant(valeur: object) -> float:
    if valeur is None or (isinstance(valeur, float) and math.isnan(valeur)):
        raise ValueError("Montant vide.")
    if isinstance(valeur, (int, float)):
        return float(valeur)
    texte = str(valeur).strip()
    if not texte or texte.lower() == "nan":
        raise ValueError("Montant vide.")
    negatif_parentheses = texte.startswith("(") and texte.endswith(")")
    texte = texte.replace("€", "").replace("EUR", "").replace("eur", "")
    texte = texte.replace("\u00a0", "").replace(" ", "").replace("'", "")
    if "," in texte and "." in texte:
        if texte.rfind(",") > texte.rfind("."):
            texte = texte.replace(".", "").replace(",", ".")
        else:
            texte = texte.replace(",", "")
    elif "," in texte:
        texte = texte.replace(",", ".")
    texte = re.sub(r"[^0-9+\-.]", "", texte)
    if not texte or texte in {"-", "+", "."}:
        raise ValueError(f"Montant non reconnu : {valeur}")
    montant = float(texte)
    return -abs(montant) if negatif_parentheses else montant


def normaliser_date(valeur: object) -> date:
    if isinstance(valeur, datetime):
        return valeur.date()
    if isinstance(valeur, date):
        return valeur
    if isinstance(valeur, (int, float)) and not isinstance(valeur, bool):
        if math.isnan(float(valeur)):
            raise ValueError("Date vide.")
        return (datetime(1899, 12, 30) + timedelta(days=float(valeur))).date()
    texte = str(valeur).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", texte):
        return date.fromisoformat(texte)
    try:
        date_convertie = pd.to_datetime(texte, dayfirst=True, errors="raise")
    except Exception as erreur:
        raise ValueError(f"Date non reconnue : {valeur}") from erreur
    return date_convertie.date()


def calculer_mois_reel(date_reelle: object) -> str:
    return mois_canonique(normaliser_date(date_reelle))


def calculer_mois_budget(
    date_reelle: object,
    type_transaction: str,
    categorie: str,
    libelle: str,
) -> str:
    return mois_budget_automatique(
        normaliser_date(date_reelle), type_transaction, categorie, libelle
    )


def _montant_ou_zero(valeur: object) -> float:
    try:
        return normaliser_montant(valeur)
    except ValueError:
        return 0.0


def _calculer_montant_budget(
    type_transaction: str,
    categorie: str,
    sens_remboursement: str,
    montant_bancaire: float,
    montant_saisi: object | None = None,
) -> float:
    try:
        base = abs(normaliser_montant(montant_saisi)) if montant_saisi is not None else abs(montant_bancaire)
    except ValueError:
        base = abs(montant_bancaire)
    if type_transaction in ("Revenu", "Dépense"):
        return base
    if type_transaction == "Épargne":
        return -base if "RETRAIT" in normaliser_texte(categorie) else base
    if type_transaction == "Remboursement":
        if sens_remboursement == "Je rembourse quelqu’un":
            return base
        if sens_remboursement == "On me rembourse":
            return -base
        return -base if montant_bancaire > 0 else base
    raise ValueError("Type de transaction non reconnu.")


def preparer_transactions_import(
    dataframe: pd.DataFrame, mapping_colonnes: dict[str, str]
) -> pd.DataFrame:
    date_colonne = mapping_colonnes.get("date_reelle")
    libelle_colonne = mapping_colonnes.get("libelle")
    montant_colonne = mapping_colonnes.get("montant")
    debit_colonne = mapping_colonnes.get("debit")
    credit_colonne = mapping_colonnes.get("credit")
    if not date_colonne or not libelle_colonne:
        raise ValueError("Associez obligatoirement les colonnes Date réelle et Libellé.")
    if not montant_colonne and not (debit_colonne and credit_colonne):
        raise ValueError("Associez une colonne Montant ou les colonnes Débit et Crédit.")

    lignes: list[dict] = []
    erreurs: list[str] = []
    for numero_ligne, (_, source) in enumerate(dataframe.iterrows(), start=2):
        try:
            date_reelle = normaliser_date(source[date_colonne])
            libelle_bancaire_brut = str(source[libelle_colonne]).strip()
            if not libelle_bancaire_brut or libelle_bancaire_brut.lower() == "nan":
                raise ValueError("libellé vide")
            libelle = nettoyer_libelle_bancaire(libelle_bancaire_brut)
            if montant_colonne:
                montant_bancaire = normaliser_montant(source[montant_colonne])
            else:
                debit = abs(_montant_ou_zero(source[debit_colonne]))
                credit = abs(_montant_ou_zero(source[credit_colonne]))
                montant_bancaire = credit - debit
            if montant_bancaire == 0:
                raise ValueError("montant nul")
            affectation = appliquer_regle(
                f"{libelle} {libelle_bancaire_brut}", montant_bancaire
            )
            mois_reel = calculer_mois_reel(date_reelle)
            mois_budget = calculer_mois_budget(
                date_reelle, affectation["type"], affectation["categorie"], libelle
            )
            montant_budget = _calculer_montant_budget(
                affectation["type"], affectation["categorie"],
                affectation["sens_remboursement"], montant_bancaire,
            )
            lignes.append(
                {
                    "importer": True,
                    "date_reelle": date_reelle.isoformat(),
                    "mois_reel": mois_reel,
                    "mois_budget": mois_budget,
                    "type": affectation["type"],
                    "sens_remboursement": affectation["sens_remboursement"],
                    "categorie": affectation["categorie"],
                    "categorie_remboursee": affectation["categorie_remboursee"],
                    "libelle": libelle,
                    "libelle_bancaire_brut": libelle_bancaire_brut,
                    "montant_bancaire": montant_bancaire,
                    "montant_budget": montant_budget,
                    "moyen_paiement": "Virement",
                    "commentaire": "",
                    "statut_import": affectation["statut_import"],
                }
            )
        except Exception as erreur:
            erreurs.append(f"ligne {numero_ligne} : {erreur}")
    if not lignes:
        detail = "; ".join(erreurs[:5])
        raise ValueError(f"Aucune ligne bancaire valide. {detail}")
    resultat = pd.DataFrame(lignes, columns=COLONNES_IMPORT)
    resultat.attrs["erreurs_lecture"] = erreurs
    return resultat


def detecter_doublons_import(dataframe: pd.DataFrame) -> pd.DataFrame:
    resultat = dataframe.copy()
    with connexion_db() as connexion:
        existantes = connexion.execute(
            "SELECT date_reelle, montant_bancaire, libelle FROM transactions"
        ).fetchall()
    cles_connues = {
        (
            ligne["date_reelle"], round(float(ligne["montant_bancaire"]), 2),
            normaliser_texte(ligne["libelle"]),
        )
        for ligne in existantes
    }
    vues_dans_fichier: set[tuple[str, float, str]] = set()
    for index, ligne in resultat.iterrows():
        cle = (
            normaliser_date(ligne["date_reelle"]).isoformat(),
            round(normaliser_montant(ligne["montant_bancaire"]), 2),
            normaliser_texte(ligne["libelle"]),
        )
        if cle in cles_connues or cle in vues_dans_fichier:
            resultat.at[index, "statut_import"] = "Doublon probable"
            resultat.at[index, "importer"] = False
        vues_dans_fichier.add(cle)
    return resultat


def est_ligne_selectionnee(valeur: object) -> bool:
    if isinstance(valeur, bool):
        return valeur
    return normaliser_texte(valeur) in {"TRUE", "VRAI", "1", "OUI", "YES"}


def valider_import(dataframe: pd.DataFrame) -> int:
    """Valide, sauvegarde puis insère uniquement les lignes cochées et non ignorées."""
    if not isinstance(dataframe, pd.DataFrame):
        raise ErreurValidationImport(
            "lecture de la sélection", "la table de relecture n’est pas exploitable"
        )
    transactions: list[dict] = []
    erreurs: list[str] = []
    for numero_ligne, (_, ligne) in enumerate(dataframe.iterrows(), start=1):
        if not est_ligne_selectionnee(ligne.get("importer", False)):
            continue
        statut = _texte_cellule(ligne.get("statut_import"), "À vérifier")
        if statut == "Ignorée":
            continue
        try:
            date_reelle = normaliser_date(ligne["date_reelle"])
            type_transaction = _texte_cellule(ligne.get("type"))
            if type_transaction not in TYPES_TRANSACTION:
                raise ValueError("type non reconnu")
            libelle = _texte_cellule(ligne.get("libelle"))
            if not libelle:
                raise ValueError("libellé obligatoire")
            libelle_bancaire_brut = _texte_cellule(
                ligne.get("libelle_bancaire_brut"), libelle
            )
            bancaire = normaliser_montant(ligne["montant_bancaire"])
            if bancaire == 0:
                raise ValueError("montant bancaire nul")
            categorie = _texte_cellule(ligne.get("categorie"))
            sens = _texte_cellule(ligne.get("sens_remboursement"))
            categorie_remboursee = _texte_cellule(ligne.get("categorie_remboursee"))
            if type_transaction == "Remboursement" and (
                sens not in ("On me rembourse", "Je rembourse quelqu’un")
                or not categorie_remboursee
            ):
                raise ValueError(
                    "un remboursement exige son sens et sa catégorie remboursée"
                )
            mois_reel_saisi = _texte_cellule(ligne.get("mois_reel"))
            try:
                mois_reel = (
                    mois_canonique(mois_reel_saisi)
                    if mois_reel_saisi
                    else calculer_mois_reel(date_reelle)
                )
            except ValueError:
                mois_reel = calculer_mois_reel(date_reelle)
            mois_saisi = _texte_cellule(ligne.get("mois_budget"))
            mois_budget = (
                mois_canonique(mois_saisi)
                if mois_saisi
                else calculer_mois_budget(date_reelle, type_transaction, categorie, libelle)
            )
            budget = _calculer_montant_budget(
                type_transaction, categorie, sens, bancaire,
                ligne.get("montant_budget"),
            )
            moyen = _texte_cellule(ligne.get("moyen_paiement"), "Virement")
            if moyen not in MOYENS_PAIEMENT:
                moyen = "Virement"
            if statut not in STATUTS_IMPORT:
                statut = "À vérifier"
            transactions.append(
                {
                    "date_reelle": date_reelle.isoformat(), "mois_reel": mois_reel,
                    "mois_budget": mois_budget, "type": type_transaction,
                    "sens": sens or None, "categorie": categorie or None,
                    "categorie_remboursee": categorie_remboursee or None,
                    "libelle": libelle,
                    "libelle_bancaire_brut": libelle_bancaire_brut,
                    "bancaire": bancaire, "budget": budget,
                    "moyen": moyen,
                    "commentaire": _texte_cellule(ligne.get("commentaire")),
                    "statut": statut,
                }
            )
        except Exception as erreur:
            erreurs.append(f"ligne {numero_ligne} : {erreur}")
    if erreurs:
        raise ErreurValidationImport(
            "contrôle des lignes", "; ".join(erreurs[:8])
        )
    if not transactions:
        return 0

    try:
        creer_sauvegarde("Sauvegarde automatique avant import bancaire")
    except Exception as erreur:
        raise ErreurValidationImport(
            "création de la sauvegarde", str(erreur)
        ) from erreur
    lot_id = uuid4().hex
    horodatage = maintenant()
    try:
        with connexion_db() as connexion:
            for numero, transaction in enumerate(transactions, start=1):
                connexion.execute(
                    """INSERT INTO transactions (
                           date_reelle, mois_reel, mois_budget, type,
                           sens_remboursement, categorie, categorie_remboursee,
                           libelle, libelle_bancaire_brut,
                           montant_bancaire, montant_budget,
                           moyen_paiement, commentaire, source, statut_import,
                           import_id, created_at, updated_at
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                                 'import_bancaire', ?, ?, ?, ?)""",
                    (
                        transaction["date_reelle"], transaction["mois_reel"],
                        transaction["mois_budget"], transaction["type"],
                        transaction["sens"], transaction["categorie"],
                        transaction["categorie_remboursee"], transaction["libelle"],
                        transaction["libelle_bancaire_brut"],
                        transaction["bancaire"], transaction["budget"],
                        transaction["moyen"], transaction["commentaire"],
                        transaction["statut"], f"{lot_id}-{numero}",
                        horodatage, horodatage,
                    ),
                )
    except Exception as erreur:
        raise ErreurValidationImport(
            "enregistrement en base", str(erreur)
        ) from erreur
    return len(transactions)
