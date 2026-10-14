"""T11 situations, T15 worked plans with one planted mistake, T21 habit questions, T22 conversation prompts."""

# T15: (level, setup, steps, index of the wrong step)
WORKED = {
    "en": [
        (
            3,
            "Ravi buys 3 pens at ₹12 each and a notebook at ₹45. He pays with a ₹100 note.",
            [
                "The pens cost 3 × 12 = ₹36.",
                "Pens and notebook together cost 36 + 45 = ₹71.",
                "His change is 100 − 71 = ₹29.",
            ],
            1,
        ),
        (
            4,
            "The bus leaves at 8:20 and the ride takes 25 minutes. The walk from the stop takes 10 minutes. "
            "School starts at 9:00.",
            [
                "The bus reaches the stop at 8:45.",
                "After the walk, Asha reaches school at 8:55.",
                "So she has 15 minutes to spare before school starts.",
            ],
            2,
        ),
        (
            4,
            "A recipe for 4 people needs 2 cups of rice. Priya is cooking for 6 people.",
            [
                "For 2 people you need 1 cup of rice.",
                "6 people is 3 groups of 2 people.",
                "So Priya needs 4 cups of rice.",
            ],
            2,
        ),
        (
            5,
            "A box holds 12 mangoes. Dev has 40 mangoes to pack.",
            [
                "3 boxes hold 36 mangoes.",
                "40 − 36 = 4 mangoes are left over.",
                "So 3 boxes are enough for all the mangoes.",
            ],
            2,
        ),
        (
            6,
            "Today is Monday, 10 June. The library book is due in 9 days.",
            [
                "7 days from today is Monday, 17 June.",
                "2 more days after that is Thursday, 19 June.",
                "So the book is due on 19 June.",
            ],
            1,
        ),
        (
            7,
            "Neha saves ₹30 every week. She wants a water bottle that costs ₹200.",
            [
                "After 5 weeks she has 5 × 30 = ₹150.",
                "After 6 weeks she has ₹180, which is not enough.",
                "After 7 weeks she has exactly ₹200.",
            ],
            2,
        ),
    ],
    "hi": [
        (
            3,
            "रवि ₹12 वाले 3 पेन और ₹45 की एक कॉपी खरीदता है। वह ₹100 का नोट देता है।",
            ["पेन की कीमत 3 × 12 = ₹36 है।", "पेन और कॉपी मिलाकर 36 + 45 = ₹71 हुए।", "उसे 100 − 71 = ₹29 वापस मिलेंगे।"],
            1,
        ),
        (
            4,
            "बस 8:20 पर चलती है और सफ़र 25 मिनट का है। स्टॉप से पैदल 10 मिनट लगते हैं। स्कूल 9:00 बजे शुरू होता है।",
            [
                "बस 8:45 पर स्टॉप पहुँचती है।",
                "पैदल चलकर आशा 8:55 पर स्कूल पहुँचती है।",
                "इसलिए स्कूल शुरू होने से पहले उसके पास 15 मिनट बचते हैं।",
            ],
            2,
        ),
        (
            4,
            "4 लोगों की एक रेसिपी में 2 कप चावल लगते हैं। प्रिया 6 लोगों के लिए खाना बना रही है।",
            ["2 लोगों के लिए 1 कप चावल चाहिए।", "6 लोग यानी 2-2 लोगों के 3 समूह।", "इसलिए प्रिया को 4 कप चावल चाहिए।"],
            2,
        ),
        (
            5,
            "एक डिब्बे में 12 आम आते हैं। देव के पास पैक करने के लिए 40 आम हैं।",
            ["3 डिब्बों में 36 आम आते हैं।", "40 − 36 = 4 आम बच जाते हैं।", "इसलिए सारे आमों के लिए 3 डिब्बे काफ़ी हैं।"],
            2,
        ),
        (
            6,
            "आज सोमवार, 10 जून है। लाइब्रेरी की किताब 9 दिन में लौटानी है।",
            ["आज से 7 दिन बाद सोमवार, 17 जून है।", "उसके 2 दिन बाद गुरुवार, 19 जून है।", "इसलिए किताब 19 जून को लौटानी है।"],
            1,
        ),
        (
            7,
            "नेहा हर हफ़्ते ₹30 बचाती है। उसे ₹200 की पानी की बोतल चाहिए।",
            [
                "5 हफ़्ते बाद उसके पास 5 × 30 = ₹150 होंगे।",
                "6 हफ़्ते बाद ₹180 होंगे, जो काफ़ी नहीं है।",
                "7 हफ़्ते बाद उसके पास ठीक ₹200 होंगे।",
            ],
            2,
        ),
    ],
    "hinglish": [
        (
            3,
            "Ravi ₹12 wale 3 pen aur ₹45 ki ek copy khareedta hai. Woh ₹100 ka note deta hai.",
            [
                "Pen ki keemat 3 × 12 = ₹36 hai.",
                "Pen aur copy milakar 36 + 45 = ₹71 hue.",
                "Use 100 − 71 = ₹29 wapas milenge.",
            ],
            1,
        ),
        (
            4,
            "Bus 8:20 par chalti hai aur safar 25 minute ka hai. Stop se paidal 10 minute lagte hain. School 9:00 baje "
            "shuru hota hai.",
            [
                "Bus 8:45 par stop pahunchti hai.",
                "Paidal chalkar Asha 8:55 par school pahunchti hai.",
                "Isliye school shuru hone se pehle uske paas 15 minute bachte hain.",
            ],
            2,
        ),
        (
            4,
            "4 logon ki ek recipe mein 2 cup chawal lagte hain. Priya 6 logon ke liye khaana bana rahi hai.",
            [
                "2 logon ke liye 1 cup chawal chahiye.",
                "6 log yaani 2-2 logon ke 3 group.",
                "Isliye Priya ko 4 cup chawal chahiye.",
            ],
            2,
        ),
        (
            5,
            "Ek dabbe mein 12 aam aate hain. Dev ke paas pack karne ke liye 40 aam hain.",
            [
                "3 dabbon mein 36 aam aate hain.",
                "40 − 36 = 4 aam bach jaate hain.",
                "Isliye saare aamon ke liye 3 dabbe kaafi hain.",
            ],
            2,
        ),
        (
            6,
            "Aaj Somvaar, 10 June hai. Library ki kitaab 9 din mein lautani hai.",
            [
                "Aaj se 7 din baad Somvaar, 17 June hai.",
                "Uske 2 din baad Guruvaar, 19 June hai.",
                "Isliye kitaab 19 June ko lautani hai.",
            ],
            1,
        ),
        (
            7,
            "Neha har hafte ₹30 bachati hai. Use ₹200 ki paani ki bottle chahiye.",
            [
                "5 hafte baad uske paas 5 × 30 = ₹150 honge.",
                "6 hafte baad ₹180 honge, jo kaafi nahi hai.",
                "7 hafte baad uske paas theek ₹200 honge.",
            ],
            2,
        ),
    ],
}

WORKED_PROMPT = {
    "en": "Which step has the mistake?",
    "hi": "किस कदम में गलती है?",
    "hinglish": "Kis step mein galti hai?",
}
STEP_LABEL = {"en": "Step {n}", "hi": "कदम {n}", "hinglish": "Step {n}"}

# T11: (prompt, keywords used for the on-device completeness feature)
SITUATIONS = {
    "en": [
        (
            "The queue at the school water cooler is very long and the bell will ring in two minutes. What could "
            "happen next, and what would you do?",
            ["late", "bell", "wait", "bottle", "turn", "class", "share", "teacher"],
        ),
        (
            "Your friend's bicycle chain keeps slipping off on the way home. Explain what might be wrong and how "
            "you could help.",
            ["chain", "loose", "tight", "oil", "walk", "repair", "shop", "help"],
        ),
        (
            "A shop has a sign: 'Buy 2, get 1 free'. Your mother needs only 2 packets. Explain whether the offer "
            "helps her.",
            ["free", "extra", "need", "waste", "price", "save", "share", "packet"],
        ),
        (
            "It rained all night and the road to school is flooded. Explain two safe ways to get to school.",
            ["water", "road", "safe", "bus", "walk", "adult", "wait", "another"],
        ),
    ],
    "hi": [
        (
            "स्कूल के वाटर कूलर पर बहुत लंबी लाइन है और दो मिनट में घंटी बजने वाली है। आगे क्या हो सकता है, और तुम क्या करोगे?",
            ["देर", "घंटी", "इंतज़ार", "बोतल", "बारी", "कक्षा", "बाँट", "शिक्षक"],
        ),
        (
            "घर लौटते समय तुम्हारे दोस्त की साइकिल की चेन बार-बार उतर जाती है। समझाओ कि क्या खराब हो सकता है और तुम कैसे मदद कर सकते हो।",
            ["चेन", "ढीली", "कस", "तेल", "पैदल", "मरम्मत", "दुकान", "मदद"],
        ),
        (
            "एक दुकान पर लिखा है: '2 खरीदो, 1 मुफ़्त'। तुम्हारी माँ को सिर्फ़ 2 पैकेट चाहिए। समझाओ कि यह ऑफ़र उनके काम का है या नहीं।",
            ["मुफ़्त", "ज़्यादा", "ज़रूरत", "बर्बाद", "दाम", "बचत", "बाँट", "पैकेट"],
        ),
        (
            "रात भर बारिश हुई और स्कूल की सड़क पर पानी भर गया है। स्कूल पहुँचने के दो सुरक्षित तरीके समझाओ।",
            ["पानी", "सड़क", "सुरक्षित", "बस", "पैदल", "बड़े", "इंतज़ार", "दूसरा"],
        ),
    ],
    "hinglish": [
        (
            "School ke water cooler par bahut lambi line hai aur do minute mein bell bajne wali hai. Aage kya ho sakta "
            "hai, aur tum kya karoge?",
            ["late", "bell", "wait", "bottle", "baari", "class", "share", "teacher"],
        ),
        (
            "Ghar laut-te time tumhare dost ki cycle ki chain baar-baar utar jaati hai. Samjhao ki kya kharab ho sakta "
            "hai aur tum kaise madad kar sakte ho.",
            ["chain", "dheeli", "tight", "tel", "paidal", "repair", "dukaan", "madad"],
        ),
        (
            "Ek dukaan par likha hai: '2 khareedo, 1 free'. Tumhari mummy ko sirf 2 packet chahiye. Samjhao ki yeh offer "
            "unke kaam ka hai ya nahi.",
            ["free", "extra", "zaroorat", "waste", "daam", "bachat", "share", "packet"],
        ),
        (
            "Raat bhar baarish hui aur school ki sadak par paani bhar gaya hai. School pahunchne ke do safe tareeke samjhao.",
            ["paani", "sadak", "safe", "bus", "paidal", "bade", "wait", "doosra"],
        ),
    ],
}

# T21: behaviour-anchored habit questions: (id, prompt, [(label, value)])
HABITS = {
    "en": [
        (
            "study_days",
            "Last week, on how many days did you study on your own for 20 minutes or more?",
            [("None", 0), ("1 or 2 days", 1.5), ("3 or 4 days", 3.5), ("5 or 6 days", 5.5), ("Every day", 7)],
        ),
        (
            "self_start",
            "Last week, how many times did you start homework without anyone reminding you?",
            [("Never", 0), ("1 or 2 times", 1.5), ("3 or 4 times", 3.5), ("5 or more times", 5.5)],
        ),
        (
            "plan_days",
            "Last week, on how many days did you decide what to study before you started?",
            [("None", 0), ("1 or 2 days", 1.5), ("3 or 4 days", 3.5), ("5 or more days", 5.5)],
        ),
        (
            "stuck",
            "When you get stuck on homework, what do you usually do first?",
            [
                ("Leave it", 0),
                ("Ask someone straight away", 1),
                ("Look at my notes or an example", 2),
                ("Try another way for a few minutes", 3),
            ],
        ),
        (
            "focus_span",
            "How long can you usually study before you check a phone or the TV?",
            [
                ("Less than 5 minutes", 2.5),
                ("5 to 15 minutes", 10),
                ("15 to 30 minutes", 22.5),
                ("More than 30 minutes", 40),
            ],
        ),
        (
            "review_days",
            "Last week, on how many days did you go over something you learned that day?",
            [("None", 0), ("1 or 2 days", 1.5), ("3 or 4 days", 3.5), ("5 or more days", 5.5)],
        ),
    ],
    "hi": [
        (
            "study_days",
            "पिछले हफ़्ते, कितने दिन तुमने खुद से 20 मिनट या उससे ज़्यादा पढ़ाई की?",
            [("एक भी नहीं", 0), ("1 या 2 दिन", 1.5), ("3 या 4 दिन", 3.5), ("5 या 6 दिन", 5.5), ("हर दिन", 7)],
        ),
        (
            "self_start",
            "पिछले हफ़्ते, कितनी बार तुमने बिना किसी के याद दिलाए होमवर्क शुरू किया?",
            [("कभी नहीं", 0), ("1 या 2 बार", 1.5), ("3 या 4 बार", 3.5), ("5 या ज़्यादा बार", 5.5)],
        ),
        (
            "plan_days",
            "पिछले हफ़्ते, कितने दिन तुमने पढ़ाई शुरू करने से पहले तय किया कि क्या पढ़ना है?",
            [("एक भी नहीं", 0), ("1 या 2 दिन", 1.5), ("3 या 4 दिन", 3.5), ("5 या ज़्यादा दिन", 5.5)],
        ),
        (
            "stuck",
            "होमवर्क में अटकने पर तुम आमतौर पर सबसे पहले क्या करते हो?",
            [
                ("छोड़ देता/देती हूँ", 0),
                ("तुरंत किसी से पूछता/पूछती हूँ", 1),
                ("नोट्स या उदाहरण देखता/देखती हूँ", 2),
                ("कुछ मिनट दूसरा तरीका आज़माता/आज़माती हूँ", 3),
            ],
        ),
        (
            "focus_span",
            "फ़ोन या टीवी देखने से पहले तुम आमतौर पर कितनी देर पढ़ पाते हो?",
            [("5 मिनट से कम", 2.5), ("5 से 15 मिनट", 10), ("15 से 30 मिनट", 22.5), ("30 मिनट से ज़्यादा", 40)],
        ),
        (
            "review_days",
            "पिछले हफ़्ते, कितने दिन तुमने उसी दिन सीखी किसी बात को दोहराया?",
            [("एक भी नहीं", 0), ("1 या 2 दिन", 1.5), ("3 या 4 दिन", 3.5), ("5 या ज़्यादा दिन", 5.5)],
        ),
    ],
    "hinglish": [
        (
            "study_days",
            "Pichhle hafte, kitne din tumne khud se 20 minute ya usse zyada padhai ki?",
            [("Ek bhi nahi", 0), ("1 ya 2 din", 1.5), ("3 ya 4 din", 3.5), ("5 ya 6 din", 5.5), ("Har din", 7)],
        ),
        (
            "self_start",
            "Pichhle hafte, kitni baar tumne bina kisi ke yaad dilaye homework shuru kiya?",
            [("Kabhi nahi", 0), ("1 ya 2 baar", 1.5), ("3 ya 4 baar", 3.5), ("5 ya zyada baar", 5.5)],
        ),
        (
            "plan_days",
            "Pichhle hafte, kitne din tumne padhai shuru karne se pehle decide kiya ki kya padhna hai?",
            [("Ek bhi nahi", 0), ("1 ya 2 din", 1.5), ("3 ya 4 din", 3.5), ("5 ya zyada din", 5.5)],
        ),
        (
            "stuck",
            "Homework mein atakne par tum aamtaur par sabse pehle kya karte ho?",
            [
                ("Chhod deta/deti hoon", 0),
                ("Turant kisi se poochhta/poochhti hoon", 1),
                ("Notes ya example dekhta/dekhti hoon", 2),
                ("Kuch minute doosra tareeka try karta/karti hoon", 3),
            ],
        ),
        (
            "focus_span",
            "Phone ya TV dekhne se pehle tum aamtaur par kitni der padh paate ho?",
            [("5 minute se kam", 2.5), ("5 se 15 minute", 10), ("15 se 30 minute", 22.5), ("30 minute se zyada", 40)],
        ),
        (
            "review_days",
            "Pichhle hafte, kitne din tumne usi din seekhi kisi baat ko dohraya?",
            [("Ek bhi nahi", 0), ("1 ya 2 din", 1.5), ("3 ya 4 din", 3.5), ("5 ya zyada din", 5.5)],
        ),
    ],
}

# T22 prompts
CONVERSATION = {
    "en": [
        "Tell me about what you did yesterday after school.",
        "Tell me about a problem you solved recently. What did you do?",
        "Tell me about a choice you made this week. Why did you choose that?",
        "What is something you would like to get better at, and why?",
        "Describe your favourite place to spend time. What makes it special?",
    ],
    "hi": [
        "मुझे बताओ कि कल स्कूल के बाद तुमने क्या किया।",
        "हाल ही में तुमने कोई समस्या सुलझाई हो, उसके बारे में बताओ। तुमने क्या किया?",
        "इस हफ़्ते तुमने कोई चुनाव किया हो, उसके बारे में बताओ। तुमने वही क्यों चुना?",
        "ऐसी कौन-सी चीज़ है जिसमें तुम और अच्छे होना चाहते हो, और क्यों?",
        "समय बिताने की अपनी पसंदीदा जगह के बारे में बताओ। वह खास क्यों है?",
    ],
    "hinglish": [
        "Mujhe batao ki kal school ke baad tumne kya kiya.",
        "Haal hi mein tumne koi problem solve ki ho, uske baare mein batao. Tumne kya kiya?",
        "Is hafte tumne koi choice ki ho, uske baare mein batao. Tumne wahi kyun chuna?",
        "Aisi kaun si cheez hai jismein tum aur achchhe hona chahte ho, aur kyun?",
        "Time bitaane ki apni favourite jagah ke baare mein batao. Woh special kyun hai?",
    ],
}
