import sqlite3
count=100
async def db_start():
    global db, cur

    db = sqlite3.connect('new.db')
    cur = db.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS profile(code_id TEXT PRIMARY KEY, name TEXT)")

    db.commit()
async def create_film(state):
    global count
    async with state.proxy() as data:
        cur.execute("INSERT INTO profile VALUES(?, ?)", (count, data['name']))
    count+=1
    db.commit()
    return count-1

async def edit_film(state):
    async with state.proxy() as data:
        cur.execute("UPDATE profile SET name = '{}' WHERE code_id == '{}'".format(data['name'], data['code']))
    db.commit()

async def delete_film(state):
    async with state.proxy() as data:
        cur.execute("DELETE FROM profile WHERE code_id == '{}'".format(data['code']))
    db.commit()

async def check_film(code):
    if list(cur.execute("SELECT * FROM profile WHERE code_id == '{}'".format(code))) == []:
        return False
    return True

async def select_film(code):
    kan = list(cur.execute("SELECT * FROM profile WHERE code_id == '{}'".format(code)))
    return kan[0][1]