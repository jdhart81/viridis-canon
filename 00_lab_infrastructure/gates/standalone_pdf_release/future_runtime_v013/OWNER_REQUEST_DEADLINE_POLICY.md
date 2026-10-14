# V013 declared-content request deadline policy

This reviewed successor changes the scoped health OWNER transport allowance.
It preserves V012 and its actual 120-second failure as immutable history. It is
not an admission, a network remedy claim or a waiver of an existing result.

Metadata requests retain 120 seconds. Every content request uses the strict
positive integer size from the complete source-bound 100-file allowlist:
`min(600, max(120, 30 + (expected_bytes + 65535) // 65536))` seconds. The formula
uses declared exact bytes; filenames, HTTP Content-Length and received bytes do
not select the allowance. Thus 5,898,240 bytes gets 120, one more gets 121,
30,500,744 bytes gets 496, and the maximum is 600.

The actual catalog first OWNER invocation still starts one 900-second clock.
Each job starts before subprocess/bootstrap/DNS/TLS/header/body work and uses
`min(actual_request_start + allowance, actual_first_owner_invocation + 900)`.
Protocol2 retains the policy, integer allowance, actual first clock, operation
deadline and job deadline. The child has a bounded 600-second initial HELLO cap,
then authenticates and uses that same absolute job deadline without restarting
it. Worker source verification, full body transfer, source-finally and actual normal
wait must all fit. Successful records and the actual health timing retain these
values for independent reconstruction from the source-bound correction sizes.
The preliminary master source guard remains at its existing position before the
request-start sample; production catalog invocation already places that work
inside the shared 900-second operation window.

The complete 14 authenticated metadata views, 100 content requests, 35 one-use
scientific jobs, full bytes/SHA256/MD5/HTTP200, original scientific predicates,
19-source checks, full input guards, owned pipes, token confinement, global 2.05
header-ACK spacing, max 6 children, cancellation and reaping remain required.
The 900 operation, 2940 internal cleanup and 3000 external master limits do not
change. Outside scoped health-prefetch, the inherited direct download fallback
retains its existing 120-second behavior. Actual full installed health and source
readback remain pending; no partial-request or earlier-version result is PASS.
