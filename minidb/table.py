import os
from .types import Column

class Table:
    def __init__(self, directory, name):
        self.dir = directory
        self.name = name
        self.data_path = os.path.join(directory, name + ".tbl")
        self.schema_path = os.path.join(directory, name + ".schema")
        self.columns = []
        self._pk_col = None
        self._load_schema()

    @classmethod
    def create(cls, directory, name, columns):
        with open(os.path.join(directory, name + ".schema"), "w", encoding="utf-8") as f:
            for col in columns:
                f.write(col.to_line() + "\n")
        open(os.path.join(directory, name + ".tbl"), "w").close()
        return cls(directory, name)

    def _load_schema(self):
        with open(self.schema_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    self.columns.append(Column.from_line(line))
        for col in self.columns:
            if col.pk:
                self._pk_col = col
        
        self._next_id = 1

        if any(c.name == "id" for c in self.columns):
            max_val = 0
            for row in self._scan():
                val = row.get("id", 0)
                if isinstance(val, int) and val > max_val:
                    max_val = val
            self._next_id = max_val + 1

    def _to_line(self, values):
        parts = [str(values[c.name]) for c in self.columns]
        return "|".join(parts) + "\n"

    def _parse_line(self, line):
        parts = line.rstrip("\n").split("|")
        row = {}
        for i, c in enumerate(self.columns):
            raw = parts[i]
            if c.ftype == "INT":
                row[c.name] = int(raw)
            elif c.ftype == "FLOAT":
                row[c.name] = float(raw)
            else:
                row[c.name] = raw
        return row

    def _read_all_lines(self):
        with open(self.data_path, "r", encoding="utf-8") as f:
            return f.readlines()

    def _append(self, values):
        with open(self.data_path, "a", encoding="utf-8") as f:
            f.write(self._to_line(values))

    def _scan(self):
        for line in self._read_all_lines():
            yield self._parse_line(line)

    def insert(self, values):
        values = dict(values)
        
        if self._pk_col:
            pk_name = self._pk_col.name
            user_pk = values.get(pk_name)
            
            if user_pk is not None:
                for row in self._scan():
                    if row[pk_name] == user_pk:
                        raise ValueError(f"Error: row with {pk_name}='{user_pk}' already exist!")

        has_id_col = any(c.name == "id" for c in self.columns)
        
        if has_id_col:
            user_id = values.get("id")
            
            if user_id is None or user_id == 0:
                values["id"] = self._next_id
                user_id = self._next_id

            if user_id >= self._next_id:
                self._next_id = user_id + 1

        self._append(values)
        return values

    def select(self, columns=None, where=None):
        out = []
        for row in self._scan(): 
            if where is None or self._matches(row, where):
                if columns:
                    row = {c: row[c] for c in columns}
                out.append(row)
        return out

    def update(self, where, updates):
        lines = self._read_all_lines()
        new_lines = []
        n = 0
        for line in lines: 
            row = self._parse_line(line)

            if self._matches(row, where):
                new_row = dict(row)
                new_row.update(updates)

                if self._pk_col and new_row[self._pk_col.name] != row[self._pk_col.name]:
                    raise ValueError("You cannot change PRIMARY KEY")
                
                new_lines.append(self._to_line(new_row))
                n += 1
            else:
                new_lines.append(line)

        with open(self.data_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return n

    def delete(self, where):
        lines = self._read_all_lines()
        new_lines = []
        n = 0
        
        for line in lines:
            row = self._parse_line(line)
            if self._matches(row, where):
                n += 1
            else:
                new_lines.append(line)
                
        with open(self.data_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return n

    def _matches(self, row, where):
        if where is None:
            return True
        if isinstance(where, dict) and "or" in where:
            return any(self._matches(row, s) for s in where["or"])
        if isinstance(where, dict) and "and" in where:
            return all(self._matches(row, s) for s in where["and"])
        
        for col, op, val in where:
            a = row[col]
            if   op == "=": ok = a == val
            elif op == "!=": ok = a != val
            elif op == ">": ok = a > val
            elif op == "<": ok = a < val
            elif op == ">=": ok = a >= val
            elif op == "<=": ok = a <= val
            else: raise ValueError(f"unknown operator: {op}")
            if not ok:
                return False
        return True