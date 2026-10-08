# Worked trace (Acme Shop, fictional)

A complete rca-tracer run on the invented Acme Shop system. All paths and lines
are made up to show the method.

## Symptom

A support report says: "Orders for more than 1000 units are saved with quantity
0. Smaller orders are fine."

## ROUTED

A wrong stored value points at the service or data layer, per the layer map. The
value is wrong on save, so start at `service` (order logic) and follow it down to
`data`.

Starting guess: the quantity is lost somewhere between the order request and the
database write.

## EVIDENCE_FOUND

Search the service repository for where an order quantity is written. Found:

- `service/src/orders/save.ext:54` builds the record that is handed to the data
  layer.

Reading it shows the quantity is read from a field named `qty` and copied into the
record. This concrete line on the save path gives the state EVIDENCE_FOUND.

## TRACING (hop ledger)

| # | file:line | what it does | status |
| - | --------- | ------------ | ------ |
| 1 | api/src/routes/orders.ext:31 | receives POST /orders, parses body, calls service | PASSED |
| 2 | service/src/orders/save.ext:54 | copies `qty` into the record | PASSED |
| 3 | service/src/orders/validate.ext:88 | clamps `qty` to a byte before save | FAULT |
| 4 | data/src/repositories/orders.ext:20 | writes the record as given | PASSED |

Hop 3 is the first place behavior diverges. Reading it:

```
# service/src/orders/validate.ext:88  (fictional)
record.qty = to_byte(request.qty)   # to_byte wraps values above 255
```

A quantity of 1000 wraps when forced into a byte, and the specific inputs in the
report land on a multiple that wraps to 0. Smaller orders stay under the limit, so
they are unaffected. This matches the symptom exactly.

## Five guards

1. **Read, not guessed.** `validate.ext:88` is open and quoted.
2. **Mechanism explained.** `to_byte` wraps values over 255; 1000 units wrap, and
   the reported inputs wrap to 0.
3. **Upstream clean.** Hops 1 and 2 carry the correct quantity (1000) unchanged.
4. **Downstream consistent.** Hop 4 writes whatever it is given, so the already
   wrong value reaches the database with no second break.
5. **Reproduction matches.** The report's "more than 1000 units" condition lines
   up with the wrap point.

All five hold, so the state is ROOT_CONFIRMED.

## Result

```
SYMPTOM
  Orders over 1000 units are saved with quantity 0.

RESULT
  ROOT_CONFIRMED

ROOT CAUSE
  service/src/orders/validate.ext:88 — quantity is forced into a byte with
  to_byte(), which wraps values above 255. Large quantities wrap, and the
  reported inputs wrap to 0.

TRACE
  api/src/routes/orders.ext:31          PASSED
  service/src/orders/save.ext:54        PASSED
  service/src/orders/validate.ext:88    FAULT  (root)
  data/src/repositories/orders.ext:20   PASSED

CERTAINTY
  high. The faulting line was read and quoted, the mechanism is explained, and
  the reproduction condition matches.

FIX OPTIONS
  fastest  — service/src/orders/validate.ext:88 (service): drop the to_byte call
             and keep qty as an integer. Risk: other callers may rely on the
             clamp; check them.
  safest   — service/src/orders/validate.ext:88 (service): validate qty against a
             real maximum and reject or cap with a clear error instead of
             silently wrapping. Risk: changes the error surface for oversized
             orders.
  cleanest — data schema + service (data, service): store quantity in a type wide
             enough for real order sizes and remove the byte conversion entirely.
             Risk: a schema migration is required.

OPEN QUESTIONS
  Do other call sites use to_byte on quantity? One unread lead:
  service/src/pricing/line.ext references qty and was not opened within budget.
```
