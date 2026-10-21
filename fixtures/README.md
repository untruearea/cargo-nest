# Fixture provenance

`input.json` is an original, fictional, non-PII fixture under the package MIT license. Its byte length is 437 and SHA256 is `6a88b716830a277a6acdb383ab42dbc510f0e5d71f208c753afe02f0a7412edd`. It uses LF UTF8 without BOM; publishing must preserve those exact bytes. `source.json.test_url` is only a synthetic mocked HTTP test locator. There is no published fixture URL yet.

`studio-constructor-reference.json` is a minimal public receipt-shape reference copied from the parent-observed Studio61999 constructor evidence. Its provenance field records the actual observation. Its hash/address are neither this project's deployment nor business-flow proof; do not configure them as such. It is used only for adapter/helper/formatter tests. Public RPC transport is mocked during local frontend tests.
