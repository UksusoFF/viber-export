import sqlite3
import argparse


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
        default="data/viber.db",
        metavar='db_location',
        type=str,
        help='The location of the Viber database'
    )
    parser.add_argument(
        '--chatname',
        default="Соседи 24",
        type=str,
        help="Name of the chat to extract messages from"
    )

    args = parser.parse_args()

    db_location = args.db_location
    chat_name = args.chatname

    conn = create_connection(db_location)

    chat_id = execute(conn, "select ChatID from ChatInfo where instr(UPPER(Name), UPPER('" + chat_name + "')) > 0")
    if len(chat_id) > 0:
        chat_id = chat_id[0][0]
        print(chat_id)
    else:
        print("Couldn't find that chat name.")
        return

    users = execute(conn, "SELECT * FROM ChatRelation LEFT JOIN Contact ON Contact.ContactID = ChatRelation.ContactID WHERE ChatRelation.ChatID = " + str(chat_id))

    for user in users:
        print(user)

    # print the messages to a text file
    #with open(out_file, "w", encoding='utf-8') as f:
    #    for message in final:
    #        message = [str(message[0])[11:],
    #                   ("From: " if int(message[3]) == 0 else "To:   ") + str(message[1]).ljust(22, ' '),
    #                   str(message[2])]
    #        f.write(", ".join(message) + "\n")


if __name__ == "__main__":
    main()