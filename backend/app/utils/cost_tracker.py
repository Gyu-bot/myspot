"""Cost tracking utility functions."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.audit import CostLog


async def log_cost(
    db: AsyncSession,
    provider: str,
    action: str,
    tokens_in: int | None,
    tokens_out: int | None,
    cost_krw: float | None,
) -> CostLog:
    """Insert cost log row.

    Args:
        db: Async database session.
        provider: Provider identifier.
        action: Action name.
        tokens_in: Prompt/input tokens.
        tokens_out: Completion/output tokens.
        cost_krw: Estimated KRW cost.

    Returns:
        Persisted CostLog model.
    """
    row = CostLog(
        provider=provider,
        action=action,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_krw=cost_krw,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_monthly_cost(db: AsyncSession, year: int, month: int) -> dict[str, float]:
    """Aggregate monthly cost grouped by provider."""
    stmt = (
        select(CostLog.provider, func.coalesce(func.sum(CostLog.cost_krw), 0.0).label("total"))
        .where(extract("year", CostLog.created_at) == year)
        .where(extract("month", CostLog.created_at) == month)
        .group_by(CostLog.provider)
    )
    rows = (await db.execute(stmt)).all()
    return {provider: float(total) for provider, total in rows}


async def check_budget_warning(db: AsyncSession) -> bool:
    """Return True if this month's cost exceeded budget."""
    now = datetime.now(UTC)
    monthly_by_provider = await get_monthly_cost(db, year=now.year, month=now.month)
    total = sum(monthly_by_provider.values())
    return total > settings.monthly_cost_limit_krw
