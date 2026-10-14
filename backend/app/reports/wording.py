"""Report wording, English and Hindi. Strengths-first, plain language, never "weak", never a rank, never
a clinical label. "{name}" is filled in only when a parent or the student views the report."""

DISCLAIMER = {
    "en": "This is a screening profile, not a clinical assessment. Talk to a specialist if you have concerns.",
    "hi": "यह एक स्क्रीनिंग प्रोफ़ाइल है, कोई क्लिनिकल जाँच नहीं। अगर आपको कोई चिंता हो तो किसी विशेषज्ञ से बात करें।",
}

UI = {
    "en": {
        "parent_title": "{name}'s learning profile",
        "student_title": "Your learning profile",
        "strengths": "Strengths",
        "areas": "Areas to grow",
        "patterns": "Patterns worth knowing",
        "root_causes": "What was behind missed answers",
        "layers": "All 24 skills, compared with {name}'s own average",
        "early": "Early signals",
        "notes": "Notes for a teacher or counsellor",
        "evidence": "Evidence",
        "evidence_level": {"High": "High evidence", "Medium": "Likely (medium evidence)", "Low": "Early signal"},
        "home": "At home",
        "school": "At school",
        "action": "Your one action",
        "band": {
            "strength": "Strength",
            "typical": "In line with own average",
            "grow": "Area to grow",
            "insufficient": "Not enough evidence yet",
        },
        "clear": "clear strength",
        "intro": "This profile compares {name} with {name}'s own average across 24 skills, measured over "
        "{sessions} short sessions. It does not compare {name} with classmates.",
        "student_intro": "Here is what we noticed over your sessions. Everyone has strengths and places to grow.",
        "early_text": "{n} early signals were seen only once. We will watch these next cycle.",
        "tagged": "{tagged} of {total} missed answers had a clear cause.",
        "no_strengths": "Strengths will be clearer after the next cycle.",
        "no_areas": "No clear area to grow stood out this cycle.",
        "scoring_version": "Scoring version",
    },
    "hi": {
        "parent_title": "{name} की सीखने की प्रोफ़ाइल",
        "student_title": "तुम्हारी सीखने की प्रोफ़ाइल",
        "strengths": "खूबियाँ",
        "areas": "आगे बढ़ने के क्षेत्र",
        "patterns": "जानने लायक पैटर्न",
        "root_causes": "छूटे उत्तरों के पीछे क्या था",
        "layers": "सभी 24 कौशल, {name} के अपने औसत की तुलना में",
        "early": "शुरुआती संकेत",
        "notes": "शिक्षक या काउंसलर के लिए नोट्स",
        "evidence": "प्रमाण",
        "evidence_level": {"High": "मज़बूत प्रमाण", "Medium": "संभावित (मध्यम प्रमाण)", "Low": "शुरुआती संकेत"},
        "home": "घर पर",
        "school": "स्कूल में",
        "action": "तुम्हारा एक कदम",
        "band": {
            "strength": "खूबी",
            "typical": "अपने औसत के अनुसार",
            "grow": "आगे बढ़ने का क्षेत्र",
            "insufficient": "अभी पर्याप्त प्रमाण नहीं",
        },
        "clear": "स्पष्ट खूबी",
        "intro": "यह प्रोफ़ाइल {name} की तुलना 24 कौशलों में {name} के ही औसत से करती है, जो {sessions} छोटे सत्रों में "
        "मापे गए। यह {name} की तुलना सहपाठियों से नहीं करती।",
        "student_intro": "तुम्हारे सत्रों में हमने यह देखा। हर किसी में खूबियाँ होती हैं और आगे बढ़ने की जगहें भी।",
        "early_text": "{n} शुरुआती संकेत केवल एक बार दिखे। अगले चक्र में हम इन पर ध्यान रखेंगे।",
        "tagged": "{total} छूटे उत्तरों में से {tagged} का कारण साफ़ था।",
        "no_strengths": "अगले चक्र के बाद खूबियाँ और साफ़ दिखेंगी।",
        "no_areas": "इस चक्र में आगे बढ़ने का कोई साफ़ क्षेत्र नहीं दिखा।",
        "scoring_version": "स्कोरिंग संस्करण",
    },
}

# skill -> language -> (strength_student, strength_parent, grow_student, grow_parent, action_home, action_school)
SKILL_TEXT: dict[str, dict[str, tuple[str, str, str, str, str, str]]] = {
    "working_memory": {
        "en": (
            "You hold information in your head really well.",
            "Working memory is a clear strength, above {name}'s own average.",
            "Holding several things in mind at once is a place to grow.",
            "Holding and reordering information in mind is harder for {name} than other skills.",
            "Play memory games: repeat a phone number or shopping list backwards.",
            "Break multi-step instructions into short chunks and write them on the board.",
        ),
        "hi": (
            "तुम जानकारी को दिमाग में बहुत अच्छे से रखते हो।",
            "कार्यशील स्मृति {name} की स्पष्ट खूबी है, {name} के अपने औसत से ऊपर।",
            "एक साथ कई बातें याद रखना आगे बढ़ने की जगह है।",
            "जानकारी को दिमाग में रखकर उलटना-पलटना {name} के लिए बाकी कौशलों से कठिन है।",
            "याददाश्त के खेल खेलें: फ़ोन नंबर या सामान की सूची उल्टी बोलें।",
            "कई कदमों वाले निर्देश छोटे हिस्सों में दें और बोर्ड पर लिखें।",
        ),
    },
    "long_term_recall": {
        "en": (
            "You remember things well even days later.",
            "Long-term recall is a strength: {name} keeps what was learned over several days.",
            "Keeping new things in memory for longer is your next step.",
            "{name} learns new information but keeps less of it after a few days.",
            "Ask {name} to explain today's lesson at dinner, and again two days later.",
            "Begin lessons with a 3-minute recap of what was taught earlier in the week.",
        ),
        "hi": (
            "तुम बातें कई दिन बाद भी अच्छे से याद रखते हो।",
            "लंबे समय तक याद रखना एक खूबी है: {name} कई दिनों तक सीखी बातें याद रखता/रखती है।",
            "नई बातों को ज़्यादा देर तक याद रखना तुम्हारा अगला कदम है।",
            "{name} नई जानकारी सीखता/सीखती है, पर कुछ दिनों बाद उसमें से कम याद रहता है।",
            "{name} से रात के खाने पर आज का पाठ समझाने को कहें, और फिर दो दिन बाद दोबारा।",
            "पाठ की शुरुआत हफ़्ते में पहले पढ़ाई गई बातों की 3 मिनट की दोहराई से करें।",
        ),
    },
    "sustained_attention": {
        "en": (
            "You can stay focused for a long time.",
            "Sustained attention is a strength: {name} stays focused through long tasks.",
            "Keeping focus steady for longer is a place to grow.",
            "{name}'s focus dips over longer tasks, seen across more than one task.",
            "Use short study blocks of 15 to 20 minutes with planned breaks.",
            "Give long tasks in parts, with a quick check-in between parts.",
        ),
        "hi": (
            "तुम लंबे समय तक ध्यान लगाए रख सकते हो।",
            "लगातार ध्यान एक खूबी है: {name} लंबे कामों में भी ध्यान बनाए रखता/रखती है।",
            "ध्यान को ज़्यादा देर तक बनाए रखना आगे बढ़ने की जगह है।",
            "लंबे कामों में {name} का ध्यान कम होता है, यह एक से ज़्यादा गतिविधियों में दिखा।",
            "15 से 20 मिनट के छोटे पढ़ाई के हिस्से रखें, बीच में तय ब्रेक के साथ।",
            "लंबे काम हिस्सों में दें, और हर हिस्से के बीच जल्दी से जाँच लें।",
        ),
    },
    "processing_speed": {
        "en": (
            "You think quickly and accurately.",
            "Processing speed is a strength: {name} works quickly while staying accurate.",
            "Getting quicker on simple tasks is a place to grow, and accuracy comes first.",
            "{name} takes longer than on other skills to finish simple tasks accurately.",
            "Allow extra time and praise accuracy; speed grows with practice of familiar tasks.",
            "Where possible, give {name} a little extra time on timed work.",
        ),
        "hi": (
            "तुम तेज़ी से और सही सोचते हो।",
            "सोचने की गति एक खूबी है: {name} सही रहते हुए तेज़ी से काम करता/करती है।",
            "आसान कामों में तेज़ होना आगे बढ़ने की जगह है, पर पहले सही होना ज़रूरी है।",
            "आसान काम सही-सही पूरे करने में {name} को बाकी कौशलों की तुलना में ज़्यादा समय लगता है।",
            "अतिरिक्त समय दें और सही होने की तारीफ़ करें; जानी-पहचानी चीज़ों के अभ्यास से गति बढ़ती है।",
            "जहाँ हो सके, समयबद्ध काम में {name} को थोड़ा अतिरिक्त समय दें।",
        ),
    },
    "logical_reasoning": {
        "en": (
            "You are good at working things out step by step.",
            "Logical reasoning is a strength: {name} follows multi-step clues well.",
            "Multi-step problems are your next place to grow.",
            "Reasoning accuracy drops on longer chains of steps.",
            "Practise writing each step down when solving puzzles together.",
            "Model problems as numbered steps and ask {name} to explain each one.",
        ),
        "hi": (
            "तुम बातों को कदम-दर-कदम सुलझाने में अच्छे हो।",
            "तार्किक सोच एक खूबी है: {name} कई कदमों वाले सुराग अच्छे से समझता/समझती है।",
            "कई कदमों वाली समस्याएँ तुम्हारे आगे बढ़ने की अगली जगह हैं।",
            "कदमों की लंबी कड़ी में तार्किक सटीकता कम हो जाती है।",
            "पहेलियाँ साथ सुलझाते समय हर कदम लिखने का अभ्यास करें।",
            "समस्याओं को क्रमांकित कदमों में दिखाएँ और {name} से हर कदम समझाने को कहें।",
        ),
    },
    "pattern_spatial": {
        "en": (
            "You spot patterns and shapes quickly.",
            "Pattern and spatial reasoning is a strength for {name}.",
            "Seeing patterns and turned shapes is a place to grow.",
            "Pattern and shape puzzles are harder for {name} than other skills.",
            "Try jigsaw puzzles, tangrams or building blocks together.",
            "Use diagrams and hands-on models alongside words.",
        ),
        "hi": (
            "तुम पैटर्न और आकृतियाँ जल्दी पहचानते हो।",
            "पैटर्न और आकार की समझ {name} की एक खूबी है।",
            "पैटर्न और घुमाई गई आकृतियाँ समझना आगे बढ़ने की जगह है।",
            "पैटर्न और आकृति वाली पहेलियाँ {name} के लिए बाकी कौशलों से कठिन हैं।",
            "साथ मिलकर जिगसॉ पहेली, टैनग्राम या ब्लॉक्स से खेलें।",
            "शब्दों के साथ चित्र और हाथ से बनाए मॉडल भी इस्तेमाल करें।",
        ),
    },
    "reading_fluency": {
        "en": (
            "You read smoothly and clearly.",
            "Reading fluency is a strength: {name} reads smoothly and accurately.",
            "Reading more smoothly is a place to grow.",
            "Reading takes {name} more effort than other skills.",
            "Read aloud together for 10 minutes a day, taking turns by paragraph.",
            "Give {name} a chance to preview texts before reading aloud in class.",
        ),
        "hi": (
            "तुम सहजता और साफ़ तरीके से पढ़ते हो।",
            "पढ़ने का प्रवाह एक खूबी है: {name} सहजता और सही तरीके से पढ़ता/पढ़ती है।",
            "और सहजता से पढ़ना आगे बढ़ने की जगह है।",
            "पढ़ना {name} के लिए बाकी कौशलों से ज़्यादा मेहनत वाला है।",
            "रोज़ 10 मिनट साथ में ज़ोर से पढ़ें, बारी-बारी से एक-एक अनुच्छेद।",
            "कक्षा में ज़ोर से पढ़ने से पहले {name} को पाठ एक बार देखने का मौका दें।",
        ),
    },
    "reading_comprehension": {
        "en": (
            "You understand what you read, even the hidden parts.",
            "Reading comprehension is a strength, including reading between the lines.",
            "Reading between the lines is your next place to grow.",
            "{name} finds direct answers in a text more easily than working out what it implies.",
            "After a story, ask 'why do you think that happened?' rather than 'what happened?'.",
            "Ask inference questions and let {name} point to the clue in the text.",
        ),
        "hi": (
            "तुम जो पढ़ते हो उसे समझते हो, छिपी बातें भी।",
            "पढ़कर समझना एक खूबी है, पंक्तियों के बीच का अर्थ समझना भी।",
            "पंक्तियों के बीच का अर्थ समझना तुम्हारा अगला कदम है।",
            "{name} को पाठ में सीधे लिखे उत्तर ढूँढना, छिपे अर्थ समझने से आसान लगता है।",
            "कहानी के बाद 'क्या हुआ?' की जगह 'तुम्हें क्यों लगता है ऐसा हुआ?' पूछें।",
            "अनुमान वाले प्रश्न पूछें और {name} से पाठ में सुराग दिखाने को कहें।",
        ),
    },
    "vocabulary": {
        "en": (
            "You figure out new words from clues really well.",
            "Vocabulary is a strength: {name} works out new words from context.",
            "Learning new words is a place to grow.",
            "Working out unfamiliar words is harder for {name} than other skills.",
            "Pick one new word a day from a newspaper or show and use it at home.",
            "Pre-teach key words before a new topic.",
        ),
        "hi": (
            "तुम सुरागों से नए शब्द बहुत अच्छे से समझ लेते हो।",
            "शब्द भंडार एक खूबी है: {name} संदर्भ से नए शब्दों का अर्थ निकाल लेता/लेती है।",
            "नए शब्द सीखना आगे बढ़ने की जगह है।",
            "अनजान शब्दों का अर्थ निकालना {name} के लिए बाकी कौशलों से कठिन है।",
            "अख़बार या किसी कार्यक्रम से रोज़ एक नया शब्द चुनें और घर पर उसका प्रयोग करें।",
            "नए विषय से पहले मुख्य शब्द पहले से सिखाएँ।",
        ),
    },
    "number_sense": {
        "en": (
            "You have a great feel for numbers and sizes.",
            "Number sense is a strength: {name} judges amounts and estimates well.",
            "Getting a feel for how big numbers are is a place to grow.",
            "Estimating amounts is harder for {name} than other skills.",
            "Ask {name} to estimate the bill before paying at a shop.",
            "Ask for an estimate before every exact calculation.",
        ),
        "hi": (
            "तुम्हें संख्याओं और मात्राओं की बढ़िया समझ है।",
            "संख्याओं की समझ एक खूबी है: {name} मात्राओं और अनुमानों को अच्छे से आँकता/आँकती है।",
            "संख्याएँ कितनी बड़ी हैं, इसका अंदाज़ा लगाना आगे बढ़ने की जगह है।",
            "मात्राओं का अनुमान लगाना {name} के लिए बाकी कौशलों से कठिन है।",
            "दुकान पर भुगतान से पहले {name} से बिल का अनुमान लगाने को कहें।",
            "हर सटीक गणना से पहले एक अनुमान पूछें।",
        ),
    },
    "expression": {
        "en": (
            "You explain your ideas clearly.",
            "Expression is a strength: {name} explains ideas completely and in order.",
            "Explaining ideas step by step is a place to grow.",
            "Explaining ideas completely and in order is harder for {name} than other skills.",
            "Ask {name} to explain how to do something, like making tea, in three steps.",
            "Give sentence starters such as 'First...', 'Then...', 'Because...'.",
        ),
        "hi": (
            "तुम अपनी बात साफ़-साफ़ समझाते हो।",
            "अपनी बात कहना एक खूबी है: {name} विचारों को पूरी तरह और क्रम से समझाता/समझाती है।",
            "विचारों को कदम-दर-कदम समझाना आगे बढ़ने की जगह है।",
            "विचारों को पूरा और क्रम से समझाना {name} के लिए बाकी कौशलों से कठिन है।",
            "{name} से कोई काम, जैसे चाय बनाना, तीन कदमों में समझाने को कहें।",
            "'पहले...', 'फिर...', 'क्योंकि...' जैसे वाक्य की शुरुआत दें।",
        ),
    },
    "concept_transfer": {
        "en": (
            "You use what you learn in new situations.",
            "Concept transfer is a strength: {name} applies new ideas to new situations.",
            "Using what you learn in new places is your next step.",
            "{name} remembers new ideas but finds applying them in new situations harder.",
            "After learning something, ask 'where else could this work?'.",
            "Follow each new idea with one unfamiliar example.",
        ),
        "hi": (
            "तुम सीखी हुई बात नई जगहों पर लगा लेते हो।",
            "सीखी बात को नई जगह लगाना {name} की एक खूबी है।",
            "सीखी हुई बात को नई जगह लगाना तुम्हारा अगला कदम है।",
            "{name} नई बातें याद रखता/रखती है, पर उन्हें नई स्थितियों में लगाना कठिन लगता है।",
            "कुछ सीखने के बाद पूछें, 'यह और कहाँ काम आ सकता है?'।",
            "हर नए विचार के बाद एक अनजाना उदाहरण दें।",
        ),
    },
    "calibration": {
        "en": (
            "You know well when you know something.",
            "Self-awareness is a strength: {name}'s confidence matches results well.",
            "Matching how sure you feel with how you did is a place to grow.",
            "{name}'s confidence often does not match results.",
            "After homework, ask {name} to mark answers they are sure of, then check together.",
            "Ask for a quick confidence rating on exit tickets.",
        ),
        "hi": (
            "तुम अच्छे से जानते हो कि तुम्हें कब कोई बात आती है।",
            "खुद को आँकना एक खूबी है: {name} का भरोसा नतीजों से अच्छी तरह मेल खाता है।",
            "जितना पक्का महसूस करते हो और जैसा किया, उनका मेल बिठाना आगे बढ़ने की जगह है।",
            "{name} का भरोसा अक्सर नतीजों से मेल नहीं खाता।",
            "होमवर्क के बाद {name} से पक्के उत्तरों पर निशान लगवाएँ, फिर साथ में जाँचें।",
            "कक्षा के अंत में भरोसे की छोटी रेटिंग पूछें।",
        ),
    },
    "strategy_planning": {
        "en": (
            "You plan before you start, and it shows.",
            "Strategy and planning is a strength: {name} plans before acting.",
            "Planning before starting is a place to grow.",
            "{name} tends to start straight away and then restart.",
            "Before a task, ask {name} 'what will you do first, second, third?'.",
            "Give one minute of planning time before multi-step tasks.",
        ),
        "hi": (
            "तुम शुरू करने से पहले योजना बनाते हो, और यह दिखता है।",
            "रणनीति और योजना एक खूबी है: {name} काम से पहले योजना बनाता/बनाती है।",
            "शुरू करने से पहले योजना बनाना आगे बढ़ने की जगह है।",
            "{name} तुरंत शुरू कर देता/देती है और फिर दोबारा शुरू करता/करती है।",
            "काम से पहले {name} से पूछें, 'पहले, दूसरे, तीसरे क्या करोगे?'।",
            "कई कदमों वाले काम से पहले एक मिनट योजना का समय दें।",
        ),
    },
    "error_detection": {
        "en": (
            "You are great at catching mistakes.",
            "Error detection is a strength: {name} catches and fixes mistakes.",
            "Checking your work and catching mistakes is a place to grow.",
            "Spotting and fixing mistakes is harder for {name} than other skills.",
            "Play 'find the mistake' with a worked bill or recipe.",
            "Build a habit of a 1-minute check before submitting work.",
        ),
        "hi": (
            "तुम गलतियाँ पकड़ने में बढ़िया हो।",
            "गलती पकड़ना और सुधारना {name} की एक खूबी है।",
            "अपना काम जाँचना और गलतियाँ पकड़ना आगे बढ़ने की जगह है।",
            "गलतियाँ पहचानना और सुधारना {name} के लिए बाकी कौशलों से कठिन है।",
            "किसी बिल या रेसिपी में 'गलती ढूँढो' खेल खेलें।",
            "काम जमा करने से पहले 1 मिनट जाँचने की आदत डालें।",
        ),
    },
    "time_management": {
        "en": (
            "You use your time wisely.",
            "Time management is a strength: {name} plans time and sticks to it.",
            "Sharing your time across tasks is a place to grow.",
            "{name} finds it harder to share time across tasks and finish all of them.",
            "Use a kitchen timer to plan homework blocks together.",
            "Show the time left during tests and suggest a time per section.",
        ),
        "hi": (
            "तुम अपना समय समझदारी से इस्तेमाल करते हो।",
            "समय का प्रबंधन एक खूबी है: {name} समय की योजना बनाकर उस पर टिकता/टिकती है।",
            "अलग-अलग कामों में समय बाँटना आगे बढ़ने की जगह है।",
            "{name} को कामों में समय बाँटना और सब पूरे करना कठिन लगता है।",
            "होमवर्क के हिस्से तय करने के लिए साथ मिलकर टाइमर का इस्तेमाल करें।",
            "परीक्षा में बचा समय दिखाएँ और हर हिस्से के लिए समय सुझाएँ।",
        ),
    },
    "confidence": {
        "en": (
            "You believe in yourself and take on challenges.",
            "Confidence is a strength: {name} is willing to take on harder challenges.",
            "Believing in your own answers is a place to grow.",
            "{name} often feels unsure, even when doing well.",
            "Point out specific things {name} got right, with the reason.",
            "Invite {name} to share answers in small groups first.",
        ),
        "hi": (
            "तुम्हें खुद पर भरोसा है और तुम चुनौतियाँ लेते हो।",
            "आत्मविश्वास एक खूबी है: {name} कठिन चुनौतियाँ लेने को तैयार रहता/रहती है।",
            "अपने उत्तरों पर भरोसा करना आगे बढ़ने की जगह है।",
            "{name} अक्सर अनिश्चित महसूस करता/करती है, तब भी जब अच्छा कर रहा/रही हो।",
            "{name} ने जो सही किया उसे कारण के साथ बताएँ।",
            "{name} को पहले छोटे समूहों में उत्तर साझा करने के लिए बुलाएँ।",
        ),
    },
    "pressure_sensitivity": {
        "en": (
            "You stay calm when the clock is ticking.",
            "Composure under pressure is a strength: {name} stays steady with a timer.",
            "Staying calm with a timer is a place to grow, and many people find timers hard.",
            "Performance falls under time pressure, seen in two sessions.",
            "Try short, low-stakes timed practice at home and praise the process, not the speed.",
            "Offer practice tests with gradually shorter time limits.",
        ),
        "hi": (
            "घड़ी चलते समय भी तुम शांत रहते हो।",
            "दबाव में संयम एक खूबी है: {name} टाइमर के साथ भी स्थिर रहता/रहती है।",
            "टाइमर के साथ शांत रहना आगे बढ़ने की जगह है, और बहुत लोगों को टाइमर कठिन लगता है।",
            "समय के दबाव में प्रदर्शन कम होता है, यह दो सत्रों में दिखा।",
            "घर पर छोटे, बिना दबाव वाले समयबद्ध अभ्यास करें और गति नहीं, तरीके की तारीफ़ करें।",
            "धीरे-धीरे कम होती समय-सीमा वाले अभ्यास टेस्ट दें।",
        ),
    },
    "motivation": {
        "en": (
            "You like a challenge and keep coming back.",
            "Motivation is a strength: {name} seeks challenges and returns to practise.",
            "Choosing challenges more often is a place to grow.",
            "{name} tends to choose easier options, especially after a mistake.",
            "Celebrate effort on hard tasks, even when the answer is wrong.",
            "Offer optional challenge questions with no penalty for mistakes.",
        ),
        "hi": (
            "तुम्हें चुनौती पसंद है और तुम बार-बार लौटते हो।",
            "प्रेरणा एक खूबी है: {name} चुनौतियाँ चुनता/चुनती है और अभ्यास के लिए लौटता/लौटती है।",
            "ज़्यादा बार चुनौती चुनना आगे बढ़ने की जगह है।",
            "{name} आसान विकल्प चुनता/चुनती है, खासकर गलती के बाद।",
            "कठिन कामों पर मेहनत की सराहना करें, उत्तर गलत हो तब भी।",
            "बिना सज़ा वाले वैकल्पिक चुनौती प्रश्न दें।",
        ),
    },
    "resilience": {
        "en": (
            "You keep going when things get tough.",
            "Resilience is a strength: {name} keeps trying and bounces back after mistakes.",
            "Bouncing back after a mistake is a place to grow.",
            "After a mistake, {name}'s next answer is often affected.",
            "Share a story of your own mistake and what you did next.",
            "Normalise mistakes as part of learning in class discussions.",
        ),
        "hi": (
            "मुश्किल होने पर भी तुम लगे रहते हो।",
            "हार न मानना एक खूबी है: {name} कोशिश करता/करती रहता/रहती है और गलती के बाद संभल जाता/जाती है।",
            "गलती के बाद संभलना आगे बढ़ने की जगह है।",
            "गलती के बाद {name} का अगला उत्तर अक्सर प्रभावित होता है।",
            "अपनी किसी गलती और उसके बाद आपने क्या किया, उसकी कहानी सुनाएँ।",
            "कक्षा में गलतियों को सीखने का हिस्सा मानकर बात करें।",
        ),
    },
    "growth_mindset": {
        "en": (
            "You see mistakes as a chance to learn.",
            "Growth mindset is a strength: {name} tries again after mistakes and picks challenges.",
            "Trying again after a mistake is a place to grow.",
            "{name} tends to avoid retrying after a mistake.",
            "Praise effort and strategy ('you tried a new way') rather than being clever.",
            "Allow corrections and resubmissions for credit.",
        ),
        "hi": (
            "तुम गलतियों को सीखने का मौका मानते हो।",
            "सीखने की सोच एक खूबी है: {name} गलती के बाद फिर कोशिश करता/करती है और चुनौतियाँ चुनता/चुनती है।",
            "गलती के बाद फिर कोशिश करना आगे बढ़ने की जगह है।",
            "{name} गलती के बाद दोबारा कोशिश करने से बचता/बचती है।",
            "होशियारी की नहीं, मेहनत और तरीके की तारीफ़ करें ('तुमने नया तरीका आज़माया')।",
            "सुधार करके दोबारा जमा करने का मौका दें।",
        ),
    },
    "study_consistency": {
        "en": (
            "You show up regularly and keep good habits.",
            "Study consistency is a strength: {name} keeps a regular rhythm.",
            "Building a regular study rhythm is a place to grow.",
            "{name}'s study rhythm is less regular than other skills suggest.",
            "Agree on a fixed 20-minute study time each day.",
            "Use a simple weekly planner and check it on Mondays.",
        ),
        "hi": (
            "तुम नियमित रूप से आते हो और अच्छी आदतें रखते हो।",
            "पढ़ाई की नियमितता एक खूबी है: {name} एक नियमित लय बनाए रखता/रखती है।",
            "पढ़ाई की नियमित लय बनाना आगे बढ़ने की जगह है।",
            "{name} की पढ़ाई की लय बाकी कौशलों के मुकाबले कम नियमित है।",
            "हर दिन पढ़ाई के लिए 20 मिनट का तय समय मिलकर तय करें।",
            "एक आसान साप्ताहिक प्लानर रखें और सोमवार को उसे देखें।",
        ),
    },
    "communication": {
        "en": (
            "You share your ideas and take part.",
            "Communication is a strength: {name} answers readily and explains in detail.",
            "Sharing your ideas more is a place to grow.",
            "{name} shares less and gives shorter answers than other skills suggest.",
            "Ask open questions at meals and give time to answer.",
            "Let {name} choose to answer in writing or speaking at first.",
        ),
        "hi": (
            "तुम अपने विचार साझा करते हो और भाग लेते हो।",
            "बातचीत और भागीदारी एक खूबी है: {name} आसानी से उत्तर देता/देती है और विस्तार से समझाता/समझाती है।",
            "अपने विचार ज़्यादा साझा करना आगे बढ़ने की जगह है।",
            "{name} कम साझा करता/करती है और छोटे उत्तर देता/देती है।",
            "खाने के समय खुले प्रश्न पूछें और उत्तर देने का समय दें।",
            "शुरुआत में {name} को लिखकर या बोलकर उत्तर देने का विकल्प दें।",
        ),
    },
    "language_comfort": {
        "en": (
            "Your thinking is strong in more than one language.",
            "Language comfort is a strength: {name} reasons equally well across languages.",
            "Getting comfortable in English reading is a place to grow.",
            "{name} reasons better in Hindi or Hinglish than in English; English scores are language-adjusted.",
            "Read short English and Hindi stories side by side.",
            "Allow {name} to explain answers in Hindi when the concept is being checked.",
        ),
        "hi": (
            "तुम्हारी सोच एक से ज़्यादा भाषाओं में मज़बूत है।",
            "भाषा में सहजता एक खूबी है: {name} भाषाओं में बराबर अच्छी तरह सोचता/सोचती है।",
            "अंग्रेज़ी में पढ़ने में सहज होना आगे बढ़ने की जगह है।",
            "{name} अंग्रेज़ी की तुलना में हिंदी या हिंग्लिश में बेहतर तर्क करता/करती है; अंग्रेज़ी के अंक भाषा-समायोजित हैं।",
            "अंग्रेज़ी और हिंदी की छोटी कहानियाँ साथ-साथ पढ़ें।",
            "जब अवधारणा जाँची जा रही हो, तो {name} को हिंदी में उत्तर समझाने दें।",
        ),
    },
}

PATTERN_TEXT = {
    "confidence_mismatch:underconfident": {
        "en": (
            "You know more than you think you do.",
            "Underconfident: often rates answers 'unsure' that are correct.",
            "Rated 'unsure' on {unsure_correct} of {right_n} correct answers.",
        ),
        "hi": (
            "तुम जितना सोचते हो, उससे ज़्यादा जानते हो।",
            "कम आत्मविश्वास: अक्सर सही उत्तरों को 'पक्का नहीं' बताता/बताती है।",
            "{right_n} सही उत्तरों में से {unsure_correct} पर 'पक्का नहीं' चुना।",
        ),
    },
    "confidence_mismatch:overconfident": {
        "en": (
            "A quick check before moving on will make you even stronger.",
            "Overconfident: often feels sure about answers that turn out wrong. Encourage a quick check.",
            "Felt sure on {sure_wrong} of {wrong_n} answers that were wrong.",
        ),
        "hi": (
            "आगे बढ़ने से पहले एक छोटी जाँच तुम्हें और मज़बूत बनाएगी।",
            "ज़्यादा भरोसा: अक्सर उन उत्तरों पर पक्का महसूस करता/करती है जो गलत निकलते हैं। जल्दी जाँचने को प्रोत्साहित करें।",
            "{wrong_n} गलत उत्तरों में से {sure_wrong} पर पक्का महसूस किया।",
        ),
    },
    "pressure_pattern": {
        "en": (
            "Timers make things harder for many people. We can practise that.",
            "Performance falls under time pressure, seen in two sessions. Try short timed practice at home.",
            "{relaxed}% relaxed vs {pressure}% under a timer, sessions {sessions}.",
        ),
        "hi": (
            "टाइमर बहुत लोगों के लिए चीज़ें कठिन बना देता है। हम इसका अभ्यास कर सकते हैं।",
            "समय के दबाव में प्रदर्शन कम होता है, यह दो सत्रों में दिखा। घर पर छोटे समयबद्ध अभ्यास करें।",
            "आराम से {relaxed}% बनाम टाइमर के साथ {pressure}%, सत्र {sessions}।",
        ),
    },
    "language_adjustment": {
        "en": (
            "Your thinking is strong in Hindi and English.",
            "English reading scores are language-adjusted because the Hindi version scored higher.",
            "Same items: {native}% in Hindi or Hinglish, {english}% in English.",
        ),
        "hi": (
            "तुम्हारी सोच हिंदी और अंग्रेज़ी दोनों में मज़बूत है।",
            "अंग्रेज़ी पढ़ने के अंक भाषा-समायोजित हैं क्योंकि हिंदी संस्करण में अंक ज़्यादा आए।",
            "वही प्रश्न: हिंदी या हिंग्लिश में {native}%, अंग्रेज़ी में {english}%।",
        ),
    },
}

TAG_TEXT = {
    "concept_gap": {
        "en": ("Concept gap", "Re-teach the idea from a simpler starting point."),
        "hi": ("अवधारणा की कमी", "विचार को आसान शुरुआत से दोबारा सिखाएँ।"),
    },
    "careless_slip": {
        "en": ("Careless slip", "Build a habit of checking before submitting."),
        "hi": ("लापरवाही की चूक", "जमा करने से पहले जाँचने की आदत डालें।"),
    },
    "pressure_error": {
        "en": ("Pressure-driven error", "Practise with gradual time pressure; praise process over speed."),
        "hi": ("दबाव से हुई गलती", "धीरे-धीरे बढ़ते समय-दबाव के साथ अभ्यास करें; गति नहीं, तरीके की तारीफ़ करें।"),
    },
    "language_barrier": {
        "en": ("Reading or language barrier", "Support language and reading before judging the concept."),
        "hi": ("पढ़ने या भाषा की बाधा", "अवधारणा आँकने से पहले भाषा और पढ़ने में मदद करें।"),
    },
    "attention_lapse": {
        "en": ("Attention lapse", "Use shorter study blocks with planned breaks."),
        "hi": ("ध्यान भटकना", "तय ब्रेक के साथ पढ़ाई के छोटे हिस्से रखें।"),
    },
    "guess": {
        "en": ("Guess", "Treat these items as not yet learned, not as a lack of ability."),
        "hi": ("अंदाज़ा", "इन्हें 'अभी नहीं सीखा' मानें, क्षमता की कमी नहीं।"),
    },
}

CUE_TEXT = {
    "forward_fine_backward_low": {
        "en": "Holding information is fine; reordering it in mind is the harder part.",
        "hi": "जानकारी याद रखना ठीक है; उसे मन में उलटना-पलटना कठिन हिस्सा है।",
    },
    "learns_not_retains": {
        "en": "Learns quickly but keeps less after a few days.",
        "hi": "जल्दी सीखता/सीखती है पर कुछ दिनों बाद कम याद रहता है।",
    },
    "decline_after_minute_2": {
        "en": "Focus drops after about two minutes across more than one task.",
        "hi": "एक से ज़्यादा गतिविधियों में लगभग दो मिनट बाद ध्यान कम होता है।",
    },
    "fast_but_inaccurate": {
        "en": "Answers quickly but with more mistakes: slowing down a little may help.",
        "hi": "जल्दी उत्तर देता/देती है पर गलतियाँ ज़्यादा होती हैं: थोड़ा धीमा होना मदद कर सकता है।",
    },
    "long_chains_check_memory": {
        "en": "Manages short reasoning chains but not longer ones; check working memory before "
        "concluding that reasoning is the issue.",
        "hi": "छोटी तर्क-कड़ियाँ संभाल लेता/लेती है पर लंबी नहीं; निष्कर्ष से पहले कार्यशील स्मृति देखें।",
    },
    "sequence_rotation_split": {
        "en": "Shape sequences and turned shapes give quite different results.",
        "hi": "आकृतियों के क्रम और घुमाई गई आकृतियों के नतीजे काफ़ी अलग हैं।",
    },
    "surface_reading": {
        "en": "Finds direct answers well; reading between the lines is the next step.",
        "hi": "सीधे उत्तर अच्छे से ढूँढता/ढूँढती है; छिपा अर्थ समझना अगला कदम है।",
    },
    "slow_but_accurate": {
        "en": "Reads slowly but understands well: decoding takes effort.",
        "hi": "धीरे पढ़ता/पढ़ती है पर अच्छी तरह समझता/समझती है: शब्द पढ़ने में मेहनत लगती है।",
    },
    "skimming": {
        "en": "Reads fast but understands less: may be skimming.",
        "hi": "तेज़ पढ़ता/पढ़ती है पर कम समझता/समझती है: शायद सरसरी नज़र से पढ़ रहा/रही है।",
    },
    "memorizes_not_applies": {
        "en": "Remembers new ideas well; applying them in new situations is the next step.",
        "hi": "नई बातें अच्छे से याद रखता/रखती है; उन्हें नई स्थितियों में लगाना अगला कदम है।",
    },
    "starts_instantly_restarts": {
        "en": "Starts instantly, then restarts several times.",
        "hi": "तुरंत शुरू करता/करती है, फिर कई बार दोबारा शुरू करता/करती है।",
    },
    "changes_right_to_wrong": {
        "en": "Changes right answers to wrong more often than the reverse.",
        "hi": "सही उत्तरों को गलत में ज़्यादा बार बदलता/बदलती है, उल्टा कम।",
    },
    "front_loads": {
        "en": "Spends most time on the first items and rushes the rest.",
        "hi": "ज़्यादातर समय पहले प्रश्नों पर लगाता/लगाती है और बाकी में जल्दी करता/करती है।",
    },
    "underconfident_good_news": {
        "en": "Feels less sure than results show, which is good news to share.",
        "hi": "नतीजे जितने अच्छे हैं, उससे कम पक्का महसूस करता/करती है; यह बताने लायक अच्छी खबर है।",
    },
    "avoids_after_error": {
        "en": "Picks only easy items after a mistake.",
        "hi": "गलती के बाद केवल आसान प्रश्न चुनता/चुनती है।",
    },
    "post_error_drop": {
        "en": "Accuracy dips on the item right after a mistake.",
        "hi": "गलती के ठीक बाद वाले प्रश्न पर सटीकता कम हो जाती है।",
    },
    "tends_to_avoid_retrying": {
        "en": "Tends to avoid retrying after a mistake.",
        "hi": "गलती के बाद दोबारा कोशिश करने से बचता/बचती है।",
    },
    "reports_daily_no_returns": {
        "en": "Reports studying most days but did not return to the app between sessions.",
        "hi": "ज़्यादातर दिन पढ़ने की बात कहता/कहती है, पर सत्रों के बीच ऐप पर नहीं लौटा/लौटी।",
    },
    "prefers_typing": {
        "en": "Prefers typing to speaking: a preference to explore, not a concern.",
        "hi": "बोलने के बजाय लिखना पसंद करता/करती है: यह एक पसंद है, चिंता नहीं।",
    },
    "prefers_speaking": {
        "en": "Explains better by speaking than by typing.",
        "hi": "लिखने के बजाय बोलकर बेहतर समझाता/समझाती है।",
    },
}

# feature -> (format, en, hi). Formats: pct, num0, num1, sec, pts, signed, times, conf4.
EVIDENCE = {
    "t1.backward_span": (
        "num0",
        "Repeated {v}-item sequences backward at 80% accuracy.",
        "{v} चीज़ों के क्रम 80% सटीकता से उल्टे दोहराए।",
    ),
    "t1.forward_span": (
        "num0",
        "Repeated {v}-item sequences in order at 80% accuracy.",
        "{v} चीज़ों के क्रम 80% सटीकता से सीधे दोहराए।",
    ),
    "t1.accuracy": ("pct", "{v} of memory sequences correct.", "याद वाले क्रमों में {v} सही।"),
    "t5.long_chain_acc": ("pct", "{v} correct on 4- and 5-step clue chains.", "4 और 5 कदमों वाली कड़ियों में {v} सही।"),
    "t2.retention": (
        "pct",
        "Kept {v} of what was remembered, a few days later.",
        "कुछ दिनों बाद भी याद की गई बातों का {v} याद रहा।",
    ),
    "t2.delayed_acc": (
        "pct",
        "{v} correct when asked about the card again days later.",
        "कई दिन बाद कार्ड के बारे में पूछने पर {v} सही।",
    ),
    "t2.false_alarm_rate": (
        "pct",
        "Remembered things that were not on the card in {v} of checks.",
        "{v} जाँचों में ऐसी चीज़ें याद बताईं जो कार्ड पर नहीं थीं।",
    ),
    "t12.recall_acc": ("pct", "{v} correct on recalling the new lesson.", "नए पाठ को याद करने में {v} सही।"),
    "t3.hit_minus_fa": (
        "pct",
        "Focus score of {v} in the 4-minute focus stream.",
        "4 मिनट की ध्यान गतिविधि में {v} ध्यान स्कोर।",
    ),
    "t3.rt_cv": (
        "pct",
        "Reaction times varied by {v} in the focus stream.",
        "ध्यान गतिविधि में प्रतिक्रिया समय {v} तक बदला।",
    ),
    "t3.decline": (
        "pts",
        "Focus changed by {v} points from the first to the last minute.",
        "पहले से आखिरी मिनट तक ध्यान {v} अंक बदला।",
    ),
    "all.distraction_rate": (
        "pct",
        "{v} of items had long pauses or app switches.",
        "{v} प्रश्नों में लंबे ठहराव या ऐप बदलना दिखा।",
    ),
    "t4.median_rt_correct": (
        "sec",
        "Typical correct answer in {v} s on quick matching.",
        "जल्दी मिलान में सही उत्तर आमतौर पर {v} सेकंड में।",
    ),
    "t10.median_rt_correct": (
        "sec",
        "Typical correct answer in {v} s on number estimates.",
        "संख्या अनुमान में सही उत्तर आमतौर पर {v} सेकंड में।",
    ),
    "all.median_rt_correct": (
        "sec",
        "Typical correct answer in {v} s on quick tasks.",
        "जल्दी वाले कामों में सही उत्तर आमतौर पर {v} सेकंड में।",
    ),
    "t5.level": ("num0", "Solved clue chains up to level {v} of 10.", "सुराग-कड़ियाँ 10 में से स्तर {v} तक हल कीं।"),
    "t5.accuracy": ("pct", "{v} of clue chains correct.", "सुराग-कड़ियों में {v} सही।"),
    "t14.accuracy": (
        "pct",
        "{v} of trip plans were close to the shortest route.",
        "{v} यात्रा योजनाएँ सबसे छोटे रास्ते के करीब थीं।",
    ),
    "t5.time_per_step": ("sec", "About {v} s per reasoning step.", "हर तर्क-कदम पर लगभग {v} सेकंड।"),
    "t6.level": ("num0", "Shape puzzles up to level {v} of 10.", "आकृति पहेलियाँ 10 में से स्तर {v} तक।"),
    "t6.sequence_acc": ("pct", "{v} correct on what-comes-next shapes.", "'आगे क्या आएगा' आकृतियों में {v} सही।"),
    "t6.rotation_acc": ("pct", "{v} correct on turned-shape puzzles.", "घुमाई गई आकृतियों में {v} सही।"),
    "t6.near_miss_share": ("pct", "{v} of misses were near misses.", "{v} चूकें बहुत करीब थीं।"),
    "t7.wpm_acc": (
        "num0",
        "Read aloud at about {v} correct words per minute.",
        "लगभग {v} सही शब्द प्रति मिनट की गति से ज़ोर से पढ़ा।",
    ),
    "t7.pause_rate": ("num0", "{v} pauses per 100 words when reading aloud.", "ज़ोर से पढ़ते समय हर 100 शब्दों में {v} ठहराव।"),
    "t8.silent_time_per_100w": (
        "num0",
        "Read silently at about {v} s per 100 words.",
        "मन में लगभग {v} सेकंड प्रति 100 शब्द की गति से पढ़ा।",
    ),
    "t8.inference_acc": ("pct", "{v} correct on 'read between the lines' questions.", "छिपे अर्थ वाले प्रश्नों में {v} सही।"),
    "t8.direct_acc": (
        "pct",
        "{v} correct on questions answered directly in the text.",
        "पाठ में सीधे लिखे उत्तरों वाले प्रश्नों में {v} सही।",
    ),
    "t8.reread_rate": (
        "num1",
        "Opened the passage again {v} times per question.",
        "हर प्रश्न पर अनुच्छेद {v} बार दोबारा खोला।",
    ),
    "t9.weighted_acc": (
        "pct",
        "Worked out {v} of new word meanings from clues (difficulty-weighted).",
        "सुरागों से नए शब्दों के {v} अर्थ निकाले (कठिनाई के अनुसार)।",
    ),
    "t9.accuracy": ("pct", "{v} of word meanings worked out from clues.", "सुरागों से {v} शब्दों के अर्थ निकाले।"),
    "t9.clue_use": (
        "pct",
        "Took time and got it right on {v} of word items.",
        "{v} शब्द प्रश्नों में समय लेकर सही उत्तर दिया।",
    ),
    "t11.unique_ratio": (
        "pct",
        "Used varied words when explaining ({v} different words).",
        "समझाते समय अलग-अलग शब्द इस्तेमाल किए ({v} अलग शब्द)।",
    ),
    "t10.estimate_acc": ("pct", "Estimates were {v} accurate on average.", "अनुमान औसतन {v} सटीक थे।"),
    "t10.compare_acc": (
        "pct",
        "{v} correct on quick 'which is more' comparisons.",
        "'कौन ज़्यादा है' वाली तुलनाओं में {v} सही।",
    ),
    "t11.rubric": (
        "num1",
        "Explanations scored {v} of 4 for completeness, order and clarity.",
        "समझाने में पूर्णता, क्रम और स्पष्टता के लिए 4 में से {v}।",
    ),
    "t22.rubric": (
        "num1",
        "Conversation answers scored {v} of 4 for completeness, order and clarity.",
        "बातचीत के उत्तरों में 4 में से {v}।",
    ),
    "t11.pause_rate": (
        "num0",
        "{v} pauses per 100 words when explaining aloud.",
        "बोलकर समझाते समय हर 100 शब्दों में {v} ठहराव।",
    ),
    "t12.far_acc": (
        "pct",
        "{v} correct when using the new idea in a new situation.",
        "नई बात को नई स्थिति में लगाने में {v} सही।",
    ),
    "t12.near_acc": ("pct", "{v} correct on similar new examples.", "मिलते-जुलते नए उदाहरणों में {v} सही।"),
    "t12.gain": ("pts", "Changed by {v} points after a short recap.", "छोटी दोहराई के बाद {v} अंक का बदलाव।"),
    "conf.abs_gap": ("pts", "Confidence and results differed by {v} points.", "भरोसे और नतीजों में {v} अंकों का अंतर।"),
    "conf.resolution": (
        "pts",
        "Felt surer on right answers than wrong ones by {v} points.",
        "सही उत्तरों पर गलत की तुलना में {v} अंक ज़्यादा पक्का महसूस किया।",
    ),
    "all.net_changes": ("signed", "Net effect of answer changes: {v}.", "उत्तर बदलने का कुल असर: {v}।"),
    "conf.hesitation_link": (
        "sec",
        "Paused {v} s longer before answers that turned out wrong.",
        "जो उत्तर गलत निकले उनसे पहले {v} सेकंड ज़्यादा रुके।",
    ),
    "t14.efficiency": (
        "pct",
        "Trip plans were {v} as efficient as the best route.",
        "यात्रा योजनाएँ सबसे अच्छे रास्ते जितनी {v} कुशल थीं।",
    ),
    "t14.plan_ratio": (
        "pct",
        "Spent {v} of the time planning before the first move.",
        "पहली चाल से पहले {v} समय योजना में लगाया।",
    ),
    "t14.restarts": ("num1", "Restarted plans {v} times on average.", "योजनाएँ औसतन {v} बार दोबारा शुरू कीं।"),
    "t5.first_click_ratio": (
        "pct",
        "Read the clues for {v} of the time before choosing.",
        "चुनने से पहले {v} समय सुराग पढ़े।",
    ),
    "t15.detection_rate": (
        "pct",
        "Found the planted mistake in {v} of worked plans.",
        "हल की गई योजनाओं में {v} में छिपी गलती पकड़ी।",
    ),
    "t15.review_net": (
        "signed",
        "Review of own answers changed results by {v}.",
        "अपने उत्तर दोबारा देखने से नतीजों में {v} बदलाव।",
    ),
    "t7.self_corrections": (
        "num1",
        "Corrected own reading slips {v} times per 100 words.",
        "हर 100 शब्दों में {v} बार अपनी पढ़ने की चूक सुधारी।",
    ),
    "t16.fit": ("pct", "Time plan matched time used at {v}.", "समय की योजना और लगे समय का मेल {v}।"),
    "t16.unfinished_share": ("pct", "Left {v} of timed puzzles unfinished.", "समयबद्ध पहेलियों में {v} अधूरी छोड़ीं।"),
    "t16.unused_share": ("pct", "Left {v} of the time unused.", "{v} समय बिना इस्तेमाल के छोड़ा।"),
    "t17.timeout_share": ("pct", "Ran out of time on {v} of timed items.", "{v} समयबद्ध प्रश्नों में समय खत्म हो गया।"),
    "conf.mean": ("conf4", "Average 'how sure' rating of {v} out of 4.", "'कितना पक्का' की औसत रेटिंग 4 में से {v}।"),
    "t18.hard_share": ("pct", "Chose the new, harder puzzle {v} of the time.", "{v} बार नई, कठिन पहेली चुनी।"),
    "all.hesitation": ("sec", "Usually started answering after {v} s.", "आमतौर पर {v} सेकंड बाद उत्तर देना शुरू किया।"),
    "t17.drop": (
        "pts",
        "Accuracy changed by {v} points from the relaxed to the timed round.",
        "आराम वाले से टाइमर वाले राउंड में सटीकता {v} अंक बदली।",
    ),
    "t17.change_skip_increase": (
        "pts",
        "Skipped or changed answers {v} points more often under the timer.",
        "टाइमर के साथ {v} अंक ज़्यादा बार उत्तर छोड़े या बदले।",
    ),
    "t17.rt_cv_change": (
        "pts",
        "Answer timing became {v} points less steady under the timer.",
        "टाइमर के साथ उत्तर देने का समय {v} अंक कम स्थिर रहा।",
    ),
    "t18.after_error_easy": (
        "pct",
        "Picked the easy option after a mistake {v} of the time.",
        "गलती के बाद {v} बार आसान विकल्प चुना।",
    ),
    "t18.bonus": ("pct", "Took the optional bonus round: {v}.", "वैकल्पिक बोनस राउंड लिया: {v}।"),
    "log.return_rate": (
        "pct",
        "Came back to the app between sessions on {v} of the gaps.",
        "सत्रों के बीच {v} अंतरालों में ऐप पर लौटे।",
    ),
    "t19.persist_s": (
        "num0",
        "Kept trying very hard puzzles for about {v} s each.",
        "बहुत कठिन पहेलियों पर हर एक पर लगभग {v} सेकंड कोशिश की।",
    ),
    "t19.attempts": ("num1", "Made {v} attempts per very hard puzzle.", "हर बहुत कठिन पहेली पर {v} कोशिशें कीं।"),
    "t20.retry_rate": ("pct", "Chose to try again after {v} of mistakes.", "{v} गलतियों के बाद दोबारा कोशिश करना चुना।"),
    "t20.retry_after_ability": (
        "pct",
        "Tried again after {v} of 'you are clever' style feedback.",
        "'तुम होशियार हो' जैसी प्रतिक्रिया के बाद {v} बार दोबारा कोशिश की।",
    ),
    "all.post_error_acc": (
        "pct",
        "{v} correct on the item right after a mistake.",
        "गलती के ठीक बाद वाले प्रश्न में {v} सही।",
    ),
    "log.on_schedule_rate": ("pct", "Did {v} of sessions on the planned day.", "{v} सत्र तय दिन पर किए।"),
    "log.completion_rate": ("pct", "Completed {v} of sessions.", "{v} सत्र पूरे किए।"),
    "t21.study_days": (
        "num0",
        "Reported studying on about {v} days last week.",
        "पिछले हफ़्ते लगभग {v} दिन पढ़ाई की बात बताई।",
    ),
    "t22.answered_rate": ("pct", "Answered {v} of conversation questions.", "बातचीत के {v} प्रश्नों के उत्तर दिए।"),
    "t22.mean_words": ("num0", "About {v} words per answer.", "हर उत्तर में लगभग {v} शब्द।"),
    "t22.speech_start_ms": ("sec", "Started speaking after about {v} s.", "लगभग {v} सेकंड बाद बोलना शुरू किया।"),
    "t11.word_count": ("num0", "About {v} words per explanation.", "हर व्याख्या में लगभग {v} शब्द।"),
    "t23.english_relative": (
        "pct",
        "English reasoning matched Hindi reasoning at {v}.",
        "अंग्रेज़ी में तर्क, हिंदी के तर्क से {v} मेल खाया।",
    ),
    "t23.en_acc": (
        "pct",
        "{v} correct on the English versions of the same puzzles.",
        "उन्हीं पहेलियों के अंग्रेज़ी संस्करण में {v} सही।",
    ),
    "t23.rt_ratio_inv": (
        "times",
        "English versions took {v} times as long as Hindi ones.",
        "अंग्रेज़ी संस्करण में हिंदी की तुलना में {v} गुना समय लगा।",
    ),
}


def fmt(kind: str, value: float) -> str:
    if kind == "pct":
        return f"{round(value * 100)}%"
    if kind == "num0":
        return f"{round(value)}"
    if kind == "num1":
        return f"{value:.1f}"
    if kind == "sec":
        return f"{value / 1000:.1f}"
    if kind == "pts":
        return f"{round(abs(value) * 100)}"
    if kind == "signed":
        return f"{'+' if value >= 0 else '−'}{round(abs(value) * 100)}%"
    if kind == "times":
        return f"{(1 / value if value else 0):.1f}"
    if kind == "conf4":
        return f"{1 + 3 * value:.1f}"
    return str(value)


def evidence_phrase(feature: str, value: float, lang: str) -> str | None:
    spec = EVIDENCE.get(feature)
    if spec is None:
        return None
    kind, en, hi = spec
    return (hi if lang == "hi" else en).format(v=fmt(kind, value))


# One action the student can take, in the student's own voice.
STUDENT_ACTION = {
    "working_memory": {
        "en": "Try saying a phone number backwards once a day.",
        "hi": "रोज़ एक बार कोई फ़ोन नंबर उल्टा बोलकर देखो।",
    },
    "long_term_recall": {
        "en": "Tell someone at home what you learned today, and again in two days.",
        "hi": "आज जो सीखा वह घर पर किसी को बताओ, और दो दिन बाद फिर से।",
    },
    "sustained_attention": {
        "en": "Study in 15-minute blocks with a short break in between.",
        "hi": "15 मिनट के हिस्सों में पढ़ो, बीच में छोटा ब्रेक लो।",
    },
    "processing_speed": {
        "en": "Go for accuracy first; speed will follow with practice.",
        "hi": "पहले सही करने पर ध्यान दो; अभ्यास से गति अपने आप आएगी।",
    },
    "logical_reasoning": {
        "en": "When a problem has many steps, write each step down.",
        "hi": "जब समस्या में कई कदम हों, तो हर कदम लिख लो।",
    },
    "pattern_spatial": {
        "en": "Try a jigsaw or a building-block puzzle this week.",
        "hi": "इस हफ़्ते कोई जिगसॉ या ब्लॉक वाली पहेली आज़माओ।",
    },
    "reading_fluency": {
        "en": "Read aloud for 10 minutes a day, anything you enjoy.",
        "hi": "रोज़ 10 मिनट ज़ोर से पढ़ो, जो भी तुम्हें पसंद हो।",
    },
    "reading_comprehension": {
        "en": "After reading, ask yourself 'why did that happen?'.",
        "hi": "पढ़ने के बाद खुद से पूछो, 'ऐसा क्यों हुआ?'।",
    },
    "vocabulary": {
        "en": "Pick one new word each day and use it in a sentence.",
        "hi": "हर दिन एक नया शब्द चुनो और उसे किसी वाक्य में इस्तेमाल करो।",
    },
    "number_sense": {
        "en": "Guess the total before paying at a shop, then check.",
        "hi": "दुकान पर भुगतान से पहले कुल रकम का अंदाज़ा लगाओ, फिर जाँचो।",
    },
    "expression": {
        "en": "Explain things using 'first', 'then' and 'because'.",
        "hi": "बातें 'पहले', 'फिर' और 'क्योंकि' से समझाओ।",
    },
    "concept_transfer": {
        "en": "After learning something, ask 'where else could I use this?'.",
        "hi": "कुछ सीखने के बाद पूछो, 'यह मैं और कहाँ इस्तेमाल कर सकता/सकती हूँ?'।",
    },
    "calibration": {
        "en": "Before checking your answers, mark the ones you are sure of.",
        "hi": "उत्तर जाँचने से पहले उन पर निशान लगाओ जिनके बारे में तुम पक्के हो।",
    },
    "strategy_planning": {
        "en": "Take one minute to plan before you start a big task.",
        "hi": "बड़ा काम शुरू करने से पहले एक मिनट योजना बनाओ।",
    },
    "error_detection": {
        "en": "Spend one minute checking your work before you hand it in.",
        "hi": "काम जमा करने से पहले एक मिनट जाँच करो।",
    },
    "time_management": {
        "en": "Before a test, decide how much time each part gets.",
        "hi": "परीक्षा से पहले तय करो कि हर हिस्से को कितना समय दोगे।",
    },
    "confidence": {
        "en": "Write down one thing you did well every day this week.",
        "hi": "इस हफ़्ते हर दिन एक बात लिखो जो तुमने अच्छी की।",
    },
    "pressure_sensitivity": {
        "en": "Practise short timed puzzles just for fun, and notice your calm breaths.",
        "hi": "मज़े के लिए छोटी समयबद्ध पहेलियाँ करो, और अपनी शांत साँसों पर ध्यान दो।",
    },
    "motivation": {
        "en": "Pick one harder challenge this week, just to see what happens.",
        "hi": "इस हफ़्ते एक कठिन चुनौती चुनो, बस यह देखने के लिए कि क्या होता है।",
    },
    "resilience": {
        "en": "After a mistake, take a breath and try the next one fresh.",
        "hi": "गलती के बाद एक साँस लो और अगला सवाल नए सिरे से करो।",
    },
    "growth_mindset": {
        "en": "When something goes wrong, try it once more another way.",
        "hi": "जब कुछ गलत हो, तो उसे एक बार दूसरे तरीके से फिर आज़माओ।",
    },
    "study_consistency": {
        "en": "Choose a fixed 20-minute study time each day.",
        "hi": "हर दिन पढ़ाई के लिए 20 मिनट का एक तय समय चुनो।",
    },
    "communication": {
        "en": "Share one idea in class this week, in writing or out loud.",
        "hi": "इस हफ़्ते कक्षा में एक विचार साझा करो, लिखकर या बोलकर।",
    },
    "language_comfort": {
        "en": "Read a short English story and the same story in Hindi.",
        "hi": "एक छोटी अंग्रेज़ी कहानी और वही कहानी हिंदी में पढ़ो।",
    },
}
