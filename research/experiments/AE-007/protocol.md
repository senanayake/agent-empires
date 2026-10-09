# AE-007 headless composition protocol

Saved before executing the new probe or analyzing its results. Question: do the
existing clock, holdings, channels, authority and decisions compose without
conflating closure, permission and evidence, sufficiently to author AE-008 inputs?
This is a structural toy-model gate, not architecture or PaymentCo acceptance.

Run six small command strategies at seeds **7, 19, 31**: unsupported closure;
delayed clarification plus delegated authority; sole-holder departure before
clarification; the same departure after a surviving transfer; harmless unsupported
choice with an authored inconclusive benign observation; authorized policy with
an authored challenge. Each uses three holders, one fixed decision profile and
one question. Repeat every complete history and replace every human label with
agent (and conversely) while keeping IDs, profiles, holdings and commands fixed.
Compare the lost/surviving pair; no larger scenario or world engine is introduced.

Controls: channel latency 1 tick, capacity 1 message/tick, loss/distortion 0,
transfer cost 1 toy unit, connection cost 0; all invented boundary controls under
MA-04, not calibrated. Seeds exercise keyed transfer draws, not a statistical
sample. Decision preferences and high confidence are fixed MA-05 toy inputs.
Authority scopes/options and evidence stance/quality/roots are explicit trusted
metadata under MA-02/06/09; no correctness flag or hidden answer may guide policy.
Record all initial setup, command arguments/order, scheduled deliveries, snapshots,
immutable decision versions, event histories and typed causal parents. Parentless
facts must be traced to explicit external/setup commands. Registration changes
without events are recorded as commands, never presented as event-sourced state.

Falsifiers: inference/delegation manufacture evidence coverage; private/lost
holdings can be consumed; a send instantly grants knowledge; a transferred copy
loses ancestry; authority prevents challenge; an unsupported choice forces harm;
matched labels alter histories; replay differs; unexplained state changes or a
forbidden simulation import. A wrong-actor grant attempt must reject atomically.
Benign and challenging observations are authored counterexamples, **not simulated
payment results**. Lack of an incident event proves no safety claim. Coverage
counts declared usable roots per question, not truth, entropy or learning.

Save `results.json`, `run-manifest.json`, `timing.json`; preserve failed tests and
commands alongside them. Pin source/protocol/lock hashes, CPython 3.12.13 and
pytest version. A full probe has a 30-second engineering budget (invented under
MA-14; uncertainty: host load; alternative: revisit AE-033), below the packet's
300-second command timeout. Timings are measured anew and budget-checked, never
compared byte-for-byte. `--verify-against` reruns into temporary storage, compares
canonical results/manifests and never writes into the evidence directory.
Existing authored result files are refused, including partial output sets.

Commands from checkout root after locked uv sync and venv activation:

```bash
python3 -m pytest -q tests/simulation/test_headless_probe.py
python3 experiments/headless_probe.py --output-dir research/experiments/AE-007
python3 experiments/headless_probe.py --verify-against research/experiments/AE-007
python3 scripts/check_campaign.py --activity AE-007
git diff --check
```

Worker self-review must choose pass, narrow, replan or stop after reading all
traces, causal parents, controls and limitations. A pass permits recommending
AE-008 only; negative dispositions require bounded replanning. Preserve unsupported
claims, failed seeds and negative checks. No participants exist in this protocol.
