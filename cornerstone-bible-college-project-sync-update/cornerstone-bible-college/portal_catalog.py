"""The college's course catalogue: 12 units, their timetable, exams, lecture notes and coursework.

This one file is the single source of truth for the database seed (portal_seed.py). Edit it to change the catalogue.
Days: 0=Mon .. 4=Fri. Bands: the four class periods of the day, numbered from 0.
"""
BANDS = [("9:00", "10:30"), ("11:00", "12:30"), ("14:00", "15:30"), ("16:00", "17:30")]
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri"]

# Kinds of coursework. "quiz" and "practical" are held in class, so students don't upload anything for them.
KINDS = {"assignment": "Assignment", "essay": "Essay", "reading": "Reading response",
         "quiz": "Quiz (in class)", "project": "Project", "practical": "Practical (in class)"}

TUTORS = [  # email, name, staff number, courses they teach
    ("amani@cornerstone.example", "Dr. Amani Okello", "T-001", ["OT101", "HM120", "GK105"]),
    ("ruth@cornerstone.example", "Pastor Ruth Mwangi", "T-002", ["NT110", "NT210", "CH101"]),
    ("samuel@cornerstone.example", "Dr. Samuel Kiptoo", "T-003", ["TH201", "ET230", "MS220"]),
    ("grace@cornerstone.example", "Pastor Grace Njeri", "T-004", ["MN150", "PR130", "CN140"]),
]

COURSES = [  # code, title, credits, description, fee, sessions [(day, band)], room, exam date-time, exam venue
    ("OT101", "Old Testament Survey", 3, "A walk through the Hebrew Bible, from creation and covenant to exile and hope.",
     18000, [(0, 0), (2, 0)], "Lecture Hall A", "2026-12-07 09:00", "Main Hall"),
    ("NT110", "Gospels and Acts", 3, "The life and teaching of Jesus, and the birth and growth of the early church.",
     18000, [(1, 0), (3, 0)], "Lecture Hall B", "2026-12-09 09:00", "Main Hall"),
    ("TH201", "Systematic Theology I", 4, "Core Christian doctrine: Scripture, the nature of God, and how the church has explained them.",
     20000, [(0, 1), (2, 1)], "Room 3", "2026-12-11 09:00", "Room 3"),
    ("MN150", "Introduction to Ministry", 2, "Practical foundations for serving in a church or community: teaching, care, and leadership.",
     15000, [(4, 0), (4, 1)], "Ministry Lab", "2026-12-14 14:00", "Ministry Lab"),
    ("HM120", "Hermeneutics: Interpreting Scripture", 3, "Principles for reading the Bible well: context, genre, language, and application.",
     18000, [(0, 2), (2, 2)], "Room 2", "2026-12-07 14:00", "Room 2"),
    ("GK105", "Biblical Greek I", 3, "The Greek alphabet, basic grammar, and reading short passages from the New Testament.",
     18000, [(1, 1), (3, 1)], "Room 4", "2026-12-08 09:00", "Room 4"),
    ("CH101", "Church History I", 3, "From the apostles to the Reformation: key people, councils, and movements.",
     18000, [(1, 2), (3, 2)], "Lecture Hall B", "2026-12-08 14:00", "Main Hall"),
    ("PR130", "Preaching and Homiletics", 3, "Preparing and delivering clear, faithful sermons from Scripture.",
     18000, [(0, 3), (2, 3)], "Ministry Lab", "2026-12-09 14:00", "Ministry Lab"),
    ("CN140", "Pastoral Counselling", 3, "Listening skills and biblical care for people facing grief, conflict, and everyday struggles.",
     18000, [(1, 3), (3, 3)], "Room 2", "2026-12-10 09:00", "Room 2"),
    ("NT210", "Pauline Epistles", 3, "Paul\u2019s life and letters: the themes of grace, faith, the church, and Christian living.",
     20000, [(0, 3), (2, 3)], "Room 3", "2026-12-10 14:00", "Room 3"),
    ("ET230", "Christian Ethics", 3, "Biblical foundations for moral decisions, and how to apply them to church and community life.",
     20000, [(4, 2), (4, 3)], "Room 4", "2026-12-11 14:00", "Room 4"),
    ("MS220", "Mission and Evangelism", 3, "God\u2019s mission, sharing the gospel across cultures, and planting and serving local churches.",
     18000, [(1, 3), (3, 3)], "Lecture Hall A", "2026-12-15 09:00", "Main Hall"),
]

LECTURE_NOTES = [  # course, title, scripture, body
    ("OT101", "Week 1: The shape of the Hebrew Bible", "Genesis 1\u20133", "Read the creation accounts as the opening of a larger story. Key idea: Genesis frames everything that follows, from covenant to exile to promise.\nReading for next class: Genesis 4\u201311."),
    ("OT101", "Week 2: Covenant themes", "Genesis 12; Exodus 19", "Trace the covenants with Abraham and at Sinai. Note what each one promises and what it asks of God\u2019s people.\nAssignment: one-page comparison of the two covenants."),
    ("NT110", "Week 1: Four portraits of Jesus", "Mark 1", "Each Gospel writer has a distinct audience and emphasis. Mark moves quickly and stresses action; compare how each Gospel opens.\nReading: Mark 1\u20134."),
    ("NT110", "Week 2: Acts and the early church", "Acts 2", "Pentecost marks the start of the church\u2019s mission. Watch how the message moves from Jerusalem outward.\nDiscussion question: what changes for the disciples after Acts 2?"),
    ("TH201", "Doctrine of Scripture", "2 Timothy 3:16", "Key terms to know: inspiration, authority, canon, illumination. Be ready to define each in your own words.\nQuiz next week."),
    ("TH201", "Doctrine of God", "Psalm 145", "We will cover God\u2019s attributes in two groups. Bring one question you still have about the Trinity."),
    ("MN150", "Preparing a short devotional", "Psalm 23", "Structure: observation, meaning, application. Keep it under five minutes.\nAssignment: deliver your devotional to a small group."),
    ("MN150", "Serving with a humble heart", "Mark 10:42\u201345", "Jesus defines leadership as service. We look at what that means for a pastor, a youth leader, and a volunteer.\nTask: find a place where you can serve for two hours this month."),
    ("HM120", "Week 1: Reading in context", "Nehemiah 8:1\u20138", "Every text has a historical, literary, and canonical context. Ask who wrote it, to whom, and why before asking what it means for us.\nReading for next class: the chapter on context in the course reader."),
    ("HM120", "Week 2: Genre matters", "Psalm 1; Luke 15", "Narrative, poetry, parable, and letter each speak in different ways. Learn the rules of each genre so you don\u2019t read poetry like law or a parable like a manual.\nBring one example of each genre."),
    ("GK105", "Week 1: The Greek alphabet", "John 1:1", "Learn the 24 letters, their sounds, and the breathing marks. Practise reading aloud slowly.\nHomework: write out the alphabet from memory and read John 1:1 aloud."),
    ("GK105", "Week 2: Nouns and the article", "John 1:1\u20135", "Greek nouns change their endings to show their job in the sentence. Start with the nominative and accusative cases and the definite article.\nQuiz next week on the alphabet and the article."),
    ("CH101", "Week 1: The early church", "Acts 2; Acts 15", "How the church grew under persecution, and how its leaders settled early questions at the Jerusalem Council.\nReading: the chapter on the first three centuries."),
    ("CH101", "Week 2: Creeds and councils", "1 Corinthians 15:3\u20135", "Why the church wrote creeds, and what the councils of Nicaea and Chalcedon decided about Christ.\nBe ready to explain the Nicene Creed in your own words."),
    ("PR130", "Week 1: From text to sermon", "Nehemiah 8:8", "A sermon explains the passage, shows its meaning, and applies it. Start with one clear main idea drawn from the text.\nHomework: write a one-sentence main idea for Psalm 23."),
    ("PR130", "Week 2: Structure and delivery", "Acts 2:14\u201341", "Introduction, main points, and conclusion. Practise pace, voice, and eye contact.\nBring a three-minute talk to practise in class."),
    ("CN140", "Week 1: Listening well", "James 1:19", "Quick to listen, slow to speak. Practise reflecting back what you hear before you offer advice.\nExercise: hold a five-minute listening conversation with a partner."),
    ("CN140", "Week 2: Grief and loss", "John 11:17\u201337; Psalm 34:18", "How people grieve, what helps, and what to avoid saying. Jesus\u2019 own response at the tomb of Lazarus is our model.\nReading: the chapter on grief in the course reader."),
    ("NT210", "Week 1: Paul\u2019s life and journeys", "Acts 9; Galatians 1", "Trace Paul from persecutor to apostle and map his missionary journeys. Note how his own letters and the book of Acts fit together.\nReading: Acts 13\u201314."),
    ("NT210", "Week 2: Justified by faith", "Romans 3\u20135", "Paul\u2019s argument in Romans: all have sinned, and righteousness comes through faith in Christ. Follow the logic one step at a time.\nDiscussion question: what does \u2018justified\u2019 mean in everyday language?"),
    ("ET230", "Week 1: Foundations of Christian ethics", "Micah 6:8", "Three approaches: rules, results, and character. See how Scripture combines them and why it starts with who God is.\nReading: Micah 6 and Matthew 5\u20137."),
    ("ET230", "Week 2: Truth, honesty and integrity", "Ephesians 4:25", "We look at honesty in business, church, and family life through real cases.\nBring one situation from your own community for discussion."),
    ("MS220", "Week 1: The mission of God", "Genesis 12:1\u20133; Matthew 28:18\u201320", "Mission begins with God, not with us. Follow the thread of blessing to the nations from Abraham to the Great Commission.\nReading: Acts 1."),
    ("MS220", "Week 2: Crossing cultures", "Acts 17:16\u201334", "Paul in Athens shows how to start from a culture\u2019s own questions without losing the message.\nTask: find out one belief or custom in a community near you."),
]

COURSEWORK = [  # id, course, title, description, due date, max marks, kind
    ("ot1", "OT101", "Compare two covenants", "Write a one-page comparison of God\u2019s covenant with Abraham (Genesis 12) and the covenant at Sinai (Exodus 19). For each, say what God promises and what he asks of his people. Draw on the Week 2 notes.", "2026-11-06", 20, "essay"),
    ("ot2", "OT101", "Reading response: Genesis 1\u20133", "In about 300 words, explain how the creation accounts set up the story that follows. Refer to the text at least twice.", "2026-11-13", 15, "reading"),
    ("ot3", "OT101", "Quiz 1: Law and history books", "A 30-minute written quiz in class on the books of the Law and the historical books. Bring a pen.", "2026-11-02", 20, "quiz"),
    ("ot4", "OT101", "Group presentation: a prophet and his message", "In groups of three or four, give a ten-minute talk on one prophet: the setting, the message, and what it means today. Hand in your slides.", "2026-11-24", 25, "project"),
    ("nt1", "NT110", "Four portraits of Jesus", "Compare how two Gospels open, using Mark 1 and one other Gospel. Describe the audience and emphasis you notice in each. Two pages at most.", "2026-11-06", 20, "essay"),
    ("nt2", "NT110", "Reflection on Acts 2", "Answer the class discussion question: what changes for the disciples after Acts 2? Write 400 words and support your answer from the passage.", "2026-11-20", 15, "reading"),
    ("nt3", "NT110", "Quiz 1: The life of Jesus", "A 30-minute quiz in class on the main events in the life of Jesus.", "2026-11-03", 20, "quiz"),
    ("nt4", "NT110", "Parable study: a short report", "Choose one parable. Write a report of up to three pages on its setting, its meaning, and how it speaks to people today.", "2026-11-27", 25, "project"),
    ("th1", "TH201", "Key terms: doctrine of Scripture", "Define inspiration, authority, canon, and illumination in your own words. Give one Bible reference for each. One page.", "2026-10-30", 10, "assignment"),
    ("th2", "TH201", "A question about the Trinity", "State one question you still have about the Trinity and write a short essay (600 words) exploring it, using what we covered on the doctrine of God.", "2026-11-20", 20, "essay"),
    ("th3", "TH201", "Quiz 1: Scripture and God", "A 30-minute quiz in class on the doctrine of Scripture and the attributes of God.", "2026-11-04", 20, "quiz"),
    ("th4", "TH201", "Doctrine in the church: interview report", "Interview a pastor or church leader about how one doctrine shapes the life of their church. Write up what you learn in two pages.", "2026-11-27", 25, "project"),
    ("mn1", "MN150", "Devotional outline: Psalm 23", "Submit a written outline of your five-minute devotional using the observation, meaning, and application structure. You will deliver it to a small group in class.", "2026-11-06", 25, "assignment"),
    ("mn2", "MN150", "Reflection: a day of service", "Spend two hours serving in a church or community project. Write a page about what you did and what you learned.", "2026-11-20", 10, "reading"),
    ("mn3", "MN150", "Quiz 1: Ministry basics", "A 30-minute quiz in class on the foundations of ministry covered so far.", "2026-11-13", 20, "quiz"),
    ("mn4", "MN150", "Deliver your devotional", "Deliver your five-minute devotional to a small group. Your tutor marks it in class and enters your result.", "2026-11-27", 30, "practical"),
    ("hm1", "HM120", "Reading response: context", "Read the chapter on context and write 250 words on how knowing the setting of a passage changes how you read it.", "2026-11-04", 10, "reading"),
    ("hm2", "HM120", "Interpreting a parable: a short paper", "Choose a parable from Luke 15. Explain its genre, its context, and its main point in two pages.", "2026-11-13", 20, "essay"),
    ("hm3", "HM120", "Quiz 1: Genre and context", "A 30-minute quiz in class on biblical genres and the questions of context.", "2026-11-09", 20, "quiz"),
    ("hm4", "HM120", "Passage study: from text to application", "Choose a passage of 10 to 15 verses. Explain its context and genre, give its main meaning, and suggest two applications.", "2026-11-25", 25, "project"),
    ("gk1", "GK105", "Alphabet and sounds exercise", "Complete the worksheet: write each Greek letter, give its sound, and read ten short words aloud.", "2026-11-03", 10, "assignment"),
    ("gk2", "GK105", "Parsing practice: nouns", "Identify the case, number, and gender of each noun in the exercise sheet.", "2026-11-12", 15, "assignment"),
    ("gk3", "GK105", "Quiz 1: Alphabet and the article", "A 30-minute quiz in class on the alphabet, accents, and the definite article.", "2026-11-10", 20, "quiz"),
    ("gk4", "GK105", "Translate and explain John 1:1\u20135", "Translate the five verses word by word, then write a paragraph on what you notice about the Greek.", "2026-11-26", 25, "project"),
    ("ch1", "CH101", "Reading response: the early church", "Read the chapter on the first three centuries and write 250 words on how the church grew under persecution.", "2026-11-03", 10, "reading"),
    ("ch2", "CH101", "Why the creeds mattered", "In two pages, explain why the early church wrote creeds and what the Nicene Creed protects.", "2026-11-17", 20, "essay"),
    ("ch3", "CH101", "Quiz 1: The first five centuries", "A 30-minute quiz in class on key people, events, and councils.", "2026-11-10", 20, "quiz"),
    ("ch4", "CH101", "Biography: a church leader", "Write a three-page biography of one leader from church history, from the apostles to the Reformation, and say what we can learn from them.", "2026-11-26", 25, "project"),
    ("pr1", "PR130", "Reading response: Nehemiah 8", "Write 250 words on how Ezra and the Levites taught the people, and what a preacher can learn from them.", "2026-11-04", 10, "reading"),
    ("pr2", "PR130", "Sermon outline", "Prepare a one-page outline for a ten-minute sermon: the passage, the main idea, three points, and the application.", "2026-11-11", 20, "assignment"),
    ("pr3", "PR130", "Quiz 1: Preparing a sermon", "A 30-minute quiz in class on the steps from passage to sermon.", "2026-11-09", 20, "quiz"),
    ("pr4", "PR130", "Preach a ten-minute sermon", "Preach your sermon to the class. Your tutor and classmates give feedback, and your tutor enters your result.", "2026-11-25", 30, "practical"),
    ("cn1", "CN140", "Reading response: James 1", "Write 250 words on what it means to be quick to listen and slow to speak when someone is hurting.", "2026-11-03", 10, "reading"),
    ("cn2", "CN140", "Responding to grief: a case study", "Read the case study provided. In two pages, describe how you would care for the family, and what you would avoid saying.", "2026-11-17", 20, "essay"),
    ("cn3", "CN140", "Quiz 1: Listening skills", "A 30-minute quiz in class on listening and the early stages of a care conversation.", "2026-11-10", 20, "quiz"),
    ("cn4", "CN140", "Role-play counselling session", "Take part in a role-played care conversation with a classmate. Your tutor marks it in class and enters your result.", "2026-11-26", 30, "practical"),
    ("pa1", "NT210", "Reading response: Galatians", "Read Galatians and write 250 words on why Paul was so concerned about the gospel in this letter.", "2026-11-04", 10, "reading"),
    ("pa2", "NT210", "Faith and works in Paul", "In two pages, explain how Paul speaks about faith and works in Romans and Galatians.", "2026-11-18", 20, "essay"),
    ("pa3", "NT210", "Quiz 1: Paul\u2019s life and journeys", "A 30-minute quiz in class on the life of Paul and his journeys.", "2026-11-09", 20, "quiz"),
    ("pa4", "NT210", "Letter study: Philippians", "Study one chapter of Philippians. Outline its message and write a page on how it applies to a church today.", "2026-11-30", 25, "project"),
    ("et1", "ET230", "Reading response: Micah 6", "Write 250 words on what Micah 6:8 asks of God\u2019s people and how it shapes everyday choices.", "2026-11-06", 10, "reading"),
    ("et2", "ET230", "A case study in honesty", "Read the case study provided. In two pages, apply what Scripture says about truthfulness and recommend what the person should do.", "2026-11-20", 20, "essay"),
    ("et3", "ET230", "Quiz 1: Approaches to ethics", "A 30-minute quiz in class on rules, results, and character as ways of thinking about ethics.", "2026-11-13", 20, "quiz"),
    ("et4", "ET230", "Community ethics report", "Choose a real moral issue in your community. Describe it, give the biblical teaching that applies, and recommend how the church should respond.", "2026-11-27", 25, "project"),
    ("ms1", "MS220", "Reading response: Acts 1 and 17", "Write 250 words comparing how the gospel is shared in Jerusalem and in Athens.", "2026-11-03", 10, "reading"),
    ("ms2", "MS220", "Crossing cultures: a field note", "Spend time in a community different from your own. In two pages, describe what you saw and how you would share the gospel there.", "2026-11-17", 20, "essay"),
    ("ms3", "MS220", "Quiz 1: Mission in Scripture", "A 30-minute quiz in class on the biblical story of mission.", "2026-11-10", 20, "quiz"),
    ("ms4", "MS220", "Outreach plan", "Plan a simple outreach for a local community: who it is for, what you will do, and how you will follow up. Two pages.", "2026-11-26", 25, "project"),
]

# Sample marks used for demonstration (made-up). The first values are the ones the prototype already used.
_MID_KNOWN = {"OT101": 72, "NT110": 65, "TH201": 58, "MN150": 81}
_AM_KNOWN = {"ot1": 16, "ot2": 12, "nt1": 15, "nt2": 13, "th1": 8, "th2": 15, "mn1": 21}


def sample_mid(code):
    return _MID_KNOWN.get(code, 55 + sum(map(ord, code)) % 27)


def sample_mark(cid, pts):
    if cid in _AM_KNOWN:
        return _AM_KNOWN[cid]
    return round(pts * (0.62 + (sum(map(ord, cid)) % 30) / 100))


def when_text(sessions):
    """'Mon and Wed, 9:00-10:30' (days that share the same times are grouped together)."""
    by_day = {}
    for d, b in sorted(sessions):
        by_day.setdefault(d, []).append("%s\u2013%s" % BANDS[b])
    groups = {}
    for d, times in by_day.items():
        groups.setdefault(" and ".join(times), []).append(DAY_NAMES[d])
    return "; ".join("%s, %s" % (" and ".join(days), t) for t, days in groups.items())


def exam_text(exam_at):
    from datetime import datetime
    dt = datetime.strptime(exam_at, "%Y-%m-%d %H:%M")
    return "%s %d %s %d, %d:%02d" % (DAY_NAMES[dt.weekday()], dt.day, dt.strftime("%b"), dt.year, dt.hour, dt.minute)


def level(code):
    return int("".join(ch for ch in code if ch.isdigit())[0])


def teacher_of(code):
    for _, name, _, codes in TUTORS:
        if code in codes:
            return name
