"""UPI URL building and helpers."""

from __future__ import annotations

import warnings
from urllib.parse import quote, urlencode


def build_upi_deep_link(
    *,
    vpa: str,
    payee_name: str,
    amount: float,
    txn_id: str,
    note: str,
) -> str:
    UPI_AMOUNT_TYPICAL_LIMIT = 100_000
    if amount > UPI_AMOUNT_TYPICAL_LIMIT:
        warnings.warn(
            f"Amount \u20b9{amount:,.2f} exceeds the typical UPI per-transaction "
            f"limit of \u20b9{UPI_AMOUNT_TYPICAL_LIMIT:,}. The generated QR may fail on scan.",
            stacklevel=2,
        )

    query = urlencode(
        {
            "pa": vpa,
            "pn": payee_name,
            "am": f"{amount:.2f}",
            "tr": txn_id,
            "tn": note,
            "cu": "INR",
        },
        quote_via=quote,
    )
    return f"upi://pay?{query}"
