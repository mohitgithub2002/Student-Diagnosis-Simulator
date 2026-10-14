"""Everyday statements for if-then puzzles (T5, T23), each with a positive and a negative state."""

# (en positive, en negative, hi positive, hi negative, hinglish positive, hinglish negative)
PROPS = [
    ("the lamp is on", "the lamp is off", "लैंप जल रहा है", "लैंप बंद है", "lamp on hai", "lamp band hai"),
    ("the door is open", "the door is closed", "दरवाज़ा खुला है", "दरवाज़ा बंद है", "darwaza khula hai", "darwaza band hai"),
    (
        "the dog is barking",
        "the dog is quiet",
        "कुत्ता भौंक रहा है",
        "कुत्ता चुप है",
        "kutta bhaunk raha hai",
        "kutta chup hai",
    ),
    ("the kettle is hot", "the kettle is cold", "केतली गरम है", "केतली ठंडी है", "kettle garam hai", "kettle thandi hai"),
    ("the bus is late", "the bus is on time", "बस देर से है", "बस समय पर है", "bus late hai", "bus time par hai"),
    ("the shop is open", "the shop is closed", "दुकान खुली है", "दुकान बंद है", "dukaan khuli hai", "dukaan band hai"),
    ("the plants are wet", "the plants are dry", "पौधे गीले हैं", "पौधे सूखे हैं", "paudhe geele hain", "paudhe sookhe hain"),
    (
        "the fan is running",
        "the fan is stopped",
        "पंखा चल रहा है",
        "पंखा रुका हुआ है",
        "pankha chal raha hai",
        "pankha ruka hua hai",
    ),
    ("the cat is inside", "the cat is outside", "बिल्ली अंदर है", "बिल्ली बाहर है", "billi andar hai", "billi bahar hai"),
    ("the window is open", "the window is shut", "खिड़की खुली है", "खिड़की बंद है", "khidki khuli hai", "khidki band hai"),
    (
        "the phone is charging",
        "the phone is not charging",
        "फ़ोन चार्ज हो रहा है",
        "फ़ोन चार्ज नहीं हो रहा है",
        "phone charge ho raha hai",
        "phone charge nahi ho raha hai",
    ),
    ("the road is busy", "the road is empty", "सड़क पर भीड़ है", "सड़क खाली है", "sadak par bheed hai", "sadak khaali hai"),
    (
        "the tea is sweet",
        "the tea is not sweet",
        "चाय मीठी है",
        "चाय मीठी नहीं है",
        "chai meethi hai",
        "chai meethi nahi hai",
    ),
    ("the bell is ringing", "the bell is silent", "घंटी बज रही है", "घंटी चुप है", "ghanti baj rahi hai", "ghanti chup hai"),
    ("the signal is green", "the signal is red", "सिग्नल हरा है", "सिग्नल लाल है", "signal hara hai", "signal laal hai"),
    (
        "the ground is muddy",
        "the ground is dry",
        "ज़मीन पर कीचड़ है",
        "ज़मीन सूखी है",
        "zameen par keechad hai",
        "zameen sookhi hai",
    ),
]

_COL = {"en": 0, "hi": 2, "hinglish": 4}


def phrase(index: int, positive: bool, lang: str) -> str:
    return PROPS[index][_COL[lang] + (0 if positive else 1)]


OPTIONS = {
    "en": {"yes": "Yes, it must be true", "no": "No, it must be false", "cannot": "Cannot tell"},
    "hi": {"yes": "हाँ, ज़रूर सच है", "no": "नहीं, ज़रूर गलत है", "cannot": "पता नहीं चल सकता"},
    "hinglish": {"yes": "Haan, pakka sach hai", "no": "Nahi, pakka galat hai", "cannot": "Pata nahi chal sakta"},
}
