from app.domain.pricing import FeeContext, FeeLine, calculate_quote, default_rules

RULES = default_rules(service_fee_rate=0.14, tax_rate=0.12)


def test_quote_3_nights():
    q = calculate_quote(nightly_rate=5000, cleaning_fee=1500, nights=3, rules=RULES)
    assert (q.subtotal, q.cleaning_fee, q.service_fee, q.taxes, q.total) == (
        15000,
        1500,
        2100,
        1980,
        20580,
    )


def test_quote_rounding_is_half_up_not_bankers():
    # 14% of 1175 is exactly 164.5: half-up gives 165 (banker's rounding would give 164)
    q = calculate_quote(nightly_rate=1175, cleaning_fee=0, nights=1, rules=RULES)
    assert q.service_fee == 165
    assert q.total == 1175 + 165 + 141


def test_a_new_charge_is_just_another_rule():
    """Open/Closed: adding a pet fee needs a new rule class, not a change to calculate_quote."""

    class PetFee:
        def apply(self, ctx: FeeContext) -> FeeLine:
            return FeeLine("pet_fee", 300)

    q = calculate_quote(5000, 1500, 3, [*RULES, PetFee()])
    assert q.extra_fees == (FeeLine("pet_fee", 300),)
    assert q.total == 20580 + 300
