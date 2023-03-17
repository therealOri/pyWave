#################### Imports & Definitions ####################
import os
import sqlite3
import beaupy
from datetime import datetime
from pystyle import Colors, Colorate
import json
import base64
from Crypto.Cipher import ChaCha20_Poly1305
from Crypto.Random import get_random_bytes
import gcm
import binascii
import csv
import secrets
import string
from decimal import Decimal



chacha_header = b"ChaCha real smooth~ dada da dada da"
salt = get_random_bytes(32)
#################### Imports & Definitions ####################



#################### Functions ####################
def banner():
    banner = """
     :::::::::  :::   ::: :::       :::     :::     :::     ::: ::::::::::
     :+:    :+: :+:   :+: :+:       :+:   :+: :+:   :+:     :+: :+:
     +:+    +:+  +:+ +:+  +:+       +:+  +:+   +:+  +:+     +:+ +:+
     +#++:++#+    +#++:   +#+  +:+  +#+ +#++:++#++: +#+     +:+ +#++:++#
     +#+           +#+    +#+ +#+#+ +#+ +#+     +#+  +#+   +#+  +#+
     #+#           #+#     #+#+# #+#+#  #+#     #+#   #+#+#+#   #+#
     ###           ###      ###   ###   ###     ###     ###     ##########

        Made by Ori#6338 | @therealOri_ | https://github.com/therealOri
    """
    colored_banner = Colorate.Horizontal(Colors.purple_to_blue, banner, 1)
    return colored_banner


def clear():
    os.system("clear||cls")


def add_action(price, operation, desc):
    now = datetime.now()
    date = now.strftime("%m/%d/%Y")
    time = now.strftime("%I:%M:%S %p")

    conn = sqlite3.connect("t_actions.db")
    c = conn.cursor()
    c.execute("INSERT INTO transactions (price, operation, description, date, time) VALUES (?, ?, ?, ?, ?)", (price, operation.lower(), desc, date, time))
    conn.commit()
    conn.close()


def update_total():
    conn = sqlite3.connect("t_actions.db")
    c = conn.cursor()
    c.execute("SELECT price FROM transactions ORDER BY id DESC LIMIT 1")
    last_price = c.fetchone()[0]

    c.execute("SELECT operation FROM transactions ORDER BY id DESC LIMIT 1")
    last_operation = c.fetchone()[0]

    c.execute("SELECT total FROM transactions")
    current_total = c.fetchall()
    try:
        current_total = current_total[-2][0]
    except:
        current_total = current_total[0][0]


    if last_operation == "in":
        new_total = current_total + last_price
    elif last_operation == "out":
        if current_total == 0.0:
            c.execute("DELETE FROM transactions WHERE id = (SELECT MAX(id) FROM transactions);")
            c.execute("DELETE FROM sqlite_sequence WHERE name = 'transactions';")
            conn.commit()
            conn.close()
            return None
        else:
            new_total = current_total - last_price

    c.execute("UPDATE transactions SET total = ? WHERE id = (SELECT MAX(id) FROM transactions)", (new_total,))
    conn.commit()
    conn.close()
    return True


def view_balance():
    conn = sqlite3.connect("t_actions.db")
    c = conn.cursor()

    c.execute("SELECT total FROM transactions")
    transactions = c.fetchall()
    try:
        current_total = Decimal(str(transactions[-1][0])).quantize(Decimal('.01'))
    except:
        current_total = Decimal('0.00')

    return current_total


def lock(plaintext, eKey):
    data_enc = gcm.stringE(enc_data=plaintext, key=eKey)
    data_enc = bytes(data_enc, 'utf-8')

    cipher = ChaCha20_Poly1305.new(key=salt)
    cipher.update(chacha_header)
    ciphertext, tag = cipher.encrypt_and_digest(data_enc)

    jk = [ 'nonce', 'header', 'ciphertext', 'tag' ]
    jv = [ base64.b64encode(x).decode('utf-8') for x in (cipher.nonce, chacha_header, ciphertext, tag) ]
    result = json.dumps(dict(zip(jk, jv)))
    result_bytes = bytes(result, 'utf-8')
    b64_result = base64.b64encode(result_bytes)
    final_result = base64_to_hex(b64_result)
    return final_result



def unlock(dKey, json_input, salt):
    try:
        b64 = json.loads(json_input)
        jk = [ 'nonce', 'header', 'ciphertext', 'tag' ]
        jv = {k:base64.b64decode(b64[k]) for k in jk}

        cipher = ChaCha20_Poly1305.new(key=salt, nonce=jv['nonce'])
        cipher.update(jv['header'])
        plaintext = cipher.decrypt_and_verify(jv['ciphertext'], jv['tag'])
    except (ValueError, KeyError):
        print("Incorrect decryption credentials, or data has been tampered with.")
        return None

    decrypted_message = gcm.stringD(dcr_data=plaintext, key=dKey)
    return decrypted_message



def base64_to_hex(base64_string):
    decoded_bytes = base64.b64decode(base64_string)
    hex_string = binascii.hexlify(decoded_bytes)
    return hex_string.decode()


def hex_to_base64(hex_string):
    hex_bytes = bytes.fromhex(hex_string)
    base64_string = base64.b64encode(hex_bytes)
    return base64_string.decode()


def generate_filename():
    alphabet = string.ascii_letters + string.digits
    filename = ''.join(secrets.choice(alphabet) for i in range(12)) + ".csv"
    return filename


def export_to_csv():
    conn = sqlite3.connect('t_actions.db')
    c = conn.cursor()
    c.execute("SELECT * FROM transactions")
    data = c.fetchall()

    c.execute(f"PRAGMA table_info(transactions)")
    column_names = [column[1] for column in c.fetchall()]

    csv_file_name = generate_filename()
    with open(csv_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(column_names)
        writer.writerows(data)

    conn.close()
    return csv_file_name
#################### Functions ####################












#################### Main ####################
def main():
    while True:
        options = ["Make Transaction?", "View balance?", "Lock database?", "Export to CSV?", "Exit?"]
        print(f'{banner()}\n\nWhat would you like to do?\n-----------------------------------------------------------\n')
        option = beaupy.select(options, cursor_style="#ffa533")

        if not option:
            clear()
            exit("Keyboard Interuption Detected!\nGoodbye <3")

        if options[0] in option:
            if os.path.isfile('t_actions.db.locked'):
                clear()
                print("Database file does not exist or is encrypted...")
                input('\n\nPress "enter" to continue...')
                clear()
                continue
            else:
                clear()
                price = beaupy.prompt("Transaction Ammount.")
                if not price:
                    clear()
                    continue
                try:
                    price = float(price)
                except Exception as e:
                    input(f'"price" is not a float.\n{e}\n\nPress "enter" to continue...')
                    clear()
                    continue


                operation = beaupy.prompt("In or Out?").lower()
                if not operation:
                    clear()
                    continue
                while operation not in ["in", "out"]:
                    operation = beaupy.prompt("Invalid input. In or Out?").lower()


                desc = beaupy.prompt("Description for transaction.")
                if not desc:
                    clear()
                    continue


                add_action(price, operation, desc)
                check = update_total()
                if check == None:
                    input('Transaction has NOT been made as current_total is 0.0 and you have no money to take out.\n\nPress "enter" to contine...')
                    clear()
                    continue
                else:
                    input('Transaction has been made.\n\nPress "enter" to contine...')
                    clear()
                    continue


        if options[1] in option:
            if os.path.isfile('t_actions.db.locked'):
                clear()
                print("Database file does not exist or is encrypted...")
                input('\n\nPress "enter" to continue...')
                clear()
                continue
            else:
                clear()
                balance = view_balance()
                input(f'Total available balance: ${balance}\n\nPress "enter" to continue...')
                clear()


        if options[2] in option:
            if os.path.isfile('t_actions.db.locked'):
                clear()
                print("Database file is already encrypted...")
                input('\n\nPress "enter" to continue...')
                clear()
                continue
            else:
                clear()
                file_name = 't_actions.db'
                key_data = beaupy.prompt("Data for key gen - (100+ characters)").encode()

                clear()
                eKey = gcm.keygen(key_data)
                if not eKey:
                    continue

                save_me = base64.b64encode(eKey)
                bSalt = base64.b64encode(salt)
                master_key = f"{save_me.decode()}:{bSalt.decode()}"

                input(f'Save this key so you can decrypt later: {master_key}\n\nPress "enter" to contine...')
                clear()

                with open(file_name, 'rb') as rb:
                    data = rb.read()

                chaCrypt = lock(data, eKey)
                clear()
                with open(file_name, 'w') as fw:
                    fw.write(chaCrypt)
                os.rename(file_name, file_name.replace(file_name, f'{file_name}.locked'))

                input('Database has been locked!\n\nPress "enter" to exit...')
                clear()
                exit("Goodbye! <3")


        if options[3] in option:
            if os.path.isfile('t_actions.db.locked'):
                clear()
                print("Database file does not exist or is encrypted...")
                input('\n\nPress "enter" to continue...')
                clear()
                continue
            else:
                exported_file = export_to_csv()
                input(f'Database transactions have been exported to "{exported_file}".\n\nPress "enter" to continue...')
                clear()
                continue


        if options[4] in option:
            clear()
            exit("Goodbye! <3")

#################### Main ####################









if __name__ == '__main__':
    enc_file_name = "t_actions.db.locked"
    if os.path.isfile(enc_file_name):
        clear()
        while True:
            print("Database is locked. Please provide the key to unlock the database.")
            dKey = beaupy.prompt("Encryption Key", secure=True)
            if not dKey:
                input("Please provide a key to unlock the database.")
                clear()
                continue
            clear()
            break

        with open(enc_file_name, 'r') as fr:
            dData = fr.read()

        enc_data = hex_to_base64(dData)


        try:
            json_input = base64.b64decode(enc_data)
            key_and_salt = dKey.split(":")
            enc_salt = key_and_salt[1]
            enc_key = key_and_salt[0]
        except:
            input('The "key" that was given is not a valid key.\n\nPress "enter" to try again...')
            clear()
            exit()

        dsalt = base64.b64decode(enc_salt)
        dkey = base64.b64decode(enc_key)

        cha_aes_crypt = unlock(dkey, json_input, dsalt)

        with open(enc_file_name, 'wb') as fw:
            fw.write(cha_aes_crypt)
        os.rename(enc_file_name, enc_file_name.replace('.locked', ''))
        clear()
        input('Database unlocked!\n\nPress "enter" to continue...')

        clear()
        main()
    else:
        clear()
        main()
