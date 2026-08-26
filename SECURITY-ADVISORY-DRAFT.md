# Draft Security Advisory

**Status:** Draft for maintainer review

## Title

Potential server-side request abuse through externally sourced post media and
search enrichment

## Affected component

`post_analysis.py`, specifically `analyze_post()` and `_request()`.

## Description

The post-analysis flow fetches a validated public Instagram URL, extracts the
`og:image` value from the returned HTML, and then fetches that image URL. It also
performs outbound requests to configured search providers. Requests follow
normal HTTP redirects and use a fixed timeout, but the application does not
apply an explicit destination allowlist to extracted image URLs or redirects.

If the deployed service can be induced to process attacker-controlled metadata,
an attacker may be able to cause server-side requests to unintended destinations
or consume outbound request resources. The practical impact depends on the
network location of the Streamlit host, proxy behavior, egress controls, and the
actual metadata returned by the upstream page.

## Impact

Potential confidentiality impact from reaching internal services, plus resource
exhaustion or unexpected third-party requests. No impact is established for the
local-only SDK path, and this draft does not assert that the public hosted app is
exploitable without deployment-specific testing.

## Severity

**To be assessed.** A CVSS score should be assigned only after confirming the
deployment topology, redirect behavior, reachable address ranges, and whether
responses are exposed to the requester.

## Preconditions

- The service is deployed with outbound network access.
- An attacker can submit URLs or cause the service to process attacker-influenced
  public metadata.
- The deployment does not block private, loopback, link-local, or other unwanted
  destination ranges at the network layer.

## Recommended remediation

1. Validate every extracted image URL before requesting it.
2. Resolve hostnames and reject loopback, private, link-local, metadata-service,
   multicast, and reserved IP ranges for every redirect hop.
3. Allow only `https` image requests and enforce response-size and content-type
   limits before image decoding.
4. Apply per-request and per-user rate limits, bounded response bodies, and
   restrictive egress firewall rules.
5. Keep provider API keys server-side and redact upstream exception details from
   end-user responses.
6. Add tests covering redirects, private IP literals, DNS rebinding, oversized
   responses, and unsupported content types.

## Verification plan

Before publication, test the deployed service in an isolated environment with
non-sensitive canary endpoints and confirm that blocked destinations are not
requested. Record the deployment configuration, affected versions, fix commit,
and regression-test results before converting this draft into a GitHub Security
Advisory.

## Disclosure notes

This is a maintainer draft, not a confirmed vulnerability announcement. Do not
publish exploit details or assign a CVE until impact has been verified against a
specific deployed version.