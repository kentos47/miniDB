import os
from .table import Table
from .types import Column

class Database:
    def __init__(self, directory):
        self.dir = directory
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)
            
        self.tables = {}
        self._load_tables()

    def _load_tables(self):
        for filename in os.listdir(self.dir):
            if filename.endswith(".schema"):
                table_name = filename[:-7]
                self.tables[table_name] = Table(self.dir, table_name)

    def create_table(self, name, columns):
        if name in self.tables:
            raise ValueError(f"Table '{name}' is already exist")
            
        pk_count = sum(1 for col in columns if col.pk)
        if pk_count > 1:
            raise ValueError(f"Error: In table '{name}' can be only one PRIMARY KEY!")
            
        Table.create(self.dir, name, columns)
        self.tables[name] = Table(self.dir, name)

    def insert(self, table_name, values):
        if table_name not in self.tables:
            raise ValueError(f"Table '{table_name}' is not exist")
        
        table = self.tables[table_name]
        self._check(table, values)
        return table.insert(values)

    def select(self, table_name, columns=None, where=None):
        if table_name not in self.tables:
            raise ValueError(f"Table '{table_name}' is not exist")
        return self.tables[table_name].select(columns, where)

    def update(self, table_name, where, updates):
        if table_name not in self.tables:
            raise ValueError(f"Table '{table_name}' is not exist")
        table = self.tables[table_name]
        self._check(table, updates, partial=True)
        return table.update(where, updates)

    def delete(self, table_name, where):
        table = self.tables[table_name]
        
        if table._pk_col:
            rows_to_delete = table.select(where=where)
            for row in rows_to_delete:
                pk_val = row["id"]
                
                for other_table in self.tables.values():
                    for col in other_table.columns:
                        if col.fk and col.fk[0] == table_name:
                            linked = other_table.select(where=[(col.name, "=", pk_val)])
                            if linked:
                                raise ValueError(f"You cannot delete {table_name}.{table._pk_col.name}={pk_val}: it is referenced by {other_table.name}")

        return table.delete(where)

    def _check(self, table, values, partial=False):
        for col in table.columns:
            if col.fk:
                if partial and col.name not in values:
                    continue
                
                fk_val = values.get(col.name)
                if fk_val is None:
                    continue
                
                ref_table_name, ref_col_name = col.fk
                ref_table = self.tables.get(ref_table_name)
                
                if not ref_table:
                    raise ValueError(f"Table '{ref_table_name}' is not exist (Error in FK)")
                
                found = ref_table.select(where=[(ref_col_name, "=", fk_val)])
                if not found:
                    raise ValueError(f"Error FK: in table '{ref_table_name}' is not row with {ref_col_name}={fk_val}")

    def join(self, left_name, right_name, on):
        left_table = self.tables[left_name]
        right_table = self.tables[right_name]
        left_col, right_col = on
        
        left_rows = left_table.select()
        right_rows = right_table.select()
        
        right_map = {}
        for r in right_rows:
            val = r[right_col]
            if val not in right_map:
                right_map[val] = []
            right_map[val].append(r)
            
        result = []
        for l_row in left_rows:
            match_val = l_row[left_col]
            if match_val in right_map:
                for r_row in right_map[match_val]:
                    combined = {}
                    for k, v in l_row.items():
                        combined[f"{left_name}.{k}"] = v
                    for k, v in r_row.items():
                        combined[f"{right_name}.{k}"] = v
                    result.append(combined)
                    
        return result