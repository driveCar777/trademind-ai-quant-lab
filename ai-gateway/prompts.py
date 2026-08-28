"""Prompt templates for AI Gateway V3.0."""

SYSTEM_PROMPT_ZH = """你是一个专业的量化投资分析师 AI 助手。
你的职责是基于提供的数据给出客观、专业的分析。
请使用中文回复，结构化输出，包含关键数据引用。
不要编造数据，只基于给定的上下文进行分析。"""

RESEARCH_REPORT_TEMPLATE = """请基于以下数据生成投研报告:

## 股票信息
- 股票代码: {stock}
- 股票名称: {stock_name}
- 行业: {sector}

## 因子数据
{factors_text}

## 评分结果
{score_text}

## 技术指标
{indicators_text}

## 市场评论
{market_comment}

请生成包含以下章节的投研报告:
1. 基本面概览
2. 估值分析
3. 技术面分析
4. 风险提示
5. 投资建议 (包含关键要点列表)
"""

STRATEGY_DESCRIBE_TEMPLATE = """请评估以下回测结果并给出专业分析:

## 策略信息
- 策略: {strategy}
- 品种: {symbol}
- 参数: {params}

## 回测结果
- 总收益: {profit}%
- 最大回撤: {max_drawdown}%
- 胜率: {win_rate}%
- 总交易次数: {total_trades}
- 夏普比率: {sharpe_ratio}
- 盈亏比: {profit_factor}

## 基准对比
{benchmark_text}

请给出:
1. 策略表现总结 (1-2 句)
2. 关键问题分析
3. 改进建议
4. 综合评分 (0-100) 和等级 (S/A/B/C/D)
5. 实盘使用建议
"""

SIGNAL_INTERPRET_TEMPLATE = """请解读以下技术指标信号。

规则:
- 只使用下面已经给出的数字。
- 某项没写就写「未提供」，不要向用户索要 MACD/RSI/布林带/均线。
- 不要编造数值，不要写「请提供数据」。

## 品种: {symbol} ({timeframe})

## 已提供的技术指标
{indicators_text}

## 已提供的价格
{price_text}

请用中文给出:
1. 当前信号判断 (看多/看空/中性) — 必须基于上面数字
2. 信号置信度 (0-1)
3. 技术分析解读 (只评论已提供的指标)
4. 建议操作
5. 建议止损位和止盈位 (没有价格则写未提供)
"""


def dict_to_text(d: dict) -> str:
    if not d:
        return "- (未提供)"
    return "\n".join(f"- {k}: {v}" for k, v in d.items())
