# Verification vectors

1. Register two elements, create a composition, propose a rearrangement with the same members, and apply it.
2. Create a variation and assert version advancement and an immutable snapshot.
3. Attempt a rearrangement with a missing member; proposal creation must fail.
4. Attempt to reuse an evolution ID; it must fail.
5. Attempt a cross-space or stale-parent application; it must not advance the head.
