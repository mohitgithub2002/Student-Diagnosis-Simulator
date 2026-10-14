"""T9 Word in Context. First option is correct (options are shuffled at build time). Levels 1-10 by
rarity; age band 11-14 uses levels 1-7 and 15-18 uses levels 4-10."""

WORDS = {
    "en": [
        (
            1,
            "drowsy",
            "The puppy was so drowsy after its long walk that it fell asleep on the mat.",
            ["Sleepy", "Angry", "Hungry", "Scared"],
        ),
        (
            2,
            "scalding",
            "The soup was so scalding that Asha waited ten minutes before tasting it.",
            ["Very hot", "Very salty", "Very thick", "Very cold"],
        ),
        (
            3,
            "famished",
            "Ravi was famished after the match and ate three plates of rice.",
            ["Very hungry", "Very tired", "Very happy", "Very sick"],
        ),
        (
            3,
            "fragile",
            "The old bridge was so fragile that only one person could cross it at a time.",
            ["Easily broken", "Very long", "Newly painted", "Very crowded"],
        ),
        (
            4,
            "candid",
            "Meena gave a candid answer; she told us exactly what she thought, even though it was not polite.",
            ["Honest and direct", "Short and quick", "Polite and careful", "Funny and silly"],
        ),
        (
            5,
            "ambiguous",
            "The rules were ambiguous, so half the class understood them one way and half another way.",
            ["Able to mean more than one thing", "Very strict", "Easy to follow", "Written in red"],
        ),
        (
            5,
            "strewn",
            "After the storm, the street was strewn with leaves, branches and plastic bags.",
            ["Scattered untidily", "Neatly swept", "Freshly painted", "Completely blocked by water"],
        ),
        (
            6,
            "frugal",
            "The shopkeeper was so frugal that he reused every paper bag until it tore.",
            ["Careful not to waste anything", "Very rich", "Very lazy", "Unkind to customers"],
        ),
        (
            6,
            "plausible",
            "Her excuse was plausible: the trains really were late that morning.",
            ["Believable", "Silly", "Very long", "Rude"],
        ),
        (
            7,
            "effusive",
            "The teacher's praise was so effusive that Arjun turned red with embarrassment.",
            ["Very warm and over the top", "Quiet and short", "Unfair", "Hard to hear"],
        ),
        (
            8,
            "convoluted",
            "The plan was so convoluted that even the person who made it needed a diagram to explain it.",
            ["Very complicated", "Very cheap", "Very old", "Very secret"],
        ),
        (
            8,
            "ubiquitous",
            "In July, rain in Cherrapunji is ubiquitous; it seems to be everywhere, all the time.",
            ["Found everywhere", "Very rare", "Very gentle", "Very dangerous"],
        ),
        (
            9,
            "laconic",
            "His laconic reply, just one word, told us nothing about the trip.",
            ["Using very few words", "Very loud", "Very rude", "Full of jokes"],
        ),
        (
            10,
            "exorbitant",
            "The prices were exorbitant, so we walked to the next market where everything cost half as much.",
            ["Far too high", "Fair and low", "Written wrongly", "Changing every hour"],
        ),
    ],
    "hi": [
        (1, "उनींदा", "लंबी सैर के बाद पिल्ला इतना उनींदा था कि चटाई पर ही सो गया।", ["नींद से भरा", "गुस्से में", "भूखा", "डरा हुआ"]),
        (
            2,
            "खौलता",
            "सूप इतना खौलता हुआ था कि आशा ने चखने से पहले दस मिनट इंतज़ार किया।",
            ["बहुत गरम", "बहुत नमकीन", "बहुत गाढ़ा", "बहुत ठंडा"],
        ),
        (
            3,
            "क्षुधित",
            "मैच के बाद रवि इतना क्षुधित था कि उसने चावल की तीन प्लेटें खा लीं।",
            ["बहुत भूखा", "बहुत थका", "बहुत खुश", "बहुत बीमार"],
        ),
        (
            3,
            "जर्जर",
            "पुराना पुल इतना जर्जर था कि एक बार में एक ही व्यक्ति उसे पार कर सकता था।",
            ["कमज़ोर और टूटा-फूटा", "बहुत लंबा", "नया रंगा हुआ", "भीड़ से भरा"],
        ),
        (
            4,
            "स्पष्टवादी",
            "मीना स्पष्टवादी है; वह जो सोचती है वही साफ़-साफ़ कह देती है, चाहे वह अच्छा न लगे।",
            ["साफ़ और सच बोलने वाली", "कम बोलने वाली", "बहुत विनम्र", "मज़ाक करने वाली"],
        ),
        (
            5,
            "द्विअर्थी",
            "नियम इतने द्विअर्थी थे कि आधी कक्षा ने उन्हें एक तरह समझा और आधी ने दूसरी तरह।",
            ["जिनके दो मतलब निकलें", "बहुत सख़्त", "बहुत आसान", "लाल रंग में लिखे"],
        ),
        (
            5,
            "अस्त-व्यस्त",
            "तूफ़ान के बाद गली में पत्ते, टहनियाँ और थैलियाँ अस्त-व्यस्त पड़ी थीं।",
            ["इधर-उधर बिखरी हुई", "ठीक से सजी हुई", "नई रंगी हुई", "पानी में डूबी हुई"],
        ),
        (
            6,
            "मितव्ययी",
            "दुकानदार इतना मितव्ययी था कि हर कागज़ की थैली को फटने तक दोबारा इस्तेमाल करता था।",
            ["चीज़ें और पैसे बचाकर चलने वाला", "बहुत अमीर", "बहुत आलसी", "ग्राहकों से रूखा"],
        ),
        (
            6,
            "विश्वसनीय",
            "उसका बहाना विश्वसनीय था; उस सुबह ट्रेनें सच में देर से चल रही थीं।",
            ["भरोसे लायक", "बेतुका", "बहुत लंबा", "बदतमीज़"],
        ),
        (
            7,
            "अतिरंजित",
            "शिक्षक की तारीफ़ इतनी अतिरंजित थी कि अर्जुन शर्म से लाल हो गया।",
            ["ज़रूरत से ज़्यादा बढ़ा-चढ़ाकर", "धीमी और छोटी", "अन्यायपूर्ण", "सुनने में कठिन"],
        ),
        (
            8,
            "दुरूह",
            "योजना इतनी दुरूह थी कि उसे बनाने वाले को भी समझाने के लिए चित्र बनाना पड़ा।",
            ["समझने में बहुत कठिन", "बहुत सस्ती", "बहुत पुरानी", "बहुत गुप्त"],
        ),
        (
            8,
            "सर्वव्यापी",
            "जुलाई में चेरापूंजी में बारिश सर्वव्यापी होती है; वह हर जगह, हर समय लगती है।",
            ["हर जगह मौजूद", "बहुत कम", "बहुत हल्की", "बहुत खतरनाक"],
        ),
        (
            9,
            "अल्पभाषी",
            "वह इतना अल्पभाषी है कि यात्रा के बारे में पूछने पर उसने बस एक शब्द कहा।",
            ["बहुत कम बोलने वाला", "बहुत ज़ोर से बोलने वाला", "बदतमीज़", "मज़ाकिया"],
        ),
        (
            10,
            "अनाप-शनाप",
            "दाम इतने अनाप-शनाप थे कि हम अगले बाज़ार गए जहाँ सब आधे दाम में मिला।",
            ["बेवजह बहुत ज़्यादा", "ठीक और कम", "गलत लिखे हुए", "हर घंटे बदलने वाले"],
        ),
    ],
    "hinglish": [
        (
            1,
            "uneenda",
            "Lambi sair ke baad pilla itna uneenda tha ki chatai par hi so gaya.",
            ["Neend se bhara", "Gusse mein", "Bhookha", "Dara hua"],
        ),
        (
            2,
            "khaulta",
            "Soup itna khaulta hua tha ki Asha ne chakhne se pehle das minute intezaar kiya.",
            ["Bahut garam", "Bahut namkeen", "Bahut gaadha", "Bahut thanda"],
        ),
        (
            3,
            "kshudhit",
            "Match ke baad Ravi itna kshudhit tha ki usne chawal ki teen plate kha li.",
            ["Bahut bhookha", "Bahut thaka", "Bahut khush", "Bahut beemar"],
        ),
        (
            3,
            "jarjar",
            "Purana pul itna jarjar tha ki ek baar mein ek hi aadmi use paar kar sakta tha.",
            ["Kamzor aur toota-phoota", "Bahut lamba", "Naya painted", "Bheed se bhara"],
        ),
        (
            4,
            "spashtvaadi",
            "Meena spashtvaadi hai; woh jo sochti hai wahi saaf-saaf keh deti hai, chahe achchha na lage.",
            ["Saaf aur sach bolne wali", "Kam bolne wali", "Bahut polite", "Mazaak karne wali"],
        ),
        (
            5,
            "dvi-arthi",
            "Rules itne dvi-arthi the ki aadhi class ne unhe ek tarah samjha aur aadhi ne doosri tarah.",
            ["Jinke do matlab niklein", "Bahut sakht", "Bahut aasaan", "Laal rang mein likhe"],
        ),
        (
            5,
            "ast-vyast",
            "Toofan ke baad gali mein patte, tehniyan aur thailiyan ast-vyast padi thi.",
            ["Idhar-udhar bikhri hui", "Theek se saji hui", "Nayi painted", "Paani mein doobi hui"],
        ),
        (
            6,
            "mitvyayi",
            "Dukaandaar itna mitvyayi tha ki har kaagaz ki thaili ko phatne tak dobara use karta tha.",
            ["Cheezein aur paise bachakar chalne wala", "Bahut ameer", "Bahut aalsi", "Customers se rookha"],
        ),
        (
            6,
            "vishwasneeya",
            "Uska bahaana vishwasneeya tha; us subah trains sach mein late chal rahi thi.",
            ["Bharose laayak", "Betuka", "Bahut lamba", "Badtameez"],
        ),
        (
            7,
            "atiranjit",
            "Teacher ki taareef itni atiranjit thi ki Arjun sharm se laal ho gaya.",
            ["Zaroorat se zyada badha-chadhakar", "Dheemi aur chhoti", "Unfair", "Sunne mein mushkil"],
        ),
        (
            8,
            "duruh",
            "Plan itna duruh tha ki use banane wale ko bhi samjhane ke liye diagram banana pada.",
            ["Samajhne mein bahut mushkil", "Bahut sasta", "Bahut purana", "Bahut secret"],
        ),
        (
            8,
            "sarvavyapi",
            "July mein Cherrapunji mein baarish sarvavyapi hoti hai; woh har jagah, har time lagti hai.",
            ["Har jagah maujood", "Bahut kam", "Bahut halki", "Bahut khatarnaak"],
        ),
        (
            9,
            "alpabhashi",
            "Woh itna alpabhashi hai ki trip ke baare mein poochhne par usne bas ek shabd kaha.",
            ["Bahut kam bolne wala", "Bahut zor se bolne wala", "Badtameez", "Mazaakiya"],
        ),
        (
            10,
            "anaap-shanaap",
            "Daam itne anaap-shanaap the ki hum agle bazaar gaye jahan sab aadhe daam mein mila.",
            ["Bewajah bahut zyada", "Theek aur kam", "Galat likhe hue", "Har ghante badalne wale"],
        ),
    ],
}

PROMPT = {
    "en": "What does “{w}” mean in this sentence?",
    "hi": "इस वाक्य में “{w}” का क्या अर्थ है?",
    "hinglish": "Is sentence mein “{w}” ka kya matlab hai?",
}
