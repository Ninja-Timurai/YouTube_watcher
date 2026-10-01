"""Labels for summaries written in the video's own language. Unknown languages fall back to English labels;
the summary text itself is still written in the video's language."""
from __future__ import annotations

KEYS = ("Bottom line", "Key takeaways", "Section by section", "Notable quotes", "Facts and figures",
        "Action items", "Verdict", "Limits")

LABELS = {
    "en": {"sections": KEYS, "channel": "Channel", "published": "Published", "length": "Length",
           "transcript": "Transcript", "summarised": "Summarised", "video": "Video", "captions": "captions",
           "ai_transcript": "AI transcript", "watch": "Watch in full if", "skip": "Skip if", "best": "Best part",
           "none": "None stated."},
    "ru": {"sections": ("Главное", "Ключевые выводы", "По разделам", "Цитаты", "Факты и цифры", "Рекомендации",
                        "Вердикт", "Ограничения"),
           "channel": "Канал", "published": "Опубликовано", "length": "Длительность", "transcript": "Транскрипт",
           "summarised": "Резюме составлено", "video": "Видео", "captions": "субтитры",
           "ai_transcript": "ИИ-транскрипция", "watch": "Смотреть целиком, если", "skip": "Пропустить, если",
           "best": "Лучший фрагмент", "none": "Не упоминается."},
    "uk": {"sections": ("Головне", "Ключові висновки", "По розділах", "Цитати", "Факти й цифри", "Рекомендації",
                        "Вердикт", "Обмеження"),
           "channel": "Канал", "published": "Опубліковано", "length": "Тривалість", "transcript": "Транскрипт",
           "summarised": "Резюме складено", "video": "Відео", "captions": "субтитри",
           "ai_transcript": "ШІ-транскрипція", "watch": "Дивитися повністю, якщо", "skip": "Пропустити, якщо",
           "best": "Найкращий фрагмент", "none": "Не згадується."},
    "de": {"sections": ("Kernaussage", "Wichtigste Erkenntnisse", "Abschnitt für Abschnitt", "Zitate",
                        "Fakten und Zahlen", "Handlungsempfehlungen", "Fazit", "Einschränkungen"),
           "channel": "Kanal", "published": "Veröffentlicht", "length": "Länge", "transcript": "Transkript",
           "summarised": "Zusammengefasst", "video": "Video", "captions": "Untertitel",
           "ai_transcript": "KI-Transkript", "watch": "Ganz ansehen, wenn", "skip": "Überspringen, wenn",
           "best": "Bester Teil", "none": "Keine genannt."},
    "es": {"sections": ("Conclusión principal", "Puntos clave", "Sección por sección", "Citas destacadas",
                        "Datos y cifras", "Acciones recomendadas", "Veredicto", "Limitaciones"),
           "channel": "Canal", "published": "Publicado", "length": "Duración", "transcript": "Transcripción",
           "summarised": "Resumido", "video": "Vídeo", "captions": "subtítulos",
           "ai_transcript": "transcripción IA", "watch": "Verlo completo si", "skip": "Saltarlo si",
           "best": "Mejor parte", "none": "Ninguna mencionada."},
    "fr": {"sections": ("L'essentiel", "Points clés", "Section par section", "Citations", "Faits et chiffres",
                        "Actions recommandées", "Verdict", "Limites"),
           "channel": "Chaîne", "published": "Publié", "length": "Durée", "transcript": "Transcription",
           "summarised": "Résumé le", "video": "Vidéo", "captions": "sous-titres",
           "ai_transcript": "transcription IA", "watch": "À regarder en entier si", "skip": "À passer si",
           "best": "Meilleur passage", "none": "Aucune mentionnée."},
}

NAMES = {"english": "en", "russian": "ru", "ukrainian": "uk", "german": "de", "spanish": "es", "french": "fr",
         "dutch": "nl", "italian": "it", "portuguese": "pt"}


def base(code: str | None) -> str:
    return (code or "").lower().split("-")[0].split("_")[0]


def summary_lang(meta: dict, cfg: dict) -> str:
    """Language code the summary is written in: the video's own language unless config names another."""
    want = str(cfg.get("output_language", "video")).strip().lower()
    if want in ("", "video", "auto"):
        return base(meta.get("transcript_lang")) or base(meta.get("language")) or "en"
    return NAMES.get(want, base(want))


def labels(lang: str) -> dict:
    return LABELS.get(lang, LABELS["en"])


def aliases() -> dict[str, str]:
    """Localized (and English) section heading -> canonical English key."""
    out = {}
    for lab in LABELS.values():
        out.update(zip(lab["sections"], KEYS))
    return out
