"""The 24 skills in 5 layers (Blueprint A-E). Every score is oriented so that higher means more of a
strength for this student; for pressure sensitivity the score is composure under time pressure."""

SKILLS: list[dict] = [
    # A. Cognitive
    {
        "id": "working_memory",
        "layer": "cognitive",
        "tasks": ["T1", "T5"],
        "name": {"en": "Working memory", "hi": "कार्यशील स्मृति"},
    },
    {
        "id": "long_term_recall",
        "layer": "cognitive",
        "tasks": ["T2", "T12"],
        "name": {"en": "Long-term recall", "hi": "लंबे समय तक याद रखना"},
    },
    {
        "id": "sustained_attention",
        "layer": "cognitive",
        "tasks": ["T3"],
        "name": {"en": "Sustained attention", "hi": "लगातार ध्यान"},
    },
    {
        "id": "processing_speed",
        "layer": "cognitive",
        "tasks": ["T4", "T10"],
        "name": {"en": "Processing speed", "hi": "सोचने की गति"},
    },
    {
        "id": "logical_reasoning",
        "layer": "cognitive",
        "tasks": ["T5", "T14"],
        "name": {"en": "Logical reasoning", "hi": "तार्किक सोच"},
    },
    {
        "id": "pattern_spatial",
        "layer": "cognitive",
        "tasks": ["T6"],
        "name": {"en": "Pattern and spatial reasoning", "hi": "पैटर्न और आकार की समझ"},
    },
    # B. Academic foundations
    {
        "id": "reading_fluency",
        "layer": "academic",
        "tasks": ["T7", "T8"],
        "name": {"en": "Reading fluency", "hi": "पढ़ने का प्रवाह"},
    },
    {
        "id": "reading_comprehension",
        "layer": "academic",
        "tasks": ["T8", "T9"],
        "name": {"en": "Reading comprehension", "hi": "पढ़कर समझना"},
    },
    {"id": "vocabulary", "layer": "academic", "tasks": ["T9", "T11"], "name": {"en": "Vocabulary", "hi": "शब्द भंडार"}},
    {"id": "number_sense", "layer": "academic", "tasks": ["T10"], "name": {"en": "Number sense", "hi": "संख्याओं की समझ"}},
    {
        "id": "expression",
        "layer": "academic",
        "tasks": ["T11", "T22"],
        "name": {"en": "Expression", "hi": "अपनी बात कहना"},
    },
    {
        "id": "concept_transfer",
        "layer": "academic",
        "tasks": ["T12"],
        "name": {"en": "Concept transfer", "hi": "सीखी बात को नई जगह लगाना"},
    },
    # C. Metacognitive
    {
        "id": "calibration",
        "layer": "metacognitive",
        "tasks": ["T13"],
        "name": {"en": "Self-awareness (calibration)", "hi": "खुद को आँकना"},
    },
    {
        "id": "strategy_planning",
        "layer": "metacognitive",
        "tasks": ["T14", "T5"],
        "name": {"en": "Strategy and planning", "hi": "रणनीति और योजना"},
    },
    {
        "id": "error_detection",
        "layer": "metacognitive",
        "tasks": ["T15", "T7"],
        "name": {"en": "Error detection and self-correction", "hi": "गलती पकड़ना और सुधारना"},
    },
    {
        "id": "time_management",
        "layer": "metacognitive",
        "tasks": ["T16", "T17"],
        "name": {"en": "Time management", "hi": "समय का प्रबंधन"},
    },
    # D. Emotional and psychological
    {
        "id": "confidence",
        "layer": "emotional",
        "tasks": ["T13", "T18"],
        "name": {"en": "Confidence level", "hi": "आत्मविश्वास"},
    },
    {
        "id": "pressure_sensitivity",
        "layer": "emotional",
        "tasks": ["T17"],
        "name": {"en": "Composure under pressure", "hi": "दबाव में संयम"},
    },
    {
        "id": "motivation",
        "layer": "emotional",
        "tasks": ["T18", "T19", "T21"],
        "name": {"en": "Motivation", "hi": "प्रेरणा"},
    },
    {
        "id": "resilience",
        "layer": "emotional",
        "tasks": ["T19", "T20"],
        "name": {"en": "Resilience", "hi": "हार न मानना"},
    },
    {
        "id": "growth_mindset",
        "layer": "emotional",
        "tasks": ["T20", "T18"],
        "name": {"en": "Growth mindset", "hi": "सीखने की सोच"},
    },
    # E. Behavioral and context
    {
        "id": "study_consistency",
        "layer": "behavioral",
        "tasks": ["T21"],
        "name": {"en": "Study consistency and focus habits", "hi": "पढ़ाई की नियमितता"},
    },
    {
        "id": "communication",
        "layer": "behavioral",
        "tasks": ["T22", "T11"],
        "name": {"en": "Communication and participation", "hi": "बातचीत और भागीदारी"},
    },
    {
        "id": "language_comfort",
        "layer": "behavioral",
        "tasks": ["T23", "T7", "T9"],
        "name": {"en": "Language comfort", "hi": "भाषा में सहजता"},
    },
]

SKILL_IDS = [s["id"] for s in SKILLS]
SKILLS_BY_ID = {s["id"]: s for s in SKILLS}
assert len(SKILLS) == 24
