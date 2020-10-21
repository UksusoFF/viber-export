import argparse
import json
import os
import re
import sqlite3
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
    parser.add_argument(
        '--output',
        type=str,
        default='result',
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

    template = open('template.html', 'r', encoding='utf-8')
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
                parse = info.split(' ')
                family = parse.pop(0)
                name = parse.pop(0)
                fio = f'{family} {name}'
                room = ' '.join(parse)
            elif re.match(r'^[\u0400-\u04FF]*[ ]\d.*', info):
                parse = info.split(' ')
                fio = parse.pop(0)
                room = ' '.join(parse)
            else:
                fio = info
                room = ''
        else:
            fio = ''
            room = ''

        if avatar is not None:
            path = f'{args.db_location}/Avatars/{avatar}'
            if os.path.isfile(path) and os.access(path, os.R_OK):
                copyfile(path, f'{args.output}/{avatar}.jpg')
                image = f'<img class="avatar" src="{avatar}.jpg">'
            else:
                avatar = None
                image = None
        else:
            image = ''

        data.append({'phone': phone, 'nick': nick, 'info': info, 'avatar': avatar})
        table.append(f'<tr><td>{image}</td><td>{nick}</td><td>{fio}</td><td>{room}</td><td>{phone}</td></tr>')

    output = re.sub(r'<tbody>(.*?)</tbody>', '<tbody>' + '\n'.join(table) + '</tbody>', s)
    output = re.sub(r'<title>(.*?)</title>', f'<title>{args.chat} :: Список участников чата</title>', output)

    index = open(f'{args.output}/index.html', 'w', encoding='utf-8')
    index.write(output)
    index.close()

    chat = open(f'{args.output}/chat.json', 'w', encoding='utf-8')
    json.dump(data, chat, ensure_ascii=False)
    chat.close()

    contacts = execute(conn, f'SELECT * FROM Contact')

    data = []
    for contact in contacts:
        info = contact[1]
        viber = contact[3]
        phone = contact[4]
        nick = contact[9]
        avatar = contact[10]
        if viber == 1:
            if phone is not None:
                if avatar is not None:
                    path = f'{args.db_location}/Avatars/{avatar}'
                    if os.path.isfile(path) and os.access(path, os.R_OK):
                        copyfile(path, f'{args.output}/{avatar}.jpg')
                    else:
                        avatar = None

                data.append({'phone': phone, 'nick': nick, 'info': info, 'avatar': avatar})

    meta = open(f'{args.output}/contacts.json', 'w', encoding='utf-8')
    json.dump(data, meta, ensure_ascii=False)
    meta.close()


if __name__ == '__main__':
    main()
