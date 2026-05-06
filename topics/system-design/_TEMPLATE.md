# <Topic name>

## 1. TL;DR

<2–4 sentences. State what the pattern/approach is, the operational pain it
solves, and the headline trade-off.>

## 2. How it works

<Mechanics. ASCII or mermaid diagrams where they help. State the invariants
the pattern maintains. For multi-variant patterns (e.g., "rate limiting"),
describe each variant briefly.>

## 3. When to use

<Signals in a design conversation that should make you reach for this. The
shape of problems where it pays off. Anti-signals — situations where it is
the *wrong* answer.>

## 4. Trade-offs and failure modes

<The honest list: what you give up, what breaks under load, what bites in
production. Concrete failure modes (e.g., "cache stampede on TTL expiry",
"split brain after network partition"). What you must operationally handle.>

## 5. Real-world and interviewer probes

- **In the wild:** systems that use this and how (e.g., "DynamoDB uses
  consistent hashing with virtual nodes for partition assignment").
- **Interviewer follow-ups:** the pointed questions you should expect and
  one-or-two-sentence answers that demonstrate depth.
