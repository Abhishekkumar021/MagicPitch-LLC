from fastapi import FastAPI, Request, File, UploadFile, HTTPException
from fastapi.templating import Jinja2Templates
import sqlite3
import re

app = FastAPI()
templates = Jinja2Templates(directory="templates")


def sanitize_filename(filename):
    filename = re.split(r"[-_]", filename)
    filename = "_".join(filename)
    filename = filename.split(".")[0]
    return filename.upper().replace(" ", "_")


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/")
async def upload_csv(file: UploadFile = File(...)):
    try:
        filename = sanitize_filename(file.filename)

        # print(f"Uploaded file name: {filename}")

        contents = await file.read()
        data = contents.decode("utf-8").split("\n")

        columns = [column.strip() for column in data[0].split(",")]
        columns_str = ", ".join(columns)

        # print(f"Column : {columns}")

        for i, col in enumerate(columns):
            if col.isalpha() == False:
                columns[i] = f"R{i+1}"

        # print(f"New columns : {columns}")
        if data[0].rstrip().startswith(columns_str):
            data = data[1:]

        with sqlite3.connect("data.db") as connection:
            cursor = connection.cursor()
            cursor.execute(
                f"""CREATE TABLE IF NOT EXISTS {filename}(id INTEGER PRIMARY KEY AUTOINCREMENT)"""
            )
            for missing_column in columns:
                cursor.execute(
                    f"""ALTER TABLE {filename} ADD COLUMN {str(missing_column)} TEXT NOT NULL;"""
                )

        #     cursor.execute(f"PRAGMA table_info({filename});")
        #     print(f"cursor : {cursor}")
        #     columns_info = cursor.fetchall()
        #     print("Table Columns:")
        #     for column_info in columns_info:
        #         print(column_info[1])

        # print("****************** Success *************")

        with sqlite3.connect("data.db") as connection:
            cursor = connection.cursor()
            for row in data:
                row = row.strip("\r")
                if row.strip():
                    values = row.split(",")
                    # print(f"Values : {values}")
                    cursor.execute(
                        f"""INSERT INTO {filename}({', '.join(columns)})
                            VALUES ({', '.join(['?' for _ in values])})""",
                        values,
                    )

            connection.commit()

        return {"message": "CSV file uploaded successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
