"""Multi-domain registry — the single source of truth for the 6 Bergeaud & Verluise
technologies. Each DomainSpec carries the official search query (CPC prefixes + keywords,
S2 Appendix), the gold-set CSV, the out-of-domain (OOD) set, and all derived artifact paths.

Self-driving (`autonomous_driving`) keeps its LEGACY flat paths + bespoke artifacts so the
committed self-driving experiment and notebook are untouched. The 5 added domains live under
per-domain subdirectories (DataSet/processed/<domain>/..., DataSet/mas/<domain>/...,
rubrics/<domain>_v1.json, outputs/scibert_<domain>_<arm>_<tag>).

CPC matching mirrors collect_expanded_pool: a candidate matches if its cpc_group startswith
any prefix here. _norm_cpc() fixes the appendix's zero-padding / range / typo quirks so the
prefixes line up with PatentsView's cpc_group format ("G08G1/0967", group not zero-padded).
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "DataSet"
PROCESSED_DIR = DATA_DIR / "processed"
LEAKAGE_DIR = DATA_DIR / "leakage"
EXPANDED_DIR = DATA_DIR / "expanded"
RUBRIC_DIR = ROOT / "rubrics"
MAS_DIR = DATA_DIR / "mas"
GOLD_DIR = DATA_DIR / "학습용 음성"          # the 5 other-domain gold sets live here
OUTPUTS_DIR = ROOT / "outputs"

AUTONOMOUS = "autonomous_driving"


# ----------------------------------------------------------------- CPC normalize
def _norm_cpc(code: str) -> str:
    """Normalize an appendix CPC code to a PatentsView cpc_group startswith-prefix.

    - uppercase, strip
    - a range 'C01B3/00-58' -> 'C01B3/' (the keyword filter constrains; prefix keeps the class)
    - remove zero-padding in the group number: 'G09C001/00' -> 'G09C1/00', 'G06F021/24' -> 'G06F21/24'
    """
    c = code.strip().upper().replace(" ", "")
    if not c:
        return ""
    if "-" in c:                                   # range -> keep the subclass+group prefix
        c = c.split("-", 1)[0]
        c = c[: c.index("/") + 1] if "/" in c else c
    # strip leading zeros on the group number that follows the 4-char subclass (e.g. G09C, G06F)
    c = re.sub(r"^([A-H]\d{2}[A-Z])0*(\d)", r"\1\2", c)
    return c


def _norm_list(codes) -> list[str]:
    seen, out = set(), []
    for c in codes:
        n = _norm_cpc(c)
        if n and n not in seen:
            seen.add(n); out.append(n)
    return sorted(out)


# ----------------------------------------------------------------- spec
@dataclass(frozen=True)
class DomainSpec:
    key: str                      # slug, e.g. "blockchain"
    display: str                  # "Blockchain"
    keywords: list[str]           # S2.3.1 — >=1 must appear in title+abstract (search query)
    cpc_prefixes: list[str]       # S2.3.2 — cpc_group startswith (search query)
    tasks: list[str]              # S2-1 annotation guideline (in-scope functional tasks -> rubric)
    gold_csv: Path                # gold benchmark for this domain (SEED / ANTISEED-*)
    legacy: bool = False          # autonomous_driving uses flat legacy paths

    # ---- derived paths --------------------------------------------------
    @property
    def subdir(self) -> str:
        return "" if self.legacy else self.key

    def _p(self, base: Path, name: str) -> Path:
        return base / name if self.legacy else base / self.key / name

    @property
    def rubric_path(self) -> Path:
        if self.legacy:
            return RUBRIC_DIR / f"{self.key}_v2.json"          # existing hand-seeded rubric
        return RUBRIC_DIR / f"{self.key}_v1.json"

    @property
    def pool_raw(self) -> Path:        # collect_expanded_pool output
        return self._p(EXPANDED_DIR, "expanded_candidates_raw.csv")

    @property
    def pool_clean(self) -> Path:      # build_expanded_trainset output (leakage removed)
        return self._p(PROCESSED_DIR, "training_expanded_clean.csv")

    @property
    def candidate_all(self) -> Path:   # build_candidate_all output (pool + OOD)
        return self._p(PROCESSED_DIR, "candidate_all.csv")

    @property
    def snorkel_labeled(self) -> Path:
        return self._p(PROCESSED_DIR, "snorkel_labeled_all.csv")

    @property
    def negatives_pool(self) -> Path:
        return self._p(PROCESSED_DIR, "negatives_pool.csv")

    @property
    def eval_processed(self) -> Path:
        return self._p(PROCESSED_DIR, "eval_processed.csv")

    @property
    def leaked_ids(self) -> Path:
        return self._p(LEAKAGE_DIR, "leaked_train_patent_ids.csv")

    @property
    def mas_audit(self) -> Path:
        return self._p(MAS_DIR, "mas_audit.jsonl")

    @property
    def mas_ranked(self) -> Path:
        return self._p(MAS_DIR, "mas_ranked_scores.csv")

    def model_name(self, arm: str, tag: str = "") -> str:
        """SciBERT output dir suffix. self-driving keeps the bare '<arm>_<tag>' naming."""
        stem = arm if self.legacy else f"{self.key}_{arm}"
        return f"{stem}_{tag}" if tag else stem

    def ood_domains(self, registry) -> list[str]:
        """All OTHER domains' gold sets serve as out-of-domain negatives for this one."""
        return [k for k in registry if k != self.key]


# ----------------------------------------------------------------- keyword lists (S2.3.1)
KW = {
    "additivemanufacturing": [
        "3d-printing", "3d printing", "stereolithography", "additive manufacturing",
        "three-dimensional objects", "three dimensional object", "rapid prototyping",
        "additive material manufacturing", "three dimensional printing material",
        "3d-printing materials", "photolithography", "fuse deposition mode",
        "fused deposition modeling",
    ],
    "blockchain": [
        "blockchain", "digital mining", "bitcoin", "cryptocoin", "cryptocurrency",
        "digital wallet", "ethereum", "smart contract", "smart contracts", "record keeping",
        "distributed ledger", "distributed node", "private ledger", "public ledger",
        "intelligent node", "full node", "digital signature", "digital signatures",
        "public key", "user identity", "hashing", "consensus methodolog", "proof of work",
        "proof of stake", "deposition based", "ripple",
    ],
    "computervision": [
        "computer vision", "machine vision", "lidar", "character recognition",
        "optical character recognition", "handwritten character recognition", "image to text",
        "text recognition", "face recognition", "facial recognition", "biometric data",
        "biometrics", "mass surveillance", "face unlock", "traffic camera", "object detection",
        "edge detection", "obstacle avoidance", "motion tracking", "neural network",
        "deep learning", "machine learning", "convolutional", "image classification",
        "image segmentation", "image recognition", "pattern recognition", "image processing",
    ],
    "genomeediting": [
        "dna editing", "gene editing", "genome editing", "genome engineering",
        "recombinant targeting vector", "homologous recombination", "double-strand dna break",
        "homology-directed repair", "targeted dna sequence", "dna cleavage", "fok1",
        "sequence-specific nuclease", "zinc finger nuclease", "cys2-his2",
        "transcriptional activator-like effector nuclease", "talen",
        "clustered regularly interspaced short palindromic repeat", "crispr",
        "cas9", "pre-crrna", "tracrrna", "rnase", "single guide rna", "cpf1", "ngago",
        "argonaute endonuclease", "natronobacterium gregoryi argonaute", "guide rna",
    ],
    "hydrogenstorage": [
        "hydrogen fuel cell", "hydrogen storage", "liquid hydrogen", "solid-state hydrogen",
        "compressed hydrogen", "dehydrogenation reaction", "hydrogen gas", "hydrogen fuel",
        "hydrogen storage material", "hydrogen-powered device", "metal hydride",
        "hydrogen production", "fuel cell",
    ],
}

# ----------------------------------------------------------------- CPC lists (S2.3.2, normalized)
CPC = {
    "additivemanufacturing": _norm_list([
        "B81C2201/0184", "A43D2200/60", "A23P2020/253", "B29C64/10", "C08L101/00",
        "B29C67/00", "B22F3/00", "G03F7/70416", "B28B1/001", "B33Y10/00", "B23K9/04",
        "B23K10/027", "B23K15/0086", "B23K11/0013",
    ] + [f"G05B2219/490{n:02d}" for n in list(range(2, 40))]),   # G05B2219/49002..49039
    "blockchain": _norm_list([
        "H04L9/08", "H04L67/00", "H04L9/10", "H04L9/12", "H04L9/14", "H04L9/28", "H04L29/06",
        "G06Q20/00", "G06F21/00", "G06F12/14", "G06Q20/06", "G06Q20/10", "G06Q20/20",
        "G06Q20/32", "G06Q20/36", "H04L2209/00", "G09C1/00", "G09C1/02", "G09C1/04",
        "G09C1/06", "H04L63/00", "G06Q30/0619", "G06F21/24", "G06F21/02", "G06F12/28",
        "G06F17/00",
    ]),
    "computervision": _norm_list([
        "B25J9/161", "G06F17/16", "G06N5/003", "G06N7/005", "G06N7/046", "B29C66/965",
        "G08B29/186", "F02D41/1405", "G01N29/4481", "G06F11/1476", "G06F17/2282",
        "H02P21/0014", "H02P23/0018", "H03H2222/04", "B64G2001/247", "F05B2270/707",
        "F05B2270/709", "F05D2270/709", "G10H2250/151", "H04L25/03165", "H04Q2213/054",
        "H04Q2213/343", "B60G2600/1876", "B60G2600/1878", "B60G2600/1879", "E21B2041/0028",
        "F16H2061/0081", "F16H2061/0084", "G06F2207/4824", "G10K2210/3024", "G10K2210/3038",
        "H03H2017/0208", "B29C2945/76979", "G05B2219/33002", "G06T2207/20081",
        "G06T2207/20084", "H04L2025/03464", "H04L2025/03554", "H04Q2213/13343", "B60W30/06",
        "B60W30/10", "B60W30/12", "B60W30/14", "B60W30/17", "G06T9/002", "G10L25/30",
        "G06K7/1482", "G06T3/4046", "B62D15/0285",
    ]),
    "genomeediting": _norm_list([
        "A01H4/00", "A01K67/00", "C12N15/00", "C12N1/00", "C12N5/00", "C12N7/00", "C12Y",
        "C12N5/10", "C12Q1/68", "C12Q1/70", "G01N33/00", "A61K48/00", "A61K31/7088",
        "C07K14/00",
    ]),
    "hydrogenstorage": _norm_list([
        "Y02E60/30", "Y02E60/32", "Y02E60/321", "Y02E60/322", "Y02E60/324", "Y02E60/325",
        "Y02E60/327", "Y02E60/328", "Y02E60/34", "Y02E60/36", "Y02E60/362", "Y02E60/364",
        "Y02E60/366", "Y02E60/368", "B01D53/02", "C01B3/00-58", "F17C2221/012", "C22C19/03",
        "C22C22/00", "C22C33/00", "F25B17/12", "H01M4/38", "H01M8/06", "F17C6/00", "F17C5/02",
    ]),
}

# ----------------------------------------------------------------- annotation tasks (S2-1)
TASKS = {
    "additivemanufacturing": [
        "Create a 3D printable model with computer-aided design",
        "Examine a stereolithography file for errors and inconsistency",
        "Convert a model into a series of thin layers (slicing)",
        "Manufacture materials for 3D printing",
        "Print a 3D model (additive layer-by-layer fabrication)",
    ],
    "blockchain": [
        "Record transactions between two parties on a ledger",
        "Serve as a public transaction ledger of a cryptocurrency",
        "Execute or enforce a smart contract",
        "Hash-tree verification / verify document authenticity / proof of work",
        "Analyse transactions in a distributed ledger",
        "Manage an identity system based on peer-to-peer protocols (IDMS) / mediate user authentication",
    ],
    "computervision": [
        "Process digital images",
        "Analyse digital images",
        "Understand / interpret digital images (recognition, detection, classification)",
    ],
    "genomeediting": [
        "Target a specific DNA sequence",
        "Break / cleave a DNA sequence (e.g. double-strand break)",
        "Edit a DNA sequence (insert / delete / replace)",
    ],
    "hydrogenstorage": [
        "Hydrogen production and compression",
        "Generate power from hydrogen gas",
        "Design vessel containment resistant to hydrogen permeation and corrosion (incl. thermal management)",
        "Manufacture a fuel cell using hydrogen",
        "Provide hydrogen to a hydrogen-powered device (fill, tank)",
    ],
}

DISPLAY = {
    "additivemanufacturing": "Additive Manufacturing",
    "blockchain": "Blockchain",
    "computervision": "Computer Vision",
    "genomeediting": "Genome Editing",
    "hydrogenstorage": "Hydrogen Storage",
}

# ----------------------------------------------------------------- build registry
def _build_registry() -> dict[str, DomainSpec]:
    reg: dict[str, DomainSpec] = {}
    # self-driving: legacy flat paths; CPC/keywords imported from collect_expanded_pool for fidelity
    from scripts import collect_expanded_pool as _sdv  # noqa: avoid duplicating the SDV query
    reg[AUTONOMOUS] = DomainSpec(
        key=AUTONOMOUS, display="Self-driving Vehicle",
        keywords=list(_sdv.KEYWORDS), cpc_prefixes=list(_sdv.CPC_PREFIXES),
        tasks=["Enable vehicles to make autonomous decisions", "Automate vehicle handling",
               "Vehicle-to-vehicle communication", "Communication between vehicle and rest-of-the-world"],
        gold_csv=DATA_DIR / "Evaluation_Set.csv", legacy=True,
    )
    for key in ("additivemanufacturing", "blockchain", "computervision",
                "genomeediting", "hydrogenstorage"):
        reg[key] = DomainSpec(
            key=key, display=DISPLAY[key], keywords=KW[key], cpc_prefixes=CPC[key],
            tasks=TASKS[key], gold_csv=GOLD_DIR / f"training_{key}.csv", legacy=False,
        )
    return reg


DOMAINS: dict[str, DomainSpec] = _build_registry()
NEW_DOMAINS = [k for k in DOMAINS if k != AUTONOMOUS]


def get(domain: str) -> DomainSpec:
    if domain not in DOMAINS:
        raise KeyError(f"unknown domain '{domain}'. known: {list(DOMAINS)}")
    return DOMAINS[domain]
