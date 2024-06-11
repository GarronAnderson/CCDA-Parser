# execute_many.py

import csv
import datetime
import itertools
import sqlite3
import time

#


# modified from grouper() recipe at:
# https://docs.python.org/3/library/itertools.html#itertools-recipes
def file_chunker(fp, batch_size):
    args = [iter(fp)] * batch_size
    return itertools.zip_longest(*args, fillvalue=None)


if __name__ == "__main__":

    db = sqlite3.connect(r"..\src\codeDatabase.db")
    cur = db.cursor()

    cur.execute(
        """CREATE TABLE loinc (
        code TEXT,
        description TEXT
        );"""
    )
    db.commit()
    with open(r"..\Raw Data\Loinc.csv", "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        chunker = file_chunker(reader, 10000)
        start = time.perf_counter()
        for batch in chunker:
            data = [(row[0], row[1]) for row in batch if row is not None]
            try:
                cur.executemany("INSERT INTO loinc VALUES (?, ?)", data)
                db.commit()
            except Exception as e:
                print(e)
                db.rollback()
        end = time.perf_counter()
        cur.close()
