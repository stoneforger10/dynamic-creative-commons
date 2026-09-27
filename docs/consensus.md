# Consensus

`apply_evolution` computes a complete report from persisted state. The validator calls the same report independently and requires exact calldata equality. The report includes the complete composition map, not only an approval flag, so a validator cannot accept an altered member list or variation payload.
