"""T2 Delayed Recall info cards. Each card has detail questions and recognition questions; recognition
lures ("was X on the card?" when it was not) measure false items added."""

CARDS = [
    {
        "band": "11-14",
        "en": {
            "title": "Sports Day Notice",
            "lines": [
                "Event: Inter-house relay race",
                "Day: Thursday",
                "Time: 8:30 in the morning",
                "Place: Back ground, near the water tank",
                "Bring: Water bottle and cap",
                "Green House wears green bands",
                "Contact: Coach Meera",
            ],
            "detail": [
                ("What day is the race?", ["Thursday", "Tuesday", "Saturday", "Monday"]),
                (
                    "What time does it start?",
                    ["8:30 in the morning", "9:00 in the morning", "7:30 in the morning", "10:30 in the morning"],
                ),
                (
                    "Where is the race?",
                    ["Near the water tank", "Near the main gate", "In the hall", "Near the canteen"],
                ),
                ("Who is the contact?", ["Coach Meera", "Coach Ravi", "Ms. Anita", "Mr. Joseph"]),
            ],
            "recognition": [("water bottle", True), ("cap", True), ("umbrella", False), ("Coach Ravi", False)],
        },
        "hi": {
            "title": "खेल दिवस सूचना",
            "lines": [
                "कार्यक्रम: हाउस के बीच रिले दौड़",
                "दिन: गुरुवार",
                "समय: सुबह 8:30",
                "जगह: पीछे का मैदान, पानी की टंकी के पास",
                "साथ लाएँ: पानी की बोतल और टोपी",
                "ग्रीन हाउस हरे बैंड पहनेगा",
                "संपर्क: कोच मीरा",
            ],
            "detail": [
                ("दौड़ किस दिन है?", ["गुरुवार", "मंगलवार", "शनिवार", "सोमवार"]),
                ("दौड़ कब शुरू होगी?", ["सुबह 8:30", "सुबह 9:00", "सुबह 7:30", "सुबह 10:30"]),
                ("दौड़ कहाँ है?", ["पानी की टंकी के पास", "मुख्य गेट के पास", "हॉल में", "कैंटीन के पास"]),
                ("संपर्क कौन है?", ["कोच मीरा", "कोच रवि", "अनीता मैडम", "जोसेफ़ सर"]),
            ],
            "recognition": [("पानी की बोतल", True), ("टोपी", True), ("छाता", False), ("कोच रवि", False)],
        },
        "hinglish": {
            "title": "Sports Day Notice",
            "lines": [
                "Event: House ke beech relay race",
                "Din: Guruvaar (Thursday)",
                "Time: Subah 8:30",
                "Jagah: Peeche ka ground, paani ki tanki ke paas",
                "Saath laayein: Paani ki bottle aur topi",
                "Green House hare band pehnega",
                "Contact: Coach Meera",
            ],
            "detail": [
                ("Race kis din hai?", ["Guruvaar", "Mangalvaar", "Shanivaar", "Somvaar"]),
                ("Race kab shuru hogi?", ["Subah 8:30", "Subah 9:00", "Subah 7:30", "Subah 10:30"]),
                ("Race kahan hai?", ["Paani ki tanki ke paas", "Main gate ke paas", "Hall mein", "Canteen ke paas"]),
                ("Contact kaun hai?", ["Coach Meera", "Coach Ravi", "Anita Madam", "Joseph Sir"]),
            ],
            "recognition": [("paani ki bottle", True), ("topi", True), ("chhaata", False), ("Coach Ravi", False)],
        },
    },
    {
        "band": "11-14",
        "en": {
            "title": "Library Card",
            "lines": [
                "Name: Kabir Shah",
                "Book: The Red Kite",
                "Borrowed on: 4 June",
                "Return by: 18 June",
                "Late fee: 2 rupees per day",
                "Shelf: C-12",
                "Counter open: 10 to 4",
            ],
            "detail": [
                ("What is the name of the book?", ["The Red Kite", "The Blue Boat", "The Red Fort", "The Lost Kite"]),
                ("By when must it be returned?", ["18 June", "4 June", "14 June", "28 June"]),
                (
                    "What is the late fee?",
                    ["2 rupees per day", "5 rupees per day", "2 rupees per week", "10 rupees in total"],
                ),
                ("Which shelf is it from?", ["C-12", "B-12", "C-21", "A-10"]),
            ],
            "recognition": [("Kabir Shah", True), ("Shelf", True), ("Phone number", False), ("Gate pass", False)],
        },
        "hi": {
            "title": "लाइब्रेरी कार्ड",
            "lines": [
                "नाम: कबीर शाह",
                "किताब: लाल पतंग",
                "लेने की तारीख: 4 जून",
                "लौटाने की तारीख: 18 जून",
                "देरी का शुल्क: 2 रुपये प्रतिदिन",
                "शेल्फ़: C-12",
                "काउंटर खुला: 10 से 4",
            ],
            "detail": [
                ("किताब का नाम क्या है?", ["लाल पतंग", "नीली नाव", "लाल किला", "खोई पतंग"]),
                ("किताब कब तक लौटानी है?", ["18 जून", "4 जून", "14 जून", "28 जून"]),
                ("देरी का शुल्क कितना है?", ["2 रुपये प्रतिदिन", "5 रुपये प्रतिदिन", "2 रुपये प्रति सप्ताह", "कुल 10 रुपये"]),
                ("किताब किस शेल्फ़ की है?", ["C-12", "B-12", "C-21", "A-10"]),
            ],
            "recognition": [("कबीर शाह", True), ("शेल्फ़", True), ("फ़ोन नंबर", False), ("गेट पास", False)],
        },
        "hinglish": {
            "title": "Library Card",
            "lines": [
                "Naam: Kabir Shah",
                "Kitaab: Laal Patang",
                "Lene ki date: 4 June",
                "Lautane ki date: 18 June",
                "Late fee: 2 rupaye roz",
                "Shelf: C-12",
                "Counter khula: 10 se 4",
            ],
            "detail": [
                ("Kitaab ka naam kya hai?", ["Laal Patang", "Neeli Naav", "Laal Qila", "Khoyi Patang"]),
                ("Kitaab kab tak lautani hai?", ["18 June", "4 June", "14 June", "28 June"]),
                ("Late fee kitni hai?", ["2 rupaye roz", "5 rupaye roz", "2 rupaye har hafte", "Total 10 rupaye"]),
                ("Kitaab kis shelf ki hai?", ["C-12", "B-12", "C-21", "A-10"]),
            ],
            "recognition": [("Kabir Shah", True), ("Shelf", True), ("Phone number", False), ("Gate pass", False)],
        },
    },
    {
        "band": "15-18",
        "en": {
            "title": "Monthly Bus Pass",
            "lines": [
                "Route 47: Gandhi Chowk to City Market",
                "Valid till: 31 August",
                "Monthly fare: 350 rupees",
                "First bus 6:15 am, last bus 9:40 pm",
                "Pass number: 4471",
                "Lost pass fee: 50 rupees",
                "Renew at Window 3",
            ],
            "detail": [
                ("Which route is the pass for?", ["Route 47", "Route 74", "Route 41", "Route 17"]),
                ("When does the last bus leave?", ["9:40 pm", "9:15 pm", "10:40 pm", "8:40 pm"]),
                ("What is the monthly fare?", ["350 rupees", "300 rupees", "530 rupees", "450 rupees"]),
                ("Where can the pass be renewed?", ["Window 3", "Window 7", "The depot office", "Online only"]),
            ],
            "recognition": [
                ("City Market", True),
                ("Lost pass fee", True),
                ("Student discount", False),
                ("Railway station", False),
            ],
        },
        "hi": {
            "title": "मासिक बस पास",
            "lines": [
                "रूट 47: गांधी चौक से सिटी मार्केट",
                "वैधता: 31 अगस्त तक",
                "मासिक किराया: 350 रुपये",
                "पहली बस सुबह 6:15, आखिरी बस रात 9:40",
                "पास नंबर: 4471",
                "पास खोने का शुल्क: 50 रुपये",
                "खिड़की 3 पर नवीनीकरण",
            ],
            "detail": [
                ("पास किस रूट का है?", ["रूट 47", "रूट 74", "रूट 41", "रूट 17"]),
                ("आखिरी बस कब चलती है?", ["रात 9:40", "रात 9:15", "रात 10:40", "रात 8:40"]),
                ("मासिक किराया कितना है?", ["350 रुपये", "300 रुपये", "530 रुपये", "450 रुपये"]),
                ("पास का नवीनीकरण कहाँ होता है?", ["खिड़की 3", "खिड़की 7", "डिपो ऑफ़िस", "सिर्फ़ ऑनलाइन"]),
            ],
            "recognition": [("सिटी मार्केट", True), ("पास खोने का शुल्क", True), ("छात्र छूट", False), ("रेलवे स्टेशन", False)],
        },
        "hinglish": {
            "title": "Monthly Bus Pass",
            "lines": [
                "Route 47: Gandhi Chowk se City Market",
                "Valid: 31 August tak",
                "Monthly kiraya: 350 rupaye",
                "Pehli bus subah 6:15, aakhri bus raat 9:40",
                "Pass number: 4471",
                "Pass khone ki fee: 50 rupaye",
                "Window 3 par renew",
            ],
            "detail": [
                ("Pass kis route ka hai?", ["Route 47", "Route 74", "Route 41", "Route 17"]),
                ("Aakhri bus kab chalti hai?", ["Raat 9:40", "Raat 9:15", "Raat 10:40", "Raat 8:40"]),
                ("Monthly kiraya kitna hai?", ["350 rupaye", "300 rupaye", "530 rupaye", "450 rupaye"]),
                ("Pass kahan renew hota hai?", ["Window 3", "Window 7", "Depot office", "Sirf online"]),
            ],
            "recognition": [
                ("City Market", True),
                ("Pass khone ki fee", True),
                ("Student discount", False),
                ("Railway station", False),
            ],
        },
    },
    {
        "band": "15-18",
        "en": {
            "title": "Robotics Workshop",
            "lines": [
                "Day: Saturday, 14 September",
                "Place: Lab 2, second floor",
                "Time: 10:00 to 12:30",
                "Bring: Notebook and pencil",
                "Seats: 24",
                "Register with Ms. Farida by Wednesday",
                "Fee: None",
            ],
            "detail": [
                (
                    "Where is the workshop?",
                    ["Lab 2, second floor", "Lab 3, first floor", "The library", "Lab 2, ground floor"],
                ),
                ("How many seats are there?", ["24", "42", "20", "30"]),
                ("Who takes registrations?", ["Ms. Farida", "Mr. Fernandes", "Ms. Fatima", "The principal"]),
                ("Register by which day?", ["Wednesday", "Saturday", "Monday", "Friday"]),
            ],
            "recognition": [("Notebook", True), ("Fee", True), ("Laptop", False), ("Lunch provided", False)],
        },
        "hi": {
            "title": "रोबोटिक्स वर्कशॉप",
            "lines": [
                "दिन: शनिवार, 14 सितंबर",
                "जगह: लैब 2, दूसरी मंज़िल",
                "समय: 10:00 से 12:30",
                "साथ लाएँ: कॉपी और पेंसिल",
                "सीटें: 24",
                "बुधवार तक फ़रीदा मैडम के पास नाम लिखवाएँ",
                "शुल्क: कोई नहीं",
            ],
            "detail": [
                ("वर्कशॉप कहाँ है?", ["लैब 2, दूसरी मंज़िल", "लैब 3, पहली मंज़िल", "लाइब्रेरी", "लैब 2, भूतल"]),
                ("कितनी सीटें हैं?", ["24", "42", "20", "30"]),
                ("नाम कौन लिखेगा?", ["फ़रीदा मैडम", "फ़र्नांडिस सर", "फ़ातिमा मैडम", "प्रिंसिपल"]),
                ("किस दिन तक नाम लिखवाना है?", ["बुधवार", "शनिवार", "सोमवार", "शुक्रवार"]),
            ],
            "recognition": [("कॉपी", True), ("शुल्क", True), ("लैपटॉप", False), ("दोपहर का खाना", False)],
        },
        "hinglish": {
            "title": "Robotics Workshop",
            "lines": [
                "Din: Shanivaar, 14 September",
                "Jagah: Lab 2, doosri manzil",
                "Time: 10:00 se 12:30",
                "Saath laayein: Copy aur pencil",
                "Seats: 24",
                "Budhvaar tak Farida Madam ke paas naam likhwayein",
                "Fee: Koi nahi",
            ],
            "detail": [
                (
                    "Workshop kahan hai?",
                    ["Lab 2, doosri manzil", "Lab 3, pehli manzil", "Library", "Lab 2, ground floor"],
                ),
                ("Kitni seats hain?", ["24", "42", "20", "30"]),
                ("Naam kaun likhega?", ["Farida Madam", "Fernandes Sir", "Fatima Madam", "Principal"]),
                ("Kis din tak naam likhwana hai?", ["Budhvaar", "Shanivaar", "Somvaar", "Shukravaar"]),
            ],
            "recognition": [("Copy", True), ("Fee", True), ("Laptop", False), ("Lunch", False)],
        },
    },
]

RECOGNITION_PROMPT = {
    "en": "Was “{x}” on the card?",
    "hi": "क्या कार्ड पर “{x}” लिखा था?",
    "hinglish": "Kya card par “{x}” likha tha?",
}
YES_NO = {
    "en": ("Yes", "No"),
    "hi": ("हाँ", "नहीं"),
    "hinglish": ("Haan", "Nahi"),
}
