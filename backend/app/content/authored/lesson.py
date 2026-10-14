"""T12 Mini-Lesson: a brand-new invented concept (Glimmers), then recall, near and far transfer items.
Set A follows the lesson; set B (parallel items) follows a short recap, which measures learning gain.
First option of each question is correct."""

LESSON = {
    "en": {
        "title": "Meet the Glimmers",
        "sections": [
            "Glimmers are small imaginary animals that live near rivers.",
            "A Glimmer always has exactly three legs and a striped tail.",
            "Glimmers change colour: they turn blue when they are happy and grey when they are hungry.",
            "A Glimmer eats only moon-berries, which grow only at night.",
            "Baby Glimmers have plain tails. The stripes appear when they turn one year old.",
            "When a Glimmer sees its own reflection, it hums.",
        ],
        "recap": "Remember: three legs, striped tail (plain for babies), blue = happy, grey = hungry, eats only "
        "moon-berries that grow at night, hums at its reflection.",
        "questions": [
            ("A", "recall", "How many legs does a Glimmer have?", ["Three", "Four", "Two", "Six"]),
            ("A", "recall", "What colour is a hungry Glimmer?", ["Grey", "Blue", "Green", "Red"]),
            (
                "A",
                "near",
                "You see a grey river animal with three legs and a striped tail. What does it most likely need?",
                ["Food", "Sleep", "A bath", "A friend"],
            ),
            (
                "A",
                "near",
                "A three-legged river animal with a plain tail follows a Glimmer. What is it most likely?",
                ["A baby Glimmer", "A different kind of animal", "A sick Glimmer", "A very old Glimmer"],
            ),
            (
                "A",
                "far",
                "A Glimmer keeper places a mirror by the river. What will they most likely hear?",
                ["Humming", "Barking", "Nothing at all", "Splashing"],
            ),
            (
                "A",
                "far",
                "A farmer grows only fruit that ripens in the daytime. Will Glimmers eat his crop?",
                ["No, they eat only moon-berries", "Yes, every day", "Only when they are blue", "Only the babies will"],
            ),
            ("B", "recall", "What do Glimmers eat?", ["Moon-berries", "River fish", "Grass", "Mangoes"]),
            (
                "B",
                "recall",
                "When does a Glimmer turn blue?",
                ["When it is happy", "When it is hungry", "When it is cold", "When it sleeps"],
            ),
            (
                "B",
                "near",
                "A three-legged river animal with a striped tail is blue. How is it feeling?",
                ["Happy", "Hungry", "Sleepy", "Scared"],
            ),
            (
                "B",
                "near",
                "An animal has four legs and a striped tail. Is it a Glimmer?",
                [
                    "No, Glimmers have three legs",
                    "Yes, the tail is striped",
                    "Yes, if it lives near a river",
                    "Only if it is grey",
                ],
            ),
            (
                "B",
                "far",
                "A storybook shows a Glimmer eating mangoes in the afternoon. What is wrong with the picture?",
                ["Glimmers eat only moon-berries", "Glimmers never go out", "Mangoes are blue", "Nothing is wrong"],
            ),
            (
                "B",
                "far",
                "You are taking Glimmers on a long trip and want them to stay blue. What matters most to pack?",
                ["Moon-berries", "A mirror", "A blanket", "Toys"],
            ),
        ],
    },
    "hi": {
        "title": "मिलो ग्लिमर्स से",
        "sections": [
            "ग्लिमर छोटे काल्पनिक जानवर हैं जो नदियों के पास रहते हैं।",
            "ग्लिमर के हमेशा ठीक तीन पैर और एक धारीदार पूँछ होती है।",
            "ग्लिमर रंग बदलते हैं: खुश होने पर नीले और भूखे होने पर स्लेटी हो जाते हैं।",
            "ग्लिमर केवल चाँद-बेर खाते हैं, जो सिर्फ़ रात में उगते हैं।",
            "बच्चे ग्लिमर की पूँछ सादी होती है। एक साल का होने पर धारियाँ आती हैं।",
            "जब ग्लिमर अपनी परछाईं देखता है, तो वह गुनगुनाता है।",
        ],
        "recap": "याद रखो: तीन पैर, धारीदार पूँछ (बच्चों की सादी), नीला = खुश, स्लेटी = भूखा, सिर्फ़ रात में उगने वाले "
        "चाँद-बेर खाता है, अपनी परछाईं देखकर गुनगुनाता है।",
        "questions": [
            ("A", "recall", "ग्लिमर के कितने पैर होते हैं?", ["तीन", "चार", "दो", "छह"]),
            ("A", "recall", "भूखा ग्लिमर किस रंग का होता है?", ["स्लेटी", "नीला", "हरा", "लाल"]),
            (
                "A",
                "near",
                "तुम्हें नदी के पास तीन पैर और धारीदार पूँछ वाला एक स्लेटी जानवर दिखता है। उसे शायद किस चीज़ की ज़रूरत है?",
                ["खाने की", "नींद की", "नहाने की", "दोस्त की"],
            ),
            (
                "A",
                "near",
                "सादी पूँछ वाला तीन पैरों का एक जानवर ग्लिमर के पीछे चल रहा है। वह शायद क्या है?",
                ["बच्चा ग्लिमर", "कोई दूसरा जानवर", "बीमार ग्लिमर", "बहुत बूढ़ा ग्लिमर"],
            ),
            (
                "A",
                "far",
                "ग्लिमर की देखभाल करने वाला नदी किनारे आईना रख देता है। उसे शायद क्या सुनाई देगा?",
                ["गुनगुनाहट", "भौंकना", "कुछ भी नहीं", "छपाक की आवाज़"],
            ),
            (
                "A",
                "far",
                "एक किसान सिर्फ़ दिन में पकने वाले फल उगाता है। क्या ग्लिमर उसकी फसल खाएँगे?",
                ["नहीं, वे सिर्फ़ चाँद-बेर खाते हैं", "हाँ, रोज़", "सिर्फ़ नीले होने पर", "सिर्फ़ बच्चे खाएँगे"],
            ),
            ("B", "recall", "ग्लिमर क्या खाते हैं?", ["चाँद-बेर", "नदी की मछली", "घास", "आम"]),
            (
                "B",
                "recall",
                "ग्लिमर नीला कब होता है?",
                ["जब वह खुश होता है", "जब वह भूखा होता है", "जब ठंड लगती है", "जब वह सोता है"],
            ),
            (
                "B",
                "near",
                "धारीदार पूँछ वाला तीन पैरों का एक जानवर नीला है। वह कैसा महसूस कर रहा है?",
                ["खुश", "भूखा", "नींद में", "डरा हुआ"],
            ),
            (
                "B",
                "near",
                "एक जानवर के चार पैर और धारीदार पूँछ है। क्या वह ग्लिमर है?",
                ["नहीं, ग्लिमर के तीन पैर होते हैं", "हाँ, पूँछ धारीदार है", "हाँ, अगर वह नदी के पास रहता है", "सिर्फ़ अगर वह स्लेटी है"],
            ),
            (
                "B",
                "far",
                "एक कहानी की किताब में ग्लिमर दोपहर में आम खा रहा है। चित्र में क्या गलत है?",
                ["ग्लिमर सिर्फ़ चाँद-बेर खाते हैं", "ग्लिमर कभी बाहर नहीं जाते", "आम नीले होते हैं", "कुछ गलत नहीं"],
            ),
            (
                "B",
                "far",
                "तुम ग्लिमर्स को लंबी यात्रा पर ले जा रहे हो और चाहते हो कि वे नीले रहें। साथ रखने के लिए सबसे ज़रूरी क्या है?",
                ["चाँद-बेर", "आईना", "कंबल", "खिलौने"],
            ),
        ],
    },
    "hinglish": {
        "title": "Milo Glimmers Se",
        "sections": [
            "Glimmers chhote imaginary jaanwar hain jo nadiyon ke paas rehte hain.",
            "Glimmer ke hamesha theek teen pair aur ek dhaaridaar poonch hoti hai.",
            "Glimmers rang badalte hain: khush hone par neele aur bhookhe hone par grey ho jaate hain.",
            "Glimmers sirf chaand-ber khaate hain, jo sirf raat mein ugte hain.",
            "Baby Glimmers ki poonch saadi hoti hai. Ek saal ka hone par dhaariyan aati hain.",
            "Jab Glimmer apni parchhaai dekhta hai, toh woh gungunata hai.",
        ],
        "recap": "Yaad rakho: teen pair, dhaaridaar poonch (babies ki saadi), neela = khush, grey = bhookha, sirf raat "
        "mein ugne wale chaand-ber khaata hai, apni parchhaai dekhkar gungunata hai.",
        "questions": [
            ("A", "recall", "Glimmer ke kitne pair hote hain?", ["Teen", "Chaar", "Do", "Chhah"]),
            ("A", "recall", "Bhookha Glimmer kis rang ka hota hai?", ["Grey", "Neela", "Hara", "Laal"]),
            (
                "A",
                "near",
                "Tumhe nadi ke paas teen pair aur dhaaridaar poonch wala ek grey jaanwar dikhta hai. Use shayad kis cheez ki zaroorat hai?",
                ["Khaane ki", "Neend ki", "Nahaane ki", "Dost ki"],
            ),
            (
                "A",
                "near",
                "Saadi poonch wala teen pairon ka ek jaanwar Glimmer ke peeche chal raha hai. Woh shayad kya hai?",
                ["Baby Glimmer", "Koi doosra jaanwar", "Beemar Glimmer", "Bahut boodha Glimmer"],
            ),
            (
                "A",
                "far",
                "Glimmer ki dekhbhaal karne wala nadi kinaare aaina rakh deta hai. Use shayad kya sunaai dega?",
                ["Gungunahat", "Bhaunkna", "Kuch bhi nahi", "Chhapaak ki awaaz"],
            ),
            (
                "A",
                "far",
                "Ek kisaan sirf din mein pakne wale phal ugata hai. Kya Glimmers uski fasal khaayenge?",
                ["Nahi, woh sirf chaand-ber khaate hain", "Haan, roz", "Sirf neele hone par", "Sirf babies khaayenge"],
            ),
            ("B", "recall", "Glimmers kya khaate hain?", ["Chaand-ber", "Nadi ki machhli", "Ghaas", "Aam"]),
            (
                "B",
                "recall",
                "Glimmer neela kab hota hai?",
                ["Jab woh khush hota hai", "Jab woh bhookha hota hai", "Jab thand lagti hai", "Jab woh sota hai"],
            ),
            (
                "B",
                "near",
                "Dhaaridaar poonch wala teen pairon ka ek jaanwar neela hai. Woh kaisa mehsoos kar raha hai?",
                ["Khush", "Bhookha", "Neend mein", "Dara hua"],
            ),
            (
                "B",
                "near",
                "Ek jaanwar ke chaar pair aur dhaaridaar poonch hai. Kya woh Glimmer hai?",
                [
                    "Nahi, Glimmer ke teen pair hote hain",
                    "Haan, poonch dhaaridaar hai",
                    "Haan, agar woh nadi ke paas rehta hai",
                    "Sirf agar woh grey hai",
                ],
            ),
            (
                "B",
                "far",
                "Ek storybook mein Glimmer dopahar mein aam kha raha hai. Picture mein kya galat hai?",
                [
                    "Glimmers sirf chaand-ber khaate hain",
                    "Glimmers kabhi bahar nahi jaate",
                    "Aam neele hote hain",
                    "Kuch galat nahi",
                ],
            ),
            (
                "B",
                "far",
                "Tum Glimmers ko lambi trip par le ja rahe ho aur chahte ho ki woh neele rahein. Saath rakhne ke liye sabse zaroori kya hai?",
                ["Chaand-ber", "Aaina", "Kambal", "Khilone"],
            ),
        ],
    },
}
