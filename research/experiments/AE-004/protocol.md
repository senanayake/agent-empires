# AE-004 bounded protocol

Written before behavioral tests and implementation. Author self-review only.
Use the checkout's locked CPython 3.12.13 environment. No new dependencies.

Question: can holdings preserve information access independently of actor names,
human/agent labels, document existence, and private scenario/audit retention?
Falsifiers: a departed sole holder remains readable, an unreadable document saves
availability, a redundant reachable holding is lost, or a source reference grants
access to hidden content. No numeric calibration or participant claims.

Use three holders: two actors on different teams and one document. The authored
JSON fixture includes a sole tacit rationale, redundant policy, unreadable item,
stale/conflicting claims and shared source labels. Tick values are arbitrary
engineering ordering units. No stochastic rule or seed is needed for access;
exhaustively vary the three holders' accessibility as a small invariant check.

Record focused missing-API red before implementing, then green. Check departure,
artifact survival, no automatic team sharing, organization loss versus team
unreachability, immutable old facts/views, item versions, shared provenance,
invalid references/commands and failure atomicity. Relabel kinds/names and move
holdings to test causal identity independence. Replay the fixture in fresh state
and reversed registration order; compare canonical history bytes.

Keep all actual command failures. Produce source-bound results with an experiment
runner supporting fresh `--output-dir` and read-only `--verify-against`. Review
MA-02/03 and update their bounded evidence. Communication, learning rules, actor
psychology, complete replacement and hostile-code isolation remain later work.
