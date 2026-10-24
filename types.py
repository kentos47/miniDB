ValidTypes = ("INT", "FLOAT", "STRING")

class Column:
    def __init__(self, name: str, ftype: str, pk: bool = False, fk = None):
        if ftype not in ValidTypes:
            raise ValueError(f"bad type {ftype!r}, allowed: {ValidTypes}")
        self.name, self.ftype = name, ftype
        self.pk, self.fk = pk, fk

    def to_line(self):
        fk = f"{self.fk[0]}:{self.fk[1]}" if self.fk else ""
        return f"{self.name}|{self.ftype}|{int(self.pk)}|{fk}"

    @classmethod
    def from_line(cls, line: str):
        p = line.rstrip("\n").split("|")
        fk_s = p[3] if len(p) > 3 else ""
        return cls(p[0], p[1], bool(int(p[2])), tuple(fk_s.split(":")) if fk_s else None)