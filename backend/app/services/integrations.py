from typing import Dict, List

DEFAULT_INTEGRATIONS: List[Dict[str, str]] = [
    {
        "provider_key": "email_smtp_resend",
        "category": "email",
        "name": "Transactional Email Provider (SMTP / Resend)",
        "description": "Deliver verification emails, invitations and approved order summaries.",
    },
    {
        "provider_key": "whatsapp_cloud",
        "category": "messaging",
        "name": "WhatsApp Business Messaging Connector",
        "description": "Ingest retailer messages and dispatch operator-approved order confirmations.",
    },
    {
        "provider_key": "razorpay_india",
        "category": "payments",
        "name": "Razorpay Payment Links (India)",
        "description": "Generate payment requests tied cleanly to confirmed order IDs.",
    },
    {
        "provider_key": "tally_zoho_books",
        "category": "accounting",
        "name": "Accounting Ledger Export (CSV / Vyapar / Tally)",
        "description": "Export reconciled order totals, tax summaries and SKU lines for bookkeeping.",
    },
    {
        "provider_key": "external_crm_sync",
        "category": "crm",
        "name": "External CRM Import / Sync Adapter",
        "description": "Migrate legacy contacts and leads cleanly into tenant-isolated CRM tables.",
    },
    {
        "provider_key": "webhook_outbound",
        "category": "api",
        "name": "Signed Outbound Business Webhooks",
        "description": "Emit HMAC-signed order and inventory events to downstream ERP endpoints.",
    },
]
