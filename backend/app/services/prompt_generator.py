PROMPT_TEMPLATES = {
    "detailed_notes": (
        "Aşağıdaki video transkriptini analiz et ve kapsamlı, detaylı notlar çıkar. "
        "Konu başlıklarını grupla, önemli kavramları açıkla, örnekleri ve açıklamaları "
        "ayrı ayrı belirt. Eksik bırakma; videodaki tüm önemli bilgileri kapsa."
    ),
    "bullet_summary": (
        "Aşağıdaki video transkriptini oku ve en önemli noktaları madde madde özetle. "
        "Her madde net, kısa ve anlaşılır olsun. Gereksiz tekrarları çıkar."
    ),
    "rules_tips": (
        "Aşağıdaki video transkriptinden videoda bahsedilen tüm kuralları, püf noktalarını, "
        "uyarıları, pratik ipuçlarını ve dikkat edilmesi gereken detayları madde madde listele."
    ),
    "study_guide": (
        "Aşağıdaki video transkriptini bir çalışma rehberine dönüştür. "
        "Ana konular, alt başlıklar, kilit kavramlar, örnekler ve tekrar soruları ekle."
    ),
    "quiz": (
        "Aşağıdaki video transkriptine dayanarak çoktan seçmeli ve açık uçlu sorular hazırla. "
        "Her sorunun altına kısa cevap anahtarı ekle."
    ),
}


def build_prompt(*, template_key: str, transcript_text: str, language: str) -> str:
    if template_key not in PROMPT_TEMPLATES:
        raise ValueError(f"Bilinmeyen şablon: {template_key}")

    instruction = PROMPT_TEMPLATES[template_key]
    return (
        f"{instruction}\n\n"
        f"Lütfen cevabını {language} dilinde ver.\n\n"
        "---- TRANSCRIPT ----\n"
        f"{transcript_text.strip()}\n"
        "---- END TRANSCRIPT ----"
    )
