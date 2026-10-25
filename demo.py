import os
import shutil
import random
from minidb.database import Database
from minidb.types import Column

#reproducibility
DB_DIR = "mydb"
if os.path.exists(DB_DIR):
    shutil.rmtree(DB_DIR)

print("1. Creating of database")

db = Database(DB_DIR)

db.create_table("datasets", [
    Column("id", "INT", pk=True),
    Column("name", "STRING"),
    Column("task", "STRING"),
    Column("size", "INT")
])

db.create_table("models", [
    Column("id", "INT", pk=True),
    Column("name", "STRING"),
    Column("version", "STRING")
])

db.create_table("experiments", [
    Column("id", "INT", pk=True),
    Column("dataset_id", "INT", fk=("datasets", "id")),
    Column("model_id", "INT", fk=("models", "id")),
    Column("accuracy", "FLOAT"),
    Column("status", "STRING")
])
print("Tables 'datasets', 'models', 'experiments' successfully created.")

print("\n2. INSERT")

datasets = [
    {"id": 1, "name": "mnist", "task": "classification", "size": 70000},
    {"id": 2, "name": "cifar10", "task": "classification", "size": 60000},
    {"id": 3, "name": "imdb", "task": "nlp", "size": 50000},
    {"id": 4, "name": "squad", "task": "qa", "size": 100000},
    {"id": 5, "name": "coco", "task": "detection", "size": 118000}
]
for d in datasets:
    db.insert("datasets", d)

models = [
    {"id": 1, "name": "resnet", "version": "v1"},
    {"id": 2, "name": "bert", "version": "base"},
    {"id": 3, "name": "yolo", "version": "v8"},
    {"id": 4, "name": "vit", "version": "large"},
    {"id": 5, "name": "gpt", "version": "2"}
]
for m in models:
    db.insert("models", m)

random.seed(42)
for i in range(1, 21):
    db.insert("experiments", {
        "id": i,
        "dataset_id": random.randint(1, 5),
        "model_id": random.randint(1, 5),
        "accuracy": round(random.uniform(0.5, 0.99), 2),
        "status": random.choice(["completed", "running", "failed"])
    })
print("Added: 5 datasets, 5 models, 20 experiments.")

# print("\n3. SELECT")

# print("1) All experiments (we output the first 3 for brevity):")
# all_exps = db.select("experiments")
# for e in all_exps[:3]:
#     print("  ", e)

# print("\n2) Selecting specific columns with a filter (accuracy >= 0.9 AND status = 'completed'):")
# filtered = db.select("experiments", columns=["id", "accuracy"], where=[("accuracy", ">=", 0.9), ("status", "=", "completed")])
# for f in filtered[:3]:
#     print("  ", f)

# print("\n3) Selecting specific columns with a filter OR (status = 'failed' OR accuracy > 0.95):")
# or_filtered = db.select("experiments", where={"or": [[("status", "=", "failed")], [("accuracy", ">", 0.95)]]})
# for f in or_filtered[:3]:
#     print("  ", f)