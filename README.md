# Smart Fitness Session Analyzer — Option A

## Files

- `fitness_session_analyzer.py` — the domain model: classes, validation, and analysis logic.
- `run_generated_scenarios.py` — imports the supplied `data_generator.py` and runs every
  scenario it can produce through the analyzer above.
- `data_generator.py` — supplied by the instructor, unmodified.

Run with:

```
python3 run_generated_scenarios.py
```

## How the problem is represented

### Domain classes

- **`ReferenceMeasurements`** — a participant's personal baseline (`heart_rate`,
  `skin_response`, `temperature`). `heart_rate` is exposed through a `@property` with a
  setter that rejects anything outside 30–150 bpm, so a baseline can never be constructed
  in an invalid state.
- **`Participant`** — holds a name/ID and *has a* `ReferenceMeasurements` object. This is
  composition: a participant's baseline is a distinct object, not a handful of loose
  attributes bolted onto `Participant` itself.
- **`Observation`** — one accepted sensor reading. Built directly from a validated
  dictionary via `self.__dict__.update(data)`, so its attributes (`timestamp`,
  `heart_rate`, …) match the generator's field names exactly, with no manual mapping.
- **`RejectedObservation`** — a subclass of `Observation` that overrides `usable()` to
  return `False` and stores only a rejection `reason` instead of the reading itself. This
  is the one place inheritance is used: both classes support the same `usable()`
  interface, so the rest of the program never has to check "is this a normal or a
  rejected reading?" with an `if/else` — it just calls `.usable()`.
- **`FitnessSession`** — *has a* `Participant` and a list of `Observation`/
  `RejectedObservation` objects (composition again). It owns the accept/reject split and
  the final analysis.

### Deciding accept vs. reject

`Observation.from_dict(data)` is a `classmethod` used as a factory: it runs `validate(data)`
first, and returns a `RejectedObservation` if validation fails, or a normal `Observation`
otherwise. Centralizing this decision in one factory method means `FitnessSession.add()`
never needs to know the difference — it just calls `Observation.from_dict(data)` and
appends whatever comes back.

`validate()` itself is a plain function, not a method, because it doesn't need any state
from a class — it's a pure check: are all required fields present, are they all numeric,
and does each fall inside its documented range (e.g. `30 <= heart_rate <= 230`)? Keeping
it as a free function makes it independently testable and reusable.

### Summarizing and classifying a session

`summary()`, `compare()`, `recovery()`, and `classify()` are also free functions rather
than methods on `FitnessSession`, because each does one well-defined calculation on data
it's handed, with no need to reach into the session's internal state:

- `summary()` computes avg/min/max per field across the usable readings.
- `compare()` subtracts the participant's baseline from those averages.
- `recovery()` splits the session into thirds and checks whether heart rate *and*
  activity level both drop by a meaningful margin (≥8 bpm, ≥0.15 activity) between the
  middle third and the final third.
- `classify()` turns the above into one of five labels: `resting`, `moderate activity`,
  `high activity`, `recovering`, or (handled separately in `FitnessSession.analyse()`)
  `insufficient data` when fewer than 3 usable readings remain.

`FitnessSession.analyse()` is the one method that ties these together: split observations
into usable/rejected, bail out early with `insufficient data` if there aren't enough
usable readings, otherwise run `summary()` → `compare()` → `recovery()` → `classify()` and
return one result dictionary containing the classification, the reason for it, the usable
count, and the list of rejection reasons.

### Reporting

`report()` prints that result dictionary in a human-readable form: the classification,
why it was chosen, the heart-rate summary, and any rejected readings with their reasons.

## Design choices worth calling out

- **Why a classmethod factory instead of `try/except` in `FitnessSession.add()`?**
  Keeping the decision inside `Observation.from_dict()` means the validation rules live
  in exactly one place, and any future observation type (e.g. a "flagged but usable"
  reading) only requires a new subclass, not changes to `FitnessSession`.
- **Why a `@property` on `ReferenceMeasurements.heart_rate` but not on the other two
  baseline fields?** Heart rate is the one baseline value used in every classification
  decision (`compare()`, `classify()`), so guarding it against being constructed outside a
  sane range (30–150 bpm) protects the analysis from a bad baseline, not just bad
  readings.
- **Why is minimum-readings (3) a class attribute rather than a magic number buried in
  `analyse()`?** `FitnessSession.MIN_READINGS = 3` documents the threshold in one place
  and makes it trivial to override for a subclass or a different session type later.

## Scenario coverage

Running `run_generated_scenarios.py` exercises all five scenarios the generator can
produce, which line up with the assignment's five minimum scenarios:

| Generator scenario | Expected classification |
|---|---|
| `resting` | resting |
| `moderate_activity` | moderate activity |
| `high_activity` | high activity |
| `recovery` | recovering |
| `poor_quality` | insufficient data |

Note on `poor_quality`: the generator's issue-injection (`timestamp % 4`) corrupts
*every* observation in that scenario across four failure types (missing heart rate, an
impossible heart rate, a negative activity level, or missing skin response), so `analyse()`
correctly rejects all of them and returns `insufficient data`. This still exercises every
branch of `validate()`'s rejection logic even though no single reading from that scenario
survives.
