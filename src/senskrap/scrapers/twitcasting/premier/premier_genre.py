from enum import Enum


class PremierGenre(int, Enum):
    """Represents the available genres for searching on Twitcasting Premier."""

    MUSIC = 1
    THEATER_COMEDY = 2
    SPORTS = 3
    EVENT = 11
    OTHER = 99

    # Music Sub-categories
    ROCK = 101
    VISUAL_KEI = 102
    IDOL = 103
    J_POP = 105
    JAZZ_FUSION = 107
    ANIME_SONG = 109
    CLASSIC = 116
    CHORUS_ACAPELLA = 117
    WIND_MUSIC = 118
    VTUBER = 119
    ACOUSTIC = 120
    OTHER_MUSIC = 121

    # Theater/Comedy Sub-categories
    PLAY = 201
    MUSICAL = 202
    CLASSICAL_PERFORMING_ARTS = 204
    DANCE = 205
    READING_ALOUD = 206
    COMEDY = 207
    RAKUGO = 208
    OTHER_THEATER_COMEDY = 299

    # Sports Sub-categories
    MARTIAL_ARTS = 302
    OTHER_SPORTS = 399

    # Event Sub-categories
    GAME = 1101
    ANIME_EVENT = 1102
    TALK_SHOW = 1103
    OTHER_EVENT = 1199
