import sqlite3
import argparse
import re
import json
from shutil import copyfile


def create_connection(db_file):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(e)

    return None


def execute(conn, query):
    cur = conn.cursor()
    cur.execute(query)

    return cur.fetchall()


def main():
    parser = argparse.ArgumentParser(
        description='Extract contacts from a supplied Viber database.'
    )
    parser.add_argument(
        'db_location',
        metavar='db_location',
        type=str,
        help='The location of the Viber database'
    )
    parser.add_argument(
        '--chat',
        type=str,
        help='Name of the chat to extract messages from'
    )

    args = parser.parse_args()

    conn = create_connection(f'{args.db_location}/viber.db')

    chats = execute(conn, f'SELECT ChatID FROM ChatInfo WHERE Name = "{args.chat}"')

    if len(chats) > 0:
        chat_id = chats[0][0]
        print(chat_id)
    else:
        print("Can't find this chat name.")
        return

    users = execute(conn, f'SELECT * FROM ChatRelation LEFT JOIN Contact ON Contact.ContactID = ChatRelation.ContactID WHERE ChatRelation.ChatID = {chat_id}')

    template = open('template.html')
    s = template.read()
    template.close()

    data = []
    table = []
    for user in users:
        info = user[4]
        phone = user[7]
        nick = user[12]
        avatar = user[13]
        if info is not None:
            if re.match(r'^[\u0400-\u04FF]*[ ][\u0400-\u04FF]*[ ]\d.*', info):
                info = info.split(' ')
                family = info.pop(0)
                name = info.pop(0)
                fio = f'{family} {name}'
                room = ' '.join(info)
            elif re.match(r'^[\u0400-\u04FF]*[ ]\d.*', info):
                info = info.split(' ')
                fio = info.pop(0)
                room = ' '.join(info)
            else:
                fio = info
                room = ''
        else:
            fio = ''
            room = ''

        if avatar is not None:
            copyfile(f'{args.db_location}/Avatars/{avatar}', f'result/{avatar}.jpg')
            image = f'<img class="avatar" src="{avatar}.jpg">'
        else:
            image = ''

        data.append({'phone': phone, 'nick': nick, 'image': image})
        table.append(f'<tr><td>{image}</td><td>{nick}</td><td>{fio}</td><td>{room}</td><td>{phone}</td></tr>')

    output = re.sub(r'<tbody>(.*?)</tbody>', '<tbody>' + '\n'.join(table) + '</tbody>', s)
    output = re.sub(r'<title>(.*?)</title>', f'<title>{args.chat} :: Список участников чата</title>', output)

    index = open('result/index.html', 'w', encoding='utf-8')
    index.write(output)
    index.close()

    meta = open('result/meta.json', 'w', encoding='utf-8')
    json.dump(data, meta)
    meta.close()


if __name__ == '__main__':
    main()
