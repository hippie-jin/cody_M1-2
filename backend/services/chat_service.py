from typing import List, Optional, Tuple

from openai import OpenAI

import config
from schemas import ChatMessage
from services import conversation_service, data_service
from services.analysis_service import build_summary

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not config.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        _client = OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL)
    return _client


def _build_system_prompt() -> str:
    points = data_service.list_data_points()
    summary = build_summary(points)
    return (
        "당신은 사용자의 시계열 데이터를 분석해주는 데이터 분석 비서입니다.\n\n"
        "[사용자 데이터 요약]\n"
        f"- 데이터 기간: {summary.period}\n"
        f"- 총 레코드: {summary.count}개\n"
        f"- 주요 지표: 합계 {summary.metrics.total}, 평균 {summary.metrics.average}, "
        f"최대 {summary.metrics.max}, 최소 {summary.metrics.min}\n"
        f"- 최근 트렌드: {summary.trend}\n\n"
        "위 데이터를 기반으로 구체적이고 맞춤형인 답변을 한국어로 제공하세요. "
        "데이터에 없는 내용은 추측하지 말고 모른다고 답하세요."
    )


def ask(message: str, conversation_id: Optional[str]) -> Tuple[str, str]:
    client = _get_client()
    system_prompt = _build_system_prompt()

    history: List[ChatMessage] = []
    if conversation_id:
        history = conversation_service.get_conversation(conversation_id).messages

    api_messages = [{"role": "system", "content": system_prompt}]
    api_messages.extend({"role": m.role, "content": m.content} for m in history)
    api_messages.append({"role": "user", "content": message})

    completion = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=api_messages,
        max_tokens=1500,
    )
    reply = completion.choices[0].message.content or ""

    new_messages = [
        ChatMessage(role="user", content=message),
        ChatMessage(role="assistant", content=reply),
    ]
    if conversation_id:
        conversation_service.append_messages(conversation_id, new_messages)
        result_id = conversation_id
    else:
        result_id = conversation_service.create_conversation(new_messages, title=message[:30])

    return reply, result_id
