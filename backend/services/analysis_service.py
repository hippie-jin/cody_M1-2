from typing import List

from schemas import DataPoint, DataSummary, SummaryMetrics


def build_summary(points: List[DataPoint]) -> DataSummary:
    if not points:
        return DataSummary(
            period="데이터 없음",
            count=0,
            metrics=SummaryMetrics(total=0, average=0, max=0, min=0),
            trend="데이터가 없어 판단할 수 없습니다.",
        )

    sorted_points = sorted(points, key=lambda p: p.date)
    values = [p.value for p in sorted_points]
    count = len(values)
    total = sum(values)
    average = total / count

    metrics = SummaryMetrics(
        total=round(total, 2),
        average=round(average, 2),
        max=round(max(values), 2),
        min=round(min(values), 2),
    )
    period = f"{sorted_points[0].date.isoformat()} ~ {sorted_points[-1].date.isoformat()}"

    window = max(1, min(30, count // 2))
    recent = values[-window:]
    previous = values[-2 * window : -window] if count >= 2 * window else values[: max(count - window, 1)]

    recent_avg = sum(recent) / len(recent)
    previous_avg = sum(previous) / len(previous) if previous else recent_avg
    change_pct = 0.0 if previous_avg == 0 else (recent_avg - previous_avg) / previous_avg * 100

    if change_pct > 2:
        trend = f"상승 (최근 {window}개 구간 평균 대비 +{change_pct:.1f}%)"
    elif change_pct < -2:
        trend = f"하락 (최근 {window}개 구간 평균 대비 {change_pct:.1f}%)"
    else:
        trend = f"유지 (최근 {window}개 구간 평균 대비 {change_pct:+.1f}%)"

    return DataSummary(period=period, count=count, metrics=metrics, trend=trend)
