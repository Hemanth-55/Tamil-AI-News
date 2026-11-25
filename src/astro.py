"""Today's energy for Hemanth, from the Tamil panchangam.

Born 14 July 1999 · Janma natchathiram: Poosam (Pushya) · Raasi: Kadagam (Cancer).

The Moon's sidereal position is computed with the `ephem` astronomy library and the Lahiri ayanamsa. From it:
  * today's natchathiram and raasi of the Moon
  * Tara Balam: the count from Poosam to today's star, which gives one of nine taras
  * Chandrashtamam: the Moon in the 8th raasi from Kadagam (Kumbham), a day for calm and care
"""
from datetime import datetime, timezone
import math

import ephem

STARS = ["Aswini", "Bharani", "Karthigai", "Rohini", "Mirugaseeridam", "Thiruvathirai", "Punarpoosam", "Poosam",
         "Ayilyam", "Magam", "Pooram", "Uthiram", "Hastham", "Chithirai", "Swathi", "Visakam", "Anusham", "Kettai",
         "Moolam", "Pooradam", "Uthiradam", "Thiruvonam", "Avittam", "Sadhayam", "Poorattadhi", "Uthirattadhi", "Revathi"]
RASIS = ["Mesham", "Rishabam", "Mithunam", "Kadagam", "Simmam", "Kanni", "Thulam", "Viruchigam", "Dhanusu", "Magaram",
         "Kumbham", "Meenam"]
BIRTH_STAR, BIRTH_RASI = 7, 3                     # Poosam, Kadagam

TARAS = {
    1: ("Janma Tara", "a day of the self", [
        "Today's energy turns inward. Protect your focus, train with intent and finish one thing that matters to you before noon.",
        "The Moon returns to your own star. Keep the day simple and steady; your best work comes from calm repetition, not big swings."]),
    2: ("Sampat Tara", "a day of gains", [
        "The energy favours growth. Send the application, ask the question, make the pitch. Doors open more easily today.",
        "A good day to build value: learn one new skill deeply and show it to someone who can open a door for you."]),
    3: ("Vipat Tara", "a day of hurdles", [
        "Small obstacles may appear. Double-check your work, leave margin in your schedule, and let patience be your edge.",
        "Treat today like a tough spell from a quick bowler: leave the wide ones, defend well, and wait for your ball."]),
    4: ("Kshema Tara", "a day of well-being", [
        "A steady, healthy energy. Good for practice, reading and quiet progress that compounds over the week.",
        "Comfort and balance are with you. Use them to fix one weak spot in your game, on the field or at the desk."]),
    5: ("Pratyak Tara", "a day of resistance", [
        "Things may push back. Avoid arguments, plan before you act, and choose the long-term win over the quick one.",
        "Expect some friction. Keep promises small and deliver them fully; consistency beats force today."]),
    6: ("Sadhana Tara", "a day of achievement", [
        "One of your strongest days. Take on the hardest task first; effort today converts into results.",
        "The energy rewards ambition. Ship the project, take the interview, play the attacking shot."]),
    7: ("Naidhana Tara", "a day to stay grounded", [
        "Keep a low profile and protect your energy. Close pending tasks, rest well and save big decisions for tomorrow.",
        "A day for discipline, not display. Quiet preparation now becomes tomorrow's confidence."]),
    8: ("Mitra Tara", "a day of friends", [
        "Relationships carry you today. Reach out to a mentor, thank a teammate, or reconnect with someone in your network.",
        "Good energy for collaboration. Share your work; the right person may be one message away."]),
    9: ("Parama Mitra Tara", "a day of great support", [
        "One of the best days of the cycle. Back yourself on something bold; support is with you.",
        "Strong, friendly energy. Start the thing you've been postponing; momentum will follow."]),
}
WEEKDAY = ["Monday belongs to Chandran, the ruler of your Kadagam raasi: trust your intuition.",
           "Tuesday belongs to Sevvai: courage and hard training are rewarded.",
           "Wednesday belongs to Budhan: a sharp day for learning, analysis and clear writing.",
           "Thursday belongs to Guru, the deity of your Poosam star: seek wisdom and good mentors.",
           "Friday belongs to Sukran: creativity, polish and relationships shine.",
           "Saturday belongs to Sani, the lord of your Poosam star: discipline today pays back for years.",
           "Sunday belongs to Suriyan: lead with confidence and clarity."]


def moon_sidereal(dt):
    m = ephem.Moon(ephem.Date(dt))
    tropical = math.degrees(ephem.Ecliptic(m, epoch=ephem.Date(dt)).lon)
    years = (dt - datetime(2000, 1, 1, tzinfo=timezone.utc)).days / 365.25
    ayanamsa = 23.853 + 0.013968 * years            # Lahiri
    return (tropical - ayanamsa) % 360


def today(dt=None, local_weekday=None):
    dt = dt or datetime.now(timezone.utc)
    lon = moon_sidereal(dt)
    star, rasi = int(lon // (360 / 27)), int(lon // 30)
    count = (star - BIRTH_STAR) % 27 + 1
    tara_no = (count - 1) % 9 + 1
    name, meaning, lines = TARAS[tara_no]
    chandrashtamam = rasi == (BIRTH_RASI + 7) % 12
    day_of_year = dt.timetuple().tm_yday
    message = lines[day_of_year % len(lines)]
    if chandrashtamam:
        message = ("Chandrashtamam today: the Moon sits in the 8th house from your Kadagam raasi. Move gently, avoid "
                   "big decisions and arguments, and keep your mind calm. Strength today is staying composed.")
    wd = local_weekday if local_weekday is not None else dt.weekday()
    return {"moon_star": STARS[star], "moon_rasi": RASIS[rasi], "tara": name, "tara_meaning": meaning,
            "tara_no": tara_no, "chandrashtamam": chandrashtamam, "message": message, "weekday": WEEKDAY[wd]}


if __name__ == "__main__":
    import json
    print(json.dumps(today(), indent=1))
    # sanity check: on his birth date the Moon should be in Poosam
    print("birth check:", today(datetime(1999, 7, 14, 6, 0, tzinfo=timezone.utc))["moon_star"])
