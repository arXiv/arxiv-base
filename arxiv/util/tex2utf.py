"""Convert between TeX escapes and UTF8."""

import re
from typing import Pattern, Dict, Match

accents = {
    # first accents with non-letter prefix, e.g. \'A
    "'A": 0x00C1,
    "'C": 0x0106,
    "'E": 0x00C9,
    "'I": 0x00CD,
    "'L": 0x0139,
    "'N": 0x0143,
    "'O": 0x00D3,
    "'R": 0x0154,
    "'S": 0x015A,
    "'U": 0x00DA,
    "'Y": 0x00DD,
    "'Z": 0x0179,
    "'a": 0x00E1,
    "'c": 0x0107,
    "'e": 0x00E9,
    "'i": 0x00ED,
    "'l": 0x013A,
    "'n": 0x0144,
    "'o": 0x00F3,
    "'r": 0x0155,
    "'s": 0x015B,
    "'u": 0x00FA,
    "'y": 0x00FD,
    "'z": 0x017A,
    '"A': 0x00C4,
    '"E': 0x00CB,
    '"I': 0x00CF,
    '"O': 0x00D6,
    '"U': 0x00DC,
    '"Y': 0x0178,
    '"a': 0x00E4,
    '"e': 0x00EB,
    '"i': 0x00EF,
    '"o': 0x00F6,
    '"u': 0x00FC,
    '"y': 0x00FF,
    ".A": 0x0226,
    ".C": 0x010A,
    ".E": 0x0116,
    ".G": 0x0120,
    ".I": 0x0130,
    ".O": 0x022E,
    ".Z": 0x017B,
    ".a": 0x0227,
    ".c": 0x010B,
    ".e": 0x0117,
    ".g": 0x0121,
    ".o": 0x022F,
    ".z": 0x017C,
    "=A": 0x0100,
    "=E": 0x0112,
    "=I": 0x012A,
    "=O": 0x014C,
    "=U": 0x016A,
    "=Y": 0x0232,
    "=a": 0x0101,
    "=e": 0x0113,
    "=i": 0x012B,
    "=o": 0x014D,
    "=u": 0x016B,
    "=y": 0x0233,
    "^A": 0x00C2,
    "^C": 0x0108,
    "^E": 0x00CA,
    "^G": 0x011C,
    "^H": 0x0124,
    "^I": 0x00CE,
    "^J": 0x0134,
    "^O": 0x00D4,
    "^S": 0x015C,
    "^U": 0x00DB,
    "^W": 0x0174,
    "^Y": 0x0176,
    "^a": 0x00E2,
    "^c": 0x0109,
    "^e": 0x00EA,
    "^g": 0x011D,
    "^h": 0x0125,
    "^i": 0x00EE,
    "^j": 0x0135,
    "^o": 0x00F4,
    "^s": 0x015D,
    "^u": 0x00FB,
    "^w": 0x0175,
    "^y": 0x0177,
    "`A": 0x00C0,
    "`E": 0x00C8,
    "`I": 0x00CC,
    "`O": 0x00D2,
    "`U": 0x00D9,
    "`a": 0x00E0,
    "`e": 0x00E8,
    "`i": 0x00EC,
    "`o": 0x00F2,
    "`u": 0x00F9,
    "~A": 0x00C3,
    "~I": 0x0128,
    "~N": 0x00D1,
    "~O": 0x00D5,
    "~U": 0x0168,
    "~a": 0x00E3,
    "~i": 0x0129,
    "~n": 0x00F1,
    "~o": 0x00F5,
    "~u": 0x0169,
    # and now ones with letter prefix \c{c} etc..
    "HO": 0x0150,
    "HU": 0x0170,
    "Ho": 0x0151,
    "Hu": 0x0171,
    "cC": 0x00C7,
    "cE": 0x0228,
    "cG": 0x0122,
    "cK": 0x0136,
    "cL": 0x013B,
    "cN": 0x0145,
    "cR": 0x0156,
    "cS": 0x015E,
    "cT": 0x0162,
    "cc": 0x00E7,
    "ce": 0x0229,
    "cg": 0x0123,
    "ck": 0x0137,
    "cl": 0x013C,
    # Commented out due ARXIVDEV-2322 (bug reported by PG)
    # 'ci' : 'i\x{0327}' = chr(0x69).ch(0x327) # i with combining cedilla
    "cn": 0x0146,
    "cr": 0x0157,
    "cs": 0x015F,
    "ct": 0x0163,
    "kA": 0x0104,
    "kE": 0x0118,
    "kI": 0x012E,
    "kO": 0x01EA,
    "kU": 0x0172,
    "ka": 0x0105,
    "ke": 0x0119,
    "ki": 0x012F,
    "ko": 0x01EB,
    "ku": 0x0173,
    "rA": 0x00C5,
    "rU": 0x016E,
    "ra": 0x00E5,
    "ru": 0x016F,
    "uA": 0x0102,
    "uE": 0x0114,
    "uG": 0x011E,
    "uI": 0x012C,
    "uO": 0x014E,
    "uU": 0x016C,
    "ua": 0x0103,
    "ue": 0x0115,
    "ug": 0x011F,
    "ui": 0x012D,
    "uo": 0x014F,
    "uu": 0x016D,
    "vA": 0x01CD,
    "vC": 0x010C,
    "vD": 0x010E,
    "vE": 0x011A,
    "vG": 0x01E6,
    "vH": 0x021E,
    "vI": 0x01CF,
    "vK": 0x01E8,
    "vL": 0x013D,
    "vN": 0x0147,
    "vO": 0x01D1,
    "vR": 0x0158,
    "vS": 0x0160,
    "vT": 0x0164,
    "vU": 0x01D3,
    "vZ": 0x017D,
    "va": 0x01CE,
    "vc": 0x010D,
    "vd": 0x010F,
    "ve": 0x011B,
    "vg": 0x01E7,
    "vh": 0x021F,
    "vi": 0x01D0,
    "vk": 0x01E9,
    "vl": 0x013E,
    "vn": 0x0148,
    "vo": 0x01D2,
    "vr": 0x0159,
    "vs": 0x0161,
    "vt": 0x0165,
    "vu": 0x01D4,
    "vz": 0x017E,
}
r"""Hash to lookup tex markup and convert to Unicode.

macron: a line above character (overbar \={} in TeX)
caron: v-shape above character (\v{ } in TeX)
See: http://www.unicode.org/charts/
"""

textlet = {
    "AA": 0x00C5,
    "AE": 0x00C6,
    "DH": 0x00D0,
    "DJ": 0x0110,
    "ETH": 0x00D0,
    "L": 0x0141,
    "NG": 0x014A,
    "O": 0x00D8,
    "oe": 0x0153,
    "OE": 0x0152,
    "TH": 0x00DE,
    "aa": 0x00E5,
    "ae": 0x00E6,
    "dh": 0x00F0,
    "dj": 0x0111,
    "eth": 0x00F0,
    "i": 0x0131,
    "l": 0x0142,
    "ng": 0x014B,
    "o": 0x00F8,
    "ss": 0x00DF,
    "th": 0x00FE,
}

textgreek = {
    # Greek (upper)
    "Gamma": 0x0393,
    "Delta": 0x0394,
    "Theta": 0x0398,
    "Lambda": 0x039B,
    "Xi": 0x039E,
    "Pi": 0x03A0,
    "Sigma": 0x03A3,
    "Upsilon": 0x03A5,
    "Phi": 0x03A6,
    "Psi": 0x03A8,
    "Omega": 0x03A9,
    # Greek (lower)
    "alpha": 0x03B1,
    "beta": 0x03B2,
    "gamma": 0x03B3,
    "delta": 0x03B4,
    "epsilon": 0x03B5,
    "zeta": 0x03B6,
    "eta": 0x03B7,
    "theta": 0x03B8,
    "iota": 0x03B9,
    "kappa": 0x03BA,
    "lambda": 0x03BB,
    "mu": 0x03BC,
    "nu": 0x03BD,
    "xi": 0x03BE,
    "omicron": 0x03BF,
    "pi": 0x03C0,
    "rho": 0x03C1,
    "varsigma": 0x03C2,
    "sigma": 0x03C3,
    "tau": 0x03C4,
    "upsion": 0x03C5,
    "varphi": 0x03C6,  # φ
    "phi": 0x03D5,  # ϕ
    "chi": 0x03C7,
    "psi": 0x03C8,
    "omega": 0x03C9,
}


def _p_to_match(tex_to_chr: Dict[str, int]) -> Pattern:
    # textsym and textlet both use the same sort of regex pattern.
    keys = r"\\(" + "|".join(tex_to_chr.keys()) + ")"
    pstr = r"({)?" + keys + r"(\b|(?=_))(?(1)}|(\\(?= )| |{}|)?)"
    return re.compile(pstr)


textlet_pattern = _p_to_match(textlet)
textgreek_pattern = _p_to_match(textgreek)

textsym = {
    "P": 0x00B6,
    "S": 0x00A7,
    "copyright": 0x00A9,
    "guillemotleft": 0x00AB,
    "guillemotright": 0x00BB,
    "pounds": 0x00A3,
    "dag": 0x2020,
    "ddag": 0x2021,
    "div": 0x00F7,
    "deg": 0x00B0,
}

textsym_pattern = _p_to_match(textsym)


def _textlet_sub(match: Match) -> str:
    return chr(textlet[match.group(2)])


def _textsym_sub(match: Match) -> str:
    return chr(textsym[match.group(2)])


def _textgreek_sub(match: Match) -> str:
    return chr(textgreek[match.group(2)])


def texch2UTF(acc: str) -> str:
    """Convert single character TeX accents to UTF-8.

    Strip non-whitepsace characters from any sequence not recognized
    (hence could return an empty string if there are no word characters
    in the input string).

    chr(num) will automatically create a UTF8 string for big num
    """
    if acc in accents:
        return chr(accents[acc])
    else:
        return re.sub(r"[^\w]+", "", acc, flags=re.IGNORECASE)


def tex2utf(tex: str, greek: bool = True) -> str:
    r"""Convert some TeX accents and greek symbols to UTF-8 characters.

    :param tex: Text to filter.
    :param greek: If False, do not convert greek letters or ligatures.
        Greek symbols can cause problems. Ex. \phi is not suppose to
        look like φ. φ looks like \varphi. See ARXIVNG-1612
    :returns: string, possibly with some TeX replaced with UTF8
    """
    # Do dotless i,j -> plain i,j where they are part of an accented i or j
    utf = re.sub(r"/(\\['`\^\"\~\=\.uvH])\{\\([ij])\}", r"\g<1>\{\g<2>\}", tex)

    # Now work on the Tex sequences, first those with letters only match
    utf = textlet_pattern.sub(_textlet_sub, utf)

    if greek:
        utf = textgreek_pattern.sub(_textgreek_sub, utf)

    utf = textsym_pattern.sub(_textsym_sub, utf)

    utf = re.sub(r"\{\\j\}|\\j\s", "j", utf)  # not in Unicode?

    # reduce {{x}}, {{{x}}}, ... down to {x}
    while re.search(r"\{\{([^\}]*)\}\}", utf):
        utf = re.sub(r"\{\{([^\}]*)\}\}", r"{\g<1>}", utf)

    # Accents which have a non-letter prefix in TeX, first \'e
    utf = re.sub(r'\\([\'`^"~=.][a-zA-Z])', lambda m: texch2UTF(m.group(1)), utf)

    # then \'{e} form:
    utf = re.sub(
        r'\\([\'`^"~=.])\{([a-zA-Z])\}',
        lambda m: texch2UTF(m.group(1) + m.group(2)),
        utf,
    )

    # Accents which have a letter prefix in TeX
    #  \u{x} u above (breve), \v{x}   v above (caron), \H{x}   double accute...
    utf = re.sub(
        r"\\([Hckoruv])\{([a-zA-Z])\}",
        lambda m: texch2UTF(m.group(1) + m.group(2)),
        utf,
    )

    # Don't do \t{oo} yet,
    utf = re.sub(r"\\t{([^\}])\}", r"\g<1>", utf)

    # bdc34: commented out in original Perl
    # $utf =~ s/\{(.)\}/$1/g; #  remove { } from around {x}

    return utf
