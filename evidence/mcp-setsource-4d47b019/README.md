# Exact MCP setSource repair evidence

This branch is **evidence-only**. Never merge it into product master.
Publication is authorised by Pine Controller directive 5972452816.
External upstream is read-only and has not been pushed or reconfigured.

## Identity
- MCP commit: `4d47b019a41617d238c51a9280bee1e4ec7eeec0`
- Required upstream parent: `01c193ada6a115a6e33fa594063f91fbf291ed09`
- Tree: `070a41c4f179b92f6dafb316ce4a22c629bcd7e2`
- Bundle SHA256: `327330f2bb978fd1e5a220694a3e745eccb9416ac1644897ce5ac6f404a7b48c`
- Read-only upstream: https://github.com/LewisWJackson/tradingview-mcp-jackson.git

## Independent recovery
Use a NEW disposable repository, not the operator's dirty MCP checkout.
Paths below are examples; resolve bundle to an absolute native path on Windows.

```sh
git init recovered-mcp
git -C recovered-mcp fetch --depth=1 https://github.com/LewisWJackson/tradingview-mcp-jackson.git 01c193ada6a115a6e33fa594063f91fbf291ed09
git -C recovered-mcp bundle verify /absolute/path/mcp-4d47b019.bundle
git -C recovered-mcp bundle list-heads /absolute/path/mcp-4d47b019.bundle
git -C recovered-mcp fetch /absolute/path/mcp-4d47b019.bundle HEAD:refs/heads/recovered
git -C recovered-mcp switch recovered
git -C recovered-mcp rev-parse HEAD HEAD^{tree}
```

Require exact commit/tree identities above and per-file blob/SHA256 identities in
`attestation.json`. SHA256 of Git blob bytes is portable; Windows checkout bytes
can differ due to CRLF conversion and are recorded separately.
Run `node --check src/core/pine.js`, `node --test tests/pine_set_source.test.js`,
and `node --test tests/pine_analyze.test.js` in the recovered repository.
Tests in pine_analyze include read-only Pine facade compilation requests.
They do not modify the live chart/editor. Dependency installation, if needed,
is separate from recovered-source identity.

`commit.patch` is the complete full-index binary/stat/patch output for this exact
commit. The thin bundle preserves the original Git commit, metadata, tree and
blobs; it is not a full upstream backup and requires the stated prerequisite.
Nothing here authorises live trading, chart/editor mutations, upstream pushes,
or publication to product master.
