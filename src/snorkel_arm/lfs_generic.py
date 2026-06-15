"""Generic, domain-driven Snorkel labeling functions for the 5 added domains.

Self-driving keeps its bespoke lfs.py (the subtle automate-vs-assist boundary). For the
other domains the boundary is the GENERIC one — does the abstract discuss a domain task —
and the gold is easier (Bergeaud reports ~90% F1 vs ~79% for self-driving). So the LFs are
keyword heuristics over the appendix keyword list (S2.3.1):

  lf_domain_keyword   : >=1 of THIS domain's keywords present            -> SEED
  lf_strong_signal    : >=2 distinct domain keywords (denser evidence)   -> SEED
  lf_other_domain     : another Bergeaud domain's keywords present and    -> NOT_SEED
                        NONE of this domain's (out-of-domain look-alike)
  lf_no_signal        : no domain keyword at all                          -> NOT_SEED

Vote predicates are pure python (testable on 3.14); build_lfs_for_domain() wraps them for Colab.
Snorkel's LabelModel reconciles the votes — keyword presence alone is a weak/noisy signal,
which is exactly the limitation the MAS reasoning arm is meant to beat.
"""
from __future__ import annotations

SEED = 1
NOT_SEED = 0
ABSTAIN = -1


def _norm(s: str) -> str:
    return (s or "").lower()


def _count_hits(text: str, terms) -> int:
    t = _norm(text)
    return sum(1 for k in terms if k in t)


def make_lf_specs(domain_key: str, registry) -> list[tuple[str, callable]]:
    """Build (name, predicate) pairs for `domain_key` using its + other domains' keywords."""
    spec = registry[domain_key]
    own = [k.lower() for k in spec.keywords]
    other = []
    for k in spec.ood_domains(registry):
        other.extend(kw.lower() for kw in registry[k].keywords)
    # keywords shared with this domain must not count as "other-domain" evidence
    own_set = set(own)
    other = [k for k in other if k not in own_set]

    def vote_domain_keyword(text: str) -> int:
        return SEED if _count_hits(text, own) >= 1 else ABSTAIN

    def vote_strong_signal(text: str) -> int:
        return SEED if _count_hits(text, own) >= 2 else ABSTAIN

    def vote_other_domain(text: str) -> int:
        if _count_hits(text, own) == 0 and _count_hits(text, other) >= 1:
            return NOT_SEED
        return ABSTAIN

    def vote_no_signal(text: str) -> int:
        return NOT_SEED if _count_hits(text, own) == 0 else ABSTAIN

    return [
        ("lf_domain_keyword", vote_domain_keyword),
        ("lf_strong_signal", vote_strong_signal),
        ("lf_other_domain", vote_other_domain),
        ("lf_no_signal", vote_no_signal),
    ]


def build_lfs_for_domain(domain_key: str, registry):
    """Snorkel LabelingFunction list for `domain_key` (Colab only — needs snorkel)."""
    from snorkel.labeling import LabelingFunction

    def make(fn):
        return lambda x: fn(x.text)

    return [LabelingFunction(name=name, f=make(fn))
            for name, fn in make_lf_specs(domain_key, registry)]
