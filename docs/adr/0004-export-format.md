# ADR 0004: Bill-Ready Export Generation & Architecture

## Status
Accepted

## Context
NEXORA Order Agent is not an ERP; it is an intelligent capture layer that feeds wholesalers' existing billing software (e.g., Vyapar, Busy, Tally, Zoho Inventory). The export mechanism must ensure:
1. Approval generates the export asynchronously without blocking HTTP response time.
2. An order is never lost or modified if an export tool has temporary disk/network latency.
3. Accounting software formats require exact line item SKUs, units, tax breakdowns, and totals.

## Decision
1. **Snapshotted Order Items:**
   - At approval time, the draft lines are frozen into `order_items` (`product_code`, `product_name`, `qty`, `unit`, `unit_price`, `line_total`).
   - Downstream catalogue changes or price updates never mutate historical order records.
2. **Background Worker Export Generation:**
   - Approval inserts `exports` with `status = 'pending'` and enqueues task `generate_export`.
   - `worker_role` has `SELECT` permission on `orders` and `order_items` to generate the file, write to disk, and update `exports` status to `'ready'` with `file_path`.
   - `worker_role` has zero write access to `orders` and `order_items`, preserving non-negotiable rule R2.
3. **Download Endpoint:**
   - `GET /api/v1/orders/{id}/export` streams the pre-generated file from storage.
   - If export generation failed, `POST /api/v1/orders/{id}/retry-export` re-enqueues the generation job.

## Consequences
- Guaranteed file durability and audit consistency.
- Instant HTTP approval response while heavy CSV/PDF file formatting occurs asynchronously.
