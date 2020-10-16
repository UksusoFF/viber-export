import sqlite3
import argparse
import re


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

    conn = create_connection(args.db_location)

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
    for user in users:
        info = user[4]
        phone = user[7]
        nick = user[12]
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

        data.append(f'<tr><td>{nick}</td><td>{fio}</td><td>{room}</td><td>{phone}</td></tr>')

    output = re.sub(r'<tbody>(.*?)</tbody>', '<tbody>' + '\n'.join(data) + '</tbody>', s)
    output = re.sub(r'<title>(.*?)</title>', f'<title>{args.chat} :: Список участников чата</title>', output)

    result = open('result.html', 'w', encoding='utf-8')
    result.write(output)
    result.close()


if __name__ == '__main__':
    main()
