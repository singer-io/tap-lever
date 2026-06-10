# Changelog

## 1.2.0
  * Fix catalog discovery: write `table-key-properties`, `forced-replication-method`, and `valid-replication-keys` to empty breadcrumb metadata using `get_standard_metadata()`; write `parent-tap-stream-id` to empty breadcrumb metadata for child streams [#45](https://github.com/singer-io/tap-lever/pull/45)
  * Upgrade `singer-python==6.8.0`, `requests==2.34.2` [#45](https://github.com/singer-io/tap-lever/pull/45)
  * Streams that the credentials cannot access (403) are now excluded from the catalog during discovery [#46](https://github.com/singer-io/tap-lever/pull/46)

## 1.1.0
  * Libraries upgrade and tap-framework replacement [#38](https://github.com/singer-io/tap-lever/pull/38)
  * Backoff and retry implementation [#39](https://github.com/singer-io/tap-lever/pull/39)

## 1.0.0
  * Releasing GA

## 0.4.1
 * Fix opportunities bookmarking [#27](https://github.com/singer-io/tap-lever/pull/27)

## 0.4.0
 * Write all datetime fields as iso8601 date-times instead of epoch milliseconds [#25](https://github.com/singer-io/tap-lever/pull/25)

## 0.3.1
 * Add opportunityId (injected by the tap), approved, posting, sentDocument, signedDocument, signatures.candidate
 to opportunity_offers schema [#23](https://github.com/singer-io/tap-lever/pull/23)

## 0.3.0
 * Bookmark on page offset for opportunity sync [#20](https://github.com/singer-io/tap-lever/pull/20)
 * Fix error during sync if no catalog passed in

## 0.2.1
 * Write schema messages when swapping to a new stream [#18](https://github.com/singer-io/tap-lever/pull/18)

## 0.2.0
 * Move Opportunity's substreams into the sync for Opportunity [#16](https://github.com/singer-io/tap-lever/pull/16)

## 0.1.2
 * Fix exception when a candidate/opportunity does not have a resume [#14](https://github.com/singer-io/tap-lever/pull/14)

## 0.1.1
 * Remove pagination from Resume streams [#11](https://github.com/singer-io/tap-lever/pull/11)
