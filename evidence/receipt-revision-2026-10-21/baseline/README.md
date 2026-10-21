# CargoNest

A complete local GenLayer Project candidate for planning a small **fictional, non-PII** set of indivisible parcels into the minimum number of abstract containers. Its interface displays each parcel, forbidden pair, per-container weight/volume meter and exact assignment. It does not certify physical dimensions, geometric fit, safe carriage, real inventory, dispatch or delivery.

## Deterministic core

Strict JSON is `{version:1,capacity:{weight,volume},max_bins,parcels:[{id,weight,volume}],incompatible:[[id,id]]}`. There are1..8 parcels with unique ASCII IDs `[A-Za-z][A-Za-z0-9_-]{0,23}`; capacity and parcel dimensions are positive exact integers1..1000000; max_bins1..8. At most28 known distinct normalized pairs are permitted; reversed duplicates, self-pairs, unknown IDs, booleans, floats, extra fields, duplicate JSON keys and nonfinite constants fail. The UTF8 body is1..16384 bytes.

The contract sorts parcel IDs in ASCII order and enumerates restricted-growth set partitions, checking both capacities and every blocked pair. At most Bell(8)=4140 complete partitions exist. It minimizes container count and then the lexicographic assignment vector; introducing only the next container number removes label permutations. Every parcel occurs exactly once. Infeasible manifests return `INFEASIBLE` with empty assignments/containers and cannot be confirmed. The frontend never substitutes a host-side packing heuristic for chain output.

The fixture a(6,3), b(4,7), c(5,4), d(5,6), capacity(10,10), max3 and forbidden a/c gives two containers with assignment[0,0,1,1]. Publication must preserve the exact LF bytes; see `fixtures/source.json`. Its test URL is an explicitly mocked synthetic locator, never a real published source. The fixture public URL remains null.

## Workflow and API

| Method | Effect |
|---|---|
| `open_load(load_id,source_url,source_sha256)` | Creator locks a strict manifest; OPEN revision0 |
| `pack_load(load_id,expected_revision)` | Permissionless fresh exact partition; PACKED revision1, result and certificate |
| `confirm_load(load_id,expected_revision,certificate_id)` | Creator freshly recomputes a FEASIBLE plan; CONFIRMED revision2 |
| `revoke_load(load_id,expected_revision,reason)` | Creator terminal revocation, revision+1; trimmed reason1..160 chars |
| `get_load(load_id)` | Decoded dictionary with source, manifest, complete partition, captures, certificate and history |
| `get_configuration()` | Bounds and physical-dispatch-unverified scope |

Demo: publish the byte-exact fixture to a real public GitHub commit; deploy `contract.py` with `[]`; enter its actual address, a unique load ID, the real pinned URL and fixture SHA; open, read, pack, inspect capacity totals and forbidden-pair separation, and creator-confirm the displayed feasible certificate. Revoke separately if desired. Oversized parcels or too few allowed containers produce an inspectable infeasible result. Reusing IDs, stale revisions, other creators, cross-record certificates and repeated confirmation fail.

## Shared protocol and source boundaries

The constructor has **zero arguments**. A creator locks a never-reusable ID, source locator and exact byte SHA256; any participant may derive a result once. Only that creator can confirm the current certificate or revoke the record. Every subsequent write uses an expected revision, confirmation also requires the exact certificate ID, and revocation is terminal. Failed fetching, validation or computation changes no stored state. Offline revocation works even when the source is unavailable. Revoked results remain visible as historical evidence.

The source must be `https://raw.githubusercontent.com/OWNER/REPO/40-lowercase-hex-commit/PATH`. Owner boundaries, repository dot segments and every path segment are checked explicitly; query strings, encoded paths, credentials, empty segments, `.` and `..` are rejected. This grammar does not authenticate a publisher or attest DNS, redirects, TLS or GitHub transport behavior. HTTP200, exact body bounds, strict UTF8, exact SHA256 and strict duplicate-key-rejecting JSON are mandatory. Availability or changed bytes cause failure, not an inferred answer. Never publish personal data or secrets: input and chain records are public.

For opening, derivation and confirmation, leader and validators each fetch fresh bytes independently. At derivation/confirmation they each recompute the complete deterministic result. The validator compares the whole canonical packet: protocol, chain, contract, creator, ID, locked URL/hash, revision, operation, observation time, input and result. It rejects a non-return, exception or any disagreement. No LLM is used. A certificate is the SHA256 of the complete derivation packet; confirmation preserves that certificate and stores a new full capture. The observation time is chain-message time, not proof of when the publisher created the data. No ongoing freshness or real-world truth is promised.

## Frontend and receipt recovery

The complete frontend starts **unconfigured**: deployment, published fixture and hosting URLs are null. Enter an actual deployed address and a published commit-pinned source with its exact byte hash. Connect MetaMask through the SDK wallet provider on **Studio61999**. Incorrect networks require the normal wallet network switch; writes are zero-value and there is no backend, key custody or external effect.

A write submits once and saves the hash plus original sender, target and zero value in browser localStorage. It requests the real SDK `waitForTransactionReceipt({waitUntil:'finalized',fullTransaction:true})`, then independently inspects the exact public `eth_getTransactionByHash` receipt. Completion requires raw `FINALIZED`, matching hash/from/to/value0, `execution_mode:NORMAL`, `leader_only:false`, `result_name:MAJORITY_AGREE` and exactly one leader-mode receipt with `execution_result:SUCCESS`. Nonfatal validator `IDLE` votes do not imply leader failure. Multiple leader entries are conservatively unresolved because this adapter cannot prove their current-round identity.

Present SDK identity, value, finality and execution fields must agree. The pinned SDK Studio branch can omit train execution fields, and its viem formatter drops raw numeric zero `value`; actual non-mocked helper/formatter regressions reproduce both facts. Missing fields or an SDK observation exception are **not manufactured into SDK success**: only the independently strict raw receipt can complete that submission. Missing, failed, pending, conflicting or ambiguous evidence retains the exact hash and blocks further writes. The inspector can recover it without a second submission, using the original saved context even if the address/account fields change. The UI intentionally provides no discard/retry control for a failed tracked transaction; operator review is required. A broadcast that fails before the wallet/SDK returns a hash cannot be recovered automatically. Browser storage is a cooperative local recovery aid, not a tamper-resistant ledger; retain the ID if storage is unavailable.

Read occurs only after proven success. Dictionary-valued SDK views are consumed as decoded dictionaries, not JSON strings. Editing the visible record ID or deployment clears the loaded record; write gates and handler checks bind the visible ID to the loaded ID. Account/network changes disconnect the UI and clear its record. Old source data and results stay visible with their status; confirmation is not silently assumed.

## Run and verify

From this package directory, with the pinned Python requirements installed:

```powershell
python tools/verify.py
cd frontend
pnpm install --frozen-lockfile
pnpm test
pnpm build
pnpm dev
```

`tools/verify.py` selects exact GenVM **v0.2.12**, runs the actual deployed Python SDK contract tests and full semantic lint/schema, and writes stdout to `evidence/verification-*.log`. Use the package as cwd: upstream gltest clears its cwd `artifacts/`. The narrow Windows test fixture defers upstream message-file unlink until teardown and synchronizes upstream warp message datetime; it never replaces contract computation or validator logic. Test HTTP responses are mocked transport bytes; production code fetches public sources. `pnpm build` runs TypeScript checking and Vite. The nonfatal large SDK chunk warning is retained. `tools/verify_frontend.py` reproduces frontend checks and binds all input hashes.

Frontend transport adapter tests mock wallet/RPC calls and execute real production adapters; the public constructor receipt fixture additionally exercises the actual SDK helper and actual viem formatter. That receipt belongs to another publicly observed constructor and is **not either project's deployment or business-method success**. No browser UI test, live source capture, deployed business flow, usage, adoption, audit, reward, financing or production readiness is claimed.

## Release and provenance

MIT license. The dedicated algorithm, state API, fixtures, domain tests and product UI are original for this application. SDK connection/receipt infrastructure and the exact SDK verification scaffold are shared development infrastructure, not separate contributions. Each Project is counted once; its contract is not also submitted as an independent IC. `CONTRIBUTION.json`, `PUBLISH_MANIFEST.json`, `PACKAGE_CONTENTS.json` and evidence record the candidate hashes and null live metadata. ZIPs omit node_modules, dist, SDK caches, artifacts and all credentials. Public fixture URLs and deployment addresses must be recorded only after actual publication/deployment and verification.

Primary SDK references: [transactions](https://docs.genlayer.com/api-references/genlayer-js/transactions), [equivalence principle](https://docs.genlayer.com/developers/intelligent-contracts/equivalence-principle), [execution and fee outcomes](https://docs.genlayer.com/developers/decentralized-applications/fee-outcomes-and-debugging), [SDK source](https://github.com/genlayerlabs/genlayer-js). Frontend pins genlayer-js2.0.0-rc.2; compatibility evidence is local and based on the public Studio constructor shape, not a live end-to-end attestation.

Verification at candidate freeze: **37 Python tests (36 actual contract/validator cases plus one exact fixture-metadata integrity case), 49 frontend tests; exact full semantic lint/schema and TypeScript/Vite exit0**. Source SHA256: `d92ff68e72d99fd8df39fa7441a10cb1d2613b18eb1189de0d9411312db854c6`. See raw logs for actual red/green history. Independent peer review is recorded separately; this is not an external security audit.
