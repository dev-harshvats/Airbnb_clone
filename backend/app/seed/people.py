"""Demo accounts. Every account uses the password below; `host@example.com` and
`guest@example.com` are the ones the README points people at."""

from datetime import date

DEMO_PASSWORD = "Password123"

# key, email, first, last, date of birth, is_host, bio
PEOPLE = [
    (
        "aarav",
        "host@example.com",
        "Aarav",
        "Mehta",
        date(1986, 3, 14),
        True,
        "Goa-born and happiest on a beach. I host in Goa and Mumbai and love sharing my favourite shacks and cafes.",
    ),
    (
        "priya",
        "priya.nair@example.com",
        "Priya",
        "Nair",
        date(1988, 7, 2),
        True,
        "Kerala through and through. My family has welcomed guests to the backwaters and tea hills for three generations.",
    ),
    (
        "rohan",
        "rohan.sharma@example.com",
        "Rohan",
        "Sharma",
        date(1984, 11, 21),
        True,
        "Mountaineer turned host. I look after cottages in Himachal and guesthouses in Ladakh.",
    ),
    (
        "ananya",
        "ananya.iyer@example.com",
        "Ananya",
        "Iyer",
        date(1990, 1, 9),
        True,
        "Coffee-estate daughter and city dweller. I host in Coorg, Bengaluru, Ooty, Pondicherry and Gokarna.",
    ),
    (
        "vikram",
        "vikram.rathore@example.com",
        "Vikram",
        "Rathore",
        date(1979, 5, 30),
        True,
        "Rajasthan is in my blood. Ask me for the best sunset spot in Jaipur, Udaipur or Jaisalmer.",
    ),
    (
        "meera",
        "meera.kapoor@example.com",
        "Meera",
        "Kapoor",
        date(1992, 9, 17),
        True,
        "Yoga teacher who hosts by the Ganges and in the Darjeeling hills.",
    ),
    ("kabir", "guest@example.com", "Kabir", "Singh", date(1993, 2, 25), False, None),
    ("ishita", "ishita.reddy@example.com", "Ishita", "Reddy", date(1995, 6, 11), False, None),
    ("arjun", "arjun.patel@example.com", "Arjun", "Patel", date(1991, 12, 3), False, None),
    ("sneha", "sneha.gupta@example.com", "Sneha", "Gupta", date(1997, 4, 28), False, None),
]
