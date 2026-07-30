"""Contract: every LLM-facing schema must survive OpenAI strict JSON-schema parsing.

`chat.completions.parse` rejects any object node that allows extra keys, so a bare
`dict` field anywhere in a response model fails the whole call at request time with

    Invalid schema for response_format '<Model>': In context=('properties', '<field>',
    'anyOf', '0'), 'additionalProperties' is required to be supplied and to be false.

This actually happened: a `card: Optional[dict]` added to HITLQuestion broke every
criteria-critique and judge-audit call, because HITLQuestion is embedded in both
response models. The card now lives on CardedHITLQuestion, which our own code builds
and the LLM never returns.
"""
from __future__ import annotations
import inspect

import pytest
from pydantic import BaseModel

from src.agentic import schemas as S

# Models our code constructs and hands to the UI — never returned by the LLM, so they
# are allowed to carry free-form payloads.
NOT_LLM_FACING = {"CardedHITLQuestion"}


def _llm_facing_models() -> list[type[BaseModel]]:
    out = []
    for name, obj in vars(S).items():
        if (inspect.isclass(obj) and issubclass(obj, BaseModel) and obj is not BaseModel
                and obj.__module__ == S.__name__ and name not in NOT_LLM_FACING):
            out.append(obj)
    return sorted(out, key=lambda m: m.__name__)


def _free_form_objects(node, path=("$",)) -> list[str]:
    """Object nodes that permit unspecified keys — exactly what strict mode rejects."""
    bad = []
    if isinstance(node, dict):
        if node.get("type") == "object" and "properties" not in node:
            bad.append(".".join(path))
        if node.get("additionalProperties") is True:
            bad.append(".".join(path) + " (additionalProperties=true)")
        for k, v in node.items():
            bad += _free_form_objects(v, path + (str(k),))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            bad += _free_form_objects(v, path + (str(i),))
    return bad


@pytest.mark.parametrize("model", _llm_facing_models(), ids=lambda m: m.__name__)
def test_no_free_form_dict_in_llm_schema(model):
    offenders = _free_form_objects(model.model_json_schema())
    assert not offenders, (
        f"{model.__name__} has free-form object node(s) {offenders}; OpenAI strict "
        f"parsing will reject it at request time. Move the field to a non-LLM-facing "
        f"model (see CardedHITLQuestion) or give it an explicit schema.")


def test_hitl_question_stays_card_free():
    """HITLQuestion is embedded in CriteriaCritiqueOut and JudgeAuditOut."""
    assert "card" not in S.HITLQuestion.model_fields
    assert "card" in S.CardedHITLQuestion.model_fields
    assert issubclass(S.CardedHITLQuestion, S.HITLQuestion)
