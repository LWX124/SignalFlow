"""市场数据相关工具."""

from typing import Any

from pydantic import BaseModel, Field

from .base import BaseAgentTool, ToolCategory, register_tool


class StockPriceInput(BaseModel):
    """股票价格查询输入."""

    symbol: str = Field(..., description="股票代码，如 '600519' 或 'AAPL'")
    market: str = Field(default="CN", description="市场，CN=中国A股, US=美股, HK=港股")


class StockPriceTool(BaseAgentTool):
    """获取股票实时价格工具."""

    name: str = "get_stock_price"
    description: str = "获取指定股票的实时价格信息，包括当前价、涨跌幅、成交量等"
    category: ToolCategory = ToolCategory.MARKET_DATA
    args_schema: type[BaseModel] = StockPriceInput

    def _run(self, symbol: str, market: str = "CN") -> dict[str, Any]:
        """同步获取股票价格 (模拟实现)."""
        # TODO: 集成真实的数据源
        return {
            "symbol": symbol,
            "market": market,
            "price": 100.0,
            "change": 2.5,
            "change_pct": 2.56,
            "volume": 1000000,
            "amount": 100000000,
            "high": 101.0,
            "low": 98.0,
            "open": 99.0,
            "prev_close": 97.5,
            "timestamp": "2024-01-15T10:30:00",
        }

    async def _arun(self, symbol: str, market: str = "CN") -> dict[str, Any]:
        """异步获取股票价格."""
        # TODO: 实现真正的异步数据获取
        return self._run(symbol, market)


class KLineInput(BaseModel):
    """K线数据查询输入."""

    symbol: str = Field(..., description="股票代码")
    period: str = Field(
        default="day",
        description="K线周期: 1min, 5min, 15min, 30min, 60min, day, week, month",
    )
    count: int = Field(default=100, description="获取的K线数量", ge=1, le=500)


class KLineTool(BaseAgentTool):
    """获取K线数据工具."""

    name: str = "get_kline"
    description: str = "获取股票的K线历史数据，支持多种周期"
    category: ToolCategory = ToolCategory.MARKET_DATA
    args_schema: type[BaseModel] = KLineInput

    def _run(
        self, symbol: str, period: str = "day", count: int = 100
    ) -> dict[str, Any]:
        """同步获取K线数据 (模拟实现)."""
        # TODO: 集成真实的数据源
        return {
            "symbol": symbol,
            "period": period,
            "count": count,
            "data": [
                {
                    "date": "2024-01-15",
                    "open": 99.0,
                    "high": 101.0,
                    "low": 98.0,
                    "close": 100.0,
                    "volume": 1000000,
                }
            ],
        }


class MarketOverviewInput(BaseModel):
    """市场概览输入."""

    market: str = Field(default="CN", description="市场，CN=中国A股, US=美股, HK=港股")


class MarketOverviewTool(BaseAgentTool):
    """获取市场概览工具."""

    name: str = "get_market_overview"
    description: str = "获取市场整体概览，包括主要指数、涨跌分布、成交额等"
    category: ToolCategory = ToolCategory.MARKET_DATA
    args_schema: type[BaseModel] = MarketOverviewInput

    def _run(self, market: str = "CN") -> dict[str, Any]:
        """同步获取市场概览 (模拟实现)."""
        return {
            "market": market,
            "indices": [
                {"name": "上证指数", "code": "000001", "value": 3000.0, "change_pct": 0.5},
                {"name": "深证成指", "code": "399001", "value": 10000.0, "change_pct": 0.8},
                {"name": "创业板指", "code": "399006", "value": 2000.0, "change_pct": 1.2},
            ],
            "statistics": {
                "up_count": 2500,
                "down_count": 2000,
                "flat_count": 500,
                "limit_up_count": 50,
                "limit_down_count": 10,
                "total_amount": 800000000000,
            },
            "timestamp": "2024-01-15T15:00:00",
        }


# 注册函数式工具示例
@register_tool(
    name="calculate_moving_average",
    description="计算移动平均线，支持 SMA、EMA",
    category=ToolCategory.TECHNICAL,
)
async def calculate_moving_average(
    prices: list[float],
    period: int = 20,
    ma_type: str = "SMA",
) -> dict[str, Any]:
    """计算移动平均线.

    Args:
        prices: 价格序列
        period: 周期
        ma_type: 类型，SMA=简单移动平均, EMA=指数移动平均

    Returns:
        移动平均线数据
    """
    if len(prices) < period:
        return {"error": f"价格数据不足，需要至少 {period} 个数据点"}

    if ma_type == "SMA":
        # 简单移动平均
        ma_values = []
        for i in range(period - 1, len(prices)):
            ma = sum(prices[i - period + 1 : i + 1]) / period
            ma_values.append(round(ma, 2))
    elif ma_type == "EMA":
        # 指数移动平均
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period  # 第一个 EMA 用 SMA
        ma_values = [round(ema, 2)]
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
            ma_values.append(round(ema, 2))
    else:
        return {"error": f"不支持的移动平均类型: {ma_type}"}

    return {
        "ma_type": ma_type,
        "period": period,
        "values": ma_values,
        "current": ma_values[-1] if ma_values else None,
    }


@register_tool(
    name="calculate_rsi",
    description="计算相对强弱指标 (RSI)",
    category=ToolCategory.TECHNICAL,
)
async def calculate_rsi(
    prices: list[float],
    period: int = 14,
) -> dict[str, Any]:
    """计算 RSI 指标.

    Args:
        prices: 价格序列 (收盘价)
        period: 周期，默认 14

    Returns:
        RSI 数据
    """
    if len(prices) < period + 1:
        return {"error": f"价格数据不足，需要至少 {period + 1} 个数据点"}

    # 计算价格变化
    changes = [prices[i] - prices[i - 1] for i in range(1, len(prices))]

    # 分离涨跌
    gains = [max(0, c) for c in changes]
    losses = [abs(min(0, c)) for c in changes]

    # 计算平均涨跌
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    rsi_values = []
    for i in range(period, len(changes)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

        rsi_values.append(round(rsi, 2))

    current_rsi = rsi_values[-1] if rsi_values else None

    # 判断超买超卖
    signal = "neutral"
    if current_rsi:
        if current_rsi >= 70:
            signal = "overbought"
        elif current_rsi <= 30:
            signal = "oversold"

    return {
        "period": period,
        "values": rsi_values,
        "current": current_rsi,
        "signal": signal,
    }


@register_tool(
    name="calculate_macd",
    description="计算 MACD 指标",
    category=ToolCategory.TECHNICAL,
)
async def calculate_macd(
    prices: list[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> dict[str, Any]:
    """计算 MACD 指标.

    Args:
        prices: 价格序列
        fast_period: 快线周期，默认 12
        slow_period: 慢线周期，默认 26
        signal_period: 信号线周期，默认 9

    Returns:
        MACD 数据
    """
    if len(prices) < slow_period + signal_period:
        return {"error": f"价格数据不足，需要至少 {slow_period + signal_period} 个数据点"}

    def calc_ema(data: list[float], period: int) -> list[float]:
        """计算 EMA."""
        multiplier = 2 / (period + 1)
        ema = sum(data[:period]) / period
        result = [ema]
        for price in data[period:]:
            ema = (price - ema) * multiplier + ema
            result.append(ema)
        return result

    # 计算快慢 EMA
    ema_fast = calc_ema(prices, fast_period)
    ema_slow = calc_ema(prices, slow_period)

    # 对齐数据
    offset = slow_period - fast_period
    ema_fast = ema_fast[offset:]

    # 计算 DIF (MACD 线)
    dif = [f - s for f, s in zip(ema_fast, ema_slow)]

    # 计算 DEA (信号线)
    dea = calc_ema(dif, signal_period)

    # 计算 MACD 柱
    offset = signal_period - 1
    dif_aligned = dif[offset:]
    macd_hist = [(d - e) * 2 for d, e in zip(dif_aligned, dea)]

    current_dif = round(dif_aligned[-1], 4) if dif_aligned else None
    current_dea = round(dea[-1], 4) if dea else None
    current_hist = round(macd_hist[-1], 4) if macd_hist else None

    # 判断金叉死叉
    signal = "neutral"
    if len(macd_hist) >= 2:
        if macd_hist[-1] > 0 and macd_hist[-2] <= 0:
            signal = "golden_cross"  # 金叉
        elif macd_hist[-1] < 0 and macd_hist[-2] >= 0:
            signal = "death_cross"  # 死叉

    return {
        "fast_period": fast_period,
        "slow_period": slow_period,
        "signal_period": signal_period,
        "dif": current_dif,
        "dea": current_dea,
        "macd": current_hist,
        "signal": signal,
    }


def register_market_tools() -> None:
    """注册所有市场数据工具到全局注册表."""
    StockPriceTool().register()
    KLineTool().register()
    MarketOverviewTool().register()
