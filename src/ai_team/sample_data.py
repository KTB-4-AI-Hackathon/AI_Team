from datetime import datetime
from ai_team.schema import Chat, AnalysisRequest, RelationshipType, User

SAMPLE_CONVERSATION: list[Chat] = [
    Chat(name='상대방', date=datetime.fromisoformat('2026-08-10T10:20:00+09:00'), message='요즘 왜 이렇게 연락이 뜸해?'),
    Chat(name='나', date=datetime.fromisoformat('2026-08-10T14:40:00+09:00'), message='어 미안 요즘 좀 바빴어'),
    Chat(name='상대방', date=datetime.fromisoformat('2026-08-10T14:41:00+09:00'), message='맨날 바쁘다고만 하고... 나랑 만나는 거 귀찮은 거 아니야?'),
    Chat(name='나', date=datetime.fromisoformat('2026-08-10T15:10:00+09:00'), message='그런거 아니야 진짜 일이 많아서 그래'),
    Chat(name='상대방', date=datetime.fromisoformat('2026-08-11T09:00:00+09:00'), message='됐어 신경쓰지마'),
]

SAMPLE_ANALYSIS_REQUEST = AnalysisRequest(
    user=User(id=1, name="나", nickname='나'),
    relationship_type=RelationshipType.ROMANTIC,
    chats=SAMPLE_CONVERSATION
)