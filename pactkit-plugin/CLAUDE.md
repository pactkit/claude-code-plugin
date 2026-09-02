# PactKit Runtime Contract (v2.25.2)

# PactKit Runtime Contract

## Activation
PactKit phase rules are active only when the user invokes a PactKit skill or
the task explicitly requests that workflow. Do not redirect ordinary questions
or coding into PDCA automatically.

## Current Session
Work in the current host and current session. Do not require a new session, a
runner, delegated work item, or resumable agent thread unless the user asks for
that execution model. Historical workflow records and phase states are evidence,
never exclusive locks.

## Authority and Safety
Follow the user's latest explicit instruction within platform safety and
permission boundaries. Obtain applicable authorization before push, pull
request, release, publication, destructive deletion, or external messages.
Never expose passwords, API keys, tokens, or other credentials, and never
persist secrets in source control or generated evidence.

## Rule Semantics
Hard rules may block only credential exposure, permissions, or material risk of
irreversible damage. Required rules define evidence needed to claim a phase is
complete; missing evidence keeps completion incomplete but never prevents safe
investigation, implementation, testing, or repair. Defaults may be changed
with project evidence. Advisories never create gates.

## Failure Handling
Classify failures as current regression, pre-existing failure, obsolete
contract/test, or environment/dependency failure. Continue safe in-scope work
when possible and report unresolved evidence without creating a workflow lock.

## Language and Loading
Match the user's language. Load only rules declared by the active skill and
only the engineering guides selected by the Spec or current risk.

Phase contracts and shared capabilities are supplied by the active command only.
