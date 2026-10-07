"""Price quotes. Each charge is a `FeeRule`, so a new charge (a weekly discount, a pet fee) is a
new class added to the rule list; `calculate_quote` itself never changes (Open/Closed)."""

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Protocol


@dataclass(frozen=True, slots=True)
class FeeContext:
    nightly_rate: int
    nights: int
    subtotal: int  # nightly_rate x nights
    cleaning_fee: int  # the listing's cleaning fee


@dataclass(frozen=True, slots=True)
class FeeLine:
    code: str
    amount: int  # whole rupees


class FeeRule(Protocol):
    def apply(self, ctx: FeeContext) -> FeeLine: ...


def percent_of(amount: int, rate: float) -> int:
    """`rate` of `amount`, rounded half-up to whole rupees (never banker's rounding)."""
    return int((Decimal(amount) * Decimal(str(rate))).quantize(Decimal(1), ROUND_HALF_UP))


class CleaningFeeRule:
    def apply(self, ctx: FeeContext) -> FeeLine:
        return FeeLine("cleaning_fee", ctx.cleaning_fee)


class ServiceFeeRule:
    """Airbnb's service fee, charged on the accommodation subtotal."""

    def __init__(self, rate: float) -> None:
        self._rate = rate

    def apply(self, ctx: FeeContext) -> FeeLine:
        return FeeLine("service_fee", percent_of(ctx.subtotal, self._rate))


class TaxRule:
    """Taxes, charged on the subtotal plus the cleaning fee."""

    def __init__(self, rate: float) -> None:
        self._rate = rate

    def apply(self, ctx: FeeContext) -> FeeLine:
        return FeeLine("taxes", percent_of(ctx.subtotal + ctx.cleaning_fee, self._rate))


def default_rules(service_fee_rate: float, tax_rate: float) -> tuple[FeeRule, ...]:
    return CleaningFeeRule(), ServiceFeeRule(service_fee_rate), TaxRule(tax_rate)


@dataclass(frozen=True, slots=True)
class Quote:
    nightly_rate: int
    nights: int
    subtotal: int
    cleaning_fee: int
    service_fee: int
    taxes: int
    total: int
    extra_fees: tuple[FeeLine, ...] = ()  # charges from any additional rules


def calculate_quote(
    nightly_rate: int, cleaning_fee: int, nights: int, rules: Sequence[FeeRule]
) -> Quote:
    ctx = FeeContext(nightly_rate, nights, nightly_rate * nights, cleaning_fee)
    lines = [rule.apply(ctx) for rule in rules]
    by_code = {line.code: line.amount for line in lines}
    known = {"cleaning_fee", "service_fee", "taxes"}
    return Quote(
        nightly_rate=nightly_rate,
        nights=nights,
        subtotal=ctx.subtotal,
        cleaning_fee=by_code.get("cleaning_fee", 0),
        service_fee=by_code.get("service_fee", 0),
        taxes=by_code.get("taxes", 0),
        total=ctx.subtotal + sum(line.amount for line in lines),
        extra_fees=tuple(line for line in lines if line.code not in known),
    )
