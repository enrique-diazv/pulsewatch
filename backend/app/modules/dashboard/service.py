from uuid import UUID

from pydantic import ValidationError
from redis.asyncio import Redis as AsyncRedis
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.modules.dashboard.repository import (
    DashboardRepository,
    DashboardSummaryData,
)
from app.modules.dashboard.schemas import DashboardSummary

logger = get_logger(__name__)


def build_dashboard_cache_key(user_id: UUID) -> str:
    return f"dashboard:{user_id}"


async def invalidate_dashboard_cache(
    redis_client: AsyncRedis,
    user_id: UUID,
) -> None:
    cache_key = build_dashboard_cache_key(user_id)

    try:
        await redis_client.delete(cache_key)
    except RedisError:
        logger.warning(
            "dashboard_cache_invalidation_failed",
            extra={"cache_key": cache_key},
        )


class DashboardService:
    def __init__(
        self,
        session: AsyncSession,
        redis_client: AsyncRedis,
        settings: Settings | None = None,
        repository: DashboardRepository | None = None,
    ) -> None:
        self.redis_client = redis_client
        self.settings = settings or get_settings()
        self.repository = repository or DashboardRepository(
            session,
        )

    async def get_summary(
        self,
        user_id: UUID,
    ) -> DashboardSummary:
        cache_key = build_dashboard_cache_key(user_id)
        cached_summary = await self._read_cache(cache_key)

        if cached_summary is not None:
            return cached_summary

        data = await self.repository.summarize_for_user(
            user_id,
        )
        summary = self._build_summary(data)

        await self._write_cache(cache_key, summary)

        return summary

    async def _read_cache(
        self,
        cache_key: str,
    ) -> DashboardSummary | None:
        try:
            cached_payload = await self.redis_client.get(
                cache_key,
            )
        except RedisError:
            logger.warning(
                "dashboard_cache_read_failed",
                extra={"cache_key": cache_key},
            )
            return None

        if cached_payload is None:
            return None

        try:
            return DashboardSummary.model_validate_json(
                cached_payload,
            )
        except ValidationError:
            logger.warning(
                "dashboard_cache_payload_invalid",
                extra={"cache_key": cache_key},
            )
            return None

    async def _write_cache(
        self,
        cache_key: str,
        summary: DashboardSummary,
    ) -> None:
        try:
            await self.redis_client.set(
                cache_key,
                summary.model_dump_json(),
                ex=self.settings.dashboard_cache_ttl_seconds,
            )
        except RedisError:
            logger.warning(
                "dashboard_cache_write_failed",
                extra={"cache_key": cache_key},
            )

    @staticmethod
    def _build_summary(
        data: DashboardSummaryData,
    ) -> DashboardSummary:
        uptime_percentage = None

        if data.total_checks > 0:
            uptime_percentage = round(
                data.successful_checks / data.total_checks * 100,
                4,
            )

        return DashboardSummary(
            total_monitors=data.total_monitors,
            operational_monitors=data.operational_monitors,
            down_monitors=data.down_monitors,
            degraded_monitors=data.degraded_monitors,
            active_incidents=data.active_incidents,
            total_checks=data.total_checks,
            successful_checks=data.successful_checks,
            overall_uptime_percentage=uptime_percentage,
            average_response_time_ms=data.average_response_time_ms,
        )
