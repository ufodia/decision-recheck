# Third-party notices

Decision Recheck's original source, documentation, fixtures, and vector artwork are licensed under the MIT license, copyright 2026 ufodia. Dependencies remain the work of their respective authors and retain their licenses and notices.

The authoritative dependency versions are in `uv.lock`. Installing the project retrieves dependencies separately; the repository does not vendor or relicense their implementations.

| Direct dependency | Role | License | Upstream |
| --- | --- | --- | --- |
| FreshCtx | Declared evidence dependencies and freshness checks | Apache-2.0 | <https://github.com/Hyperwise-LLC/freshctx> |
| Playwright for Python | Isolated browser sessions and traces | Apache-2.0 | <https://github.com/microsoft/playwright-python> |
| Pydantic | Structured record validation | MIT | <https://github.com/pydantic/pydantic> |
| HTTPX | Bounded HTTP access | BSD-3-Clause | <https://github.com/encode/httpx> |
| HTTP Core | Pinned network backend used by bounded HTTP access | BSD-3-Clause | <https://github.com/encode/httpcore> |

Development dependencies, build tools, and transitive packages retain their upstream terms. Browser binaries have their own notices. Review the installed distribution metadata before redistributing a bundled environment.

FreshCtx is an upstream dependency, not a Decision Recheck invention. Project names identify integration surfaces and do not imply endorsement. No competitor implementation is included or relicensed here.
