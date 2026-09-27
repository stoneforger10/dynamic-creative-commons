# DynamicCreativeCommons

DynamicCreativeCommons is a structural evolution layer for collaborative creative compositions on GenLayer. It stores content-addressed element references, typed relations, compositions, and immutable version snapshots.

It does not decide copyright ownership, authorship, originality, artistic quality, popularity, or licensing. A reference hash is only a pointer to an application-managed asset; it is not an ownership claim.

## Consensus boundary

The contract owns the minimum state transition that needs consensus: a parent-bound `REARRANGE` or `CREATE_VARIATION` evolution. The leader and validators independently reconstruct the full result from persisted space state and exact proposal fields. Equality covers the operation, parent root, composition membership, payload, resulting composition map, and deterministic result root.

## Lifecycle

```text
CREATED -> ACTIVE -> PROPOSED -> APPLIED
                         |-> REJECTED
                         |-> STALE
                         |-> EXPIRED
```

Applied versions and snapshots are append-only. Owner checks, exact parent roots, unique IDs, bounded element lists, terminal evolution states, and exact validator reports prevent replay and payload substitution.

## API

- `create_space`
- `register_element`
- `connect_elements`
- `create_composition`
- `propose_evolution`
- `apply_evolution`
- `get_space`, `get_evolution`, `get_record`, `get_snapshot`

The first release intentionally bounds transformations to `REARRANGE` and `CREATE_VARIATION`. Both preserve element identity and reject missing or duplicated members.

## Development

```powershell
genlayer network set studionet
genvm-lint check contracts/DynamicCreativeCommons.py --json
genlayer deploy --contract contracts/DynamicCreativeCommons.py
```

StudioNet is gasless. Treat only `FINALIZED` receipts with successful leader execution as deployment or lifecycle proof.

## Scope

This is creative infrastructure, not a legal or media-rights oracle. Applications needing rights enforcement must add a separately reviewed licensing and evidence layer.

## License

MIT
