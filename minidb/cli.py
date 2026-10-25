import os
from .database import Database
from .types import Column

def print_table(rows):
    if not rows:
        print("(0 rows)")
        return
        
    headers = list(rows[0].keys())
    
    print(" | ".join(headers))
    print("-" * 60)
    
    for row in rows:
        values = [str(row[h]) for h in headers]
        print(" | ".join(values))
        
    print(f"({len(rows)} rows)")

def print_help():
    print("""
Available commands:
  tables                                              - Show a list of all tables
  schema <table>                                      - Show the table structure
  create table <name> (col1 type [pk], col2 type ...) - Creating a new table
  insert <table> <id or 0> <val1> <val2> ...          - Insert an entry (values separated by a space)
  select <table> [col1,col2] [where ...]              - Select data (you can select columns and filter)
  update <table> [set <val1>,<val2>] [where...]       - Update record by ID
  delete from <table> [where ...]                     - Delete an entry by ID
  join <left> <right> <union_condition>               - Join two tables together
  exit                                                - Exit the program
""")

def run(db_dir):
    print(f"Downloading MiniDB from: {os.path.abspath(db_dir)}")
    db = Database(db_dir)
    print("The database is loaded. Enter help for the list of commands.\n")

    while True:
        try:
            line = input("minidb> ").strip()
            if not line:
                continue

            parts = line.split()
            cmd = parts[0].lower()

            if cmd in ("exit", "quit"):
                print("Exit...")
                break
                
            elif cmd == "help":
                print_help()

            elif cmd == "tables":
                print("Tables in the database:")
                for name in db.tables:
                    print(f" - {name}")

            elif cmd == "schema":
                if len(parts) < 2:
                    print("Error: select the name of the table (schema <table>)")
                    continue
                table_name = parts[1]
                if table_name in db.tables:
                    for col in db.tables[table_name].columns:
                        pk = " [PK]" if col.pk else ""
                        fk = f" [FK -> {col.fk[0]}.{col.fk[1]}]" if col.fk else ""
                        print(f"  {col.name} ({col.ftype}){pk}{fk}")
                else:
                    print(f"Error: Table '{table_name}' is not exist")

            elif cmd == "insert":
                if len(parts) < 3:
                    print("Error: syntax 'insert <table> <val1> <val2>...'")
                    continue
                table_name = parts[1]
                raw_vals = parts[2:]
                
                table = db.tables[table_name]
                row = {}
                for i, col in enumerate(table.columns):
                    if i >= len(raw_vals):
                        break
                    val = raw_vals[i]
                    if col.ftype == "INT":
                        row[col.name] = int(val)
                    elif col.ftype == "FLOAT":
                        row[col.name] = float(val)
                    else:
                        row[col.name] = val
                
                res = db.insert(table_name, row)
                print(f"Added: {res}")

            elif cmd == "select":
                if len(parts) < 2:
                    print("Error: syntax 'select <table> [rows] [where ...]'")
                    continue
                table_name = parts[1]
                
                cols = None
                where = None
                
                if "where" in parts:
                    w_idx = parts.index("where")
                    if w_idx > 2:
                        cols = parts[2].split(",")
                    cond_parts = parts[w_idx+1:]
                    where = []
                    i = 0
                    while i < len(cond_parts):
                        if cond_parts[i].lower() == "and":
                            i += 1
                            continue
                        col = cond_parts[i]
                        op = cond_parts[i+1]
                        val = cond_parts[i+2]
                        try: val = int(val)
                        except ValueError:
                            try: val = float(val)
                            except ValueError: pass
                        where.append((col, op, val))
                        i += 3
                else:
                    if len(parts) > 2:
                        cols = parts[2].split(",")
                
                results = db.select(table_name, columns=cols, where=where)
                print_table(results)

            elif cmd == "update":
                if len(parts) < 5 or parts[2].lower() != "set" or "where" not in parts:
                    print("Error: syntax 'update <table> set <col>=<val> where <condition> ...'")
                    continue
                table_name = parts[1]

                set_idx = parts.index("set")
                where_idx = parts.index("where")

                set_clause = " ".join(parts[set_idx + 1 : where_idx])

                updates = {}
                for assignment in set_clause.split(","):
                    assignment = assignment.strip()
                    if not assignment:
                        continue
                    
                    k, v = assignment.split("=")
                    k = k.strip()
                    v = v.strip()

                    try: v = int(v)
                    except ValueError:
                        try: v = float(v)
                        except ValueError: pass
                    updates[k] = v

                cond_parts = parts[where_idx+1:]
                where = []
                i = 0
                while i < len(cond_parts):
                    if cond_parts[i].lower() == "and":
                        i += 1
                        continue
                    col = cond_parts[i]
                    op = cond_parts[i+1]
                    val = cond_parts[i+2]
                    try: val = int(val)
                    except ValueError:
                        try: val = float(val)
                        except ValueError: pass
                    where.append((col, op, val))
                    i += 3

                count = db.update(table_name, where=where, updates=updates)
                print(f"Updated lines: {count}")

            elif cmd == "delete":
                if len(parts) < 3 or parts[1].lower() != "from":
                    print("Error: syntax 'delete from <table> where <condition>'")
                    continue
                
                table_name = parts[2]
                where = None

                if "where" in parts:
                    where_idx = parts.index("where")
                    cond_parts = parts[where_idx+1:]
                    
                    where = []
                    i = 0
                    while i < len(cond_parts):
                        if cond_parts[i].lower() == "and":
                            i += 1
                            continue
                        col = cond_parts[i]
                        op = cond_parts[i+1]
                        val = cond_parts[i+2]
                        try: val = int(val)
                        except ValueError:
                            try: val = float(val)
                            except ValueError: pass
                        where.append((col, op, val))
                        i += 3
                else:
                    print("Attencion: Condition WHERE do not set. ALL records from the table will be deleted!")

                count = db.delete(table_name, where=where)
                print(f"Deleted lines: {count}")

            elif cmd == "join":
                if len(parts) < 4:
                    print("Error: syntax 'join <left_table> <rught_table> <union_condition>'")
                    continue
                
                left_name = parts[1]
                right_name = parts[2]

                join_cond = "".join(parts[3:]) 
                
                if "=" in join_cond:
                    left_col, right_col = join_cond.split("=")
                else:
                    left_col = join_cond
                    right_col = "id"

                results = db.join(left_name, right_name, on=(left_col, right_col))
                print_table(results)


            elif cmd == "create":
                clean_line = line.replace("(", " ").replace(")", " ").replace(",", " ")
                c_parts = clean_line.split()
                
                if len(c_parts) < 4 or c_parts[1].lower() != "table":
                    print("Error: syntax 'create table <name> (col type [pk], ...)'")
                    continue
                
                table_name = c_parts[2]
                col_defs = c_parts[3:]
                
                columns = []
                i = 0
                while i < len(col_defs):
                    col_name = col_defs[i]
                    col_type = col_defs[i+1].upper()
                    is_pk = False
                    fk = None
                    
                    i += 2
                    while i < len(col_defs) and col_defs[i].lower() not in ("int", "string", "float"):
                        if col_defs[i].lower() == "pk":
                            is_pk = True
                            i += 1
                        elif "fk=" in col_defs[i].lower():
                            fk_str = col_defs[i].split("=")[1]
                            if "." in fk_str:
                                fk_table, fk_col = fk_str.split(".")
                            else:
                                fk_table = fk_str
                                fk_col = "id"
                            fk = (fk_table, fk_col)
                            i += 1
                        else:
                            break
                            
                    columns.append(Column(col_name, col_type, pk=is_pk, fk=fk))
                
                try:
                    db.create_table(table_name, columns)
                    print(f"Table '{table_name}' successfully created!")
                except Exception as e:
                    print(f"CREATION ERROR: {e}")

            else:
                print(f"Unknown command: '{cmd}'. Enter 'help'.")


        except ValueError as e:
            print(f"DATABASE ERROR: {e}")
        except Exception as e:
            print(f"SYSTEM ERROR: {e}")