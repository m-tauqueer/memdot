"""Parser-neutral normalization and promotion gates."""

from __future__ import annotations

import uuid

from memdot_domain.ports.parser import NormalizedElement, ParseResult


def validate_parse_result(result: ParseResult) -> tuple[str, ...]:
    errors: list[str] = []
    seen_ids: set[uuid.UUID] = set()
    for element in result.elements:
        if element.element_id in seen_ids:
            errors.append("duplicate_element_id")
        seen_ids.add(element.element_id)
        if not element.exact_text and element.kind.value not in {"figure", "asset"}:
            errors.append("empty_element_text")
        if element.order_index < 0:
            errors.append("invalid_element_order")
    if result.quality_score < 0.3:
        errors.append("quality_below_threshold")
    return tuple(errors)


def referential_integrity(elements: tuple[NormalizedElement, ...]) -> bool:
    ids = {element.element_id for element in elements}
    for element in elements:
        if element.parent_element_id is not None and element.parent_element_id not in ids:
            return False
    return True
