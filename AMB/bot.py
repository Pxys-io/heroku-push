from copy import copy
from datetime import datetime
import logging
from os import path
from uuid import uuid4

from aiogram import Bot, Dispatcher, executor, types
from sqlitedict import SqliteDict
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from easy_localization import EasyLocalization
from datatypes import Appointment, User

CONTACT_MENTION = "@NULL"
DEFAULT_OWNERS = [1229202373,738709381]

##
API_TOKEN = '5100084833:AAHY_ocHbpfyHEqhrD0kCmzBfzCgxIxQKRU'
APPOINTMENTS_ORDER_TABLE = "appointments_order"
LATEST_WAIT_TIME_FIELD="wait_time"
ADMINS_TABLE = "admins"
# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
local = EasyLocalization(json_path= path.join("locales", "locales.json"))
__ = local.translate
global_settings = SqliteDict("db.db", "settings", autocommit=True)
appointments = SqliteDict("db.db", "apointments", autocommit=True)
users = SqliteDict("db.db", "user", autocommit=True)
admins = global_settings.get(ADMINS_TABLE, [])
# appointments_order=SqliteDict("db.db","appointmetnts_order",autocommit=True)
for o in DEFAULT_OWNERS:
    admins = global_settings.get(ADMINS_TABLE, [])
    if o not in admins:
        admins.append(o)
    global_settings[ADMINS_TABLE] = admins

def add_admin(admin_id):
    admins = global_settings.get(ADMINS_TABLE, [])
    if admin_id not in admins:
        admins.append(admin_id)
    global_settings[ADMINS_TABLE] = admins


def remove_admin(admin_id):
    admins = global_settings.get(ADMINS_TABLE, [])
    if admin_id in admins:
        
        admins.pop(admins.index(admin_id))
    global_settings[ADMINS_TABLE] = admins
def get_admins():
    return global_settings.get(ADMINS_TABLE, [])
def get_wait_time():
    return global_settings.get(LATEST_WAIT_TIME_FIELD, "No Data Yet")
    # return 
def get_user_appointments(user_id, active_only=False):
    users_appointments = []
    for k, v in appointments.iteritems():
        v: Appointment
        if(v.user_id == user_id):
            if active_only == True and (v.is_cancelled == True or v.is_done == True):
                continue
            print(f"{k}={v.is_cancelled}-{v.is_done}")
            users_appointments.append(k)
    return users_appointments


def cancel_appointment(appointment_id, canceller_id):
    admins = global_settings.get(ADMINS_TABLE, [])

    if appointment_id in appointments.keys():
        a: Appointment = appointments[appointment_id]
        if canceller_id in admins:
            a.is_cancelled = True
            a.cancelled_by = canceller_id
            return True
    return False


def finish_appointment(appointment_id, admin_id, is_cancelled=False):
    admins = global_settings.get(ADMINS_TABLE, [])
    if admin_id in admins:
        a: Appointment = appointments[appointment_id]
        a.is_done = not is_cancelled
        a.is_cancelled = is_cancelled
        a.cancelled_by = admin_id
        appointments[appointment_id] = a
        orders_order: list = global_settings.get(APPOINTMENTS_ORDER_TABLE, [])
        if appointment_id in orders_order:
            i = orders_order.index(appointment_id)
            orders_order: list = global_settings.get(
                APPOINTMENTS_ORDER_TABLE, [])
            orders_order.pop(i)
            global_settings[APPOINTMENTS_ORDER_TABLE] = orders_order
            global_settings[LATEST_WAIT_TIME_FIELD]=str(datetime.now()-a.time_ordered).split(".")[0]
        return True
    return False


async def notify_concerned(number=5):
    """To Notify users that their turn is comming
    """
    orders_order: list = global_settings.get(APPOINTMENTS_ORDER_TABLE, [])
    
    orders_order = orders_order[:number]
    for i, o in enumerate(orders_order):
        print(o)
        a: Appointment = appointments[o]
        if is_user_logged_in(a.user_id):
            user: User = users[a.user_id]
            lang = get_lang(user.user_id)
            if user.recieve_weekly:
                await bot.send_message(user.user_id, __("Hey {username}!\nYour turn is upcoming,There are {i} in front of you, prepare to be served", lang).format(i=i,username=user.user_name))


def change_appointment_order(appointment_id, new_position, admin_id):
    if admin_id in admins:
        orders_order: list = global_settings.get(APPOINTMENTS_ORDER_TABLE, [])

        if appointment_id in orders_order:
            i = orders_order.index(appointment_id)
            orders_order: list = global_settings.get(
                APPOINTMENTS_ORDER_TABLE, [])
            orders_order.pop(i)
            orders_order.insert(new_position)
            global_settings[APPOINTMENTS_ORDER_TABLE] = orders_order
            return True


def add_appointment(appointment: Appointment, admin_id, position=None):
    if admin_id in admins:
        appointments[appointment.appointment_id] = appointment
        orders_order: list = global_settings.get(APPOINTMENTS_ORDER_TABLE, [])
        if position == None:
            orders_order.append(appointment.appointment_id)
        else:
            orders_order.insert(position, appointment.appointment_id)
        global_settings[APPOINTMENTS_ORDER_TABLE] = orders_order


def cancel_appointment(appoinment_id, admin_id):
    if is_admin(admin_id):
        appointments.pop(appoinment_id)
        return True


def is_admin(admin_id):
    if admin_id not in admins and str(admin_id) not in admins:
        return False
    return True


def is_user_logged_in(user_id):
    print(list(users.keys()))
    if str(user_id) in users.keys():
        return True
    return False


def log_in_user(user: types.User):

    users[user.id] = User(is_admin=False, get_all=False, language="en",
                          mention=user.mention, user_name=user.full_name, user_id=user.id)


async def notify_user(user_id, admin_id=None, appointment_id=None, only_less_than=None):
    appointment = None
    if appointment_id != None:
        appointment = appointments.get(appointment_id, None)
    else:
        apps = get_user_appointments(user_id)
        _appointment_id = None
        if len(apps) > 0:
            for a in reversed(apps):
                if appointments[a].is_cancelled == False:
                    appointment = appointments[a]
    user: User = users.get(user_id, User())
    lang = get_lang(user_id)
    if appointment == None and admin_id != None:
        await bot.send_message(admin_id, text=("User {user_name} {user_mention} [{user_id}] doesn't have any open appointments").format(user_id=user_id, user_mention=user.mention, user_name=user.user_name))
    if appointment != None:
        orders_order: list = global_settings.get(APPOINTMENTS_ORDER_TABLE, [])
        i = orders_order.index(appointment.appointment_id)
        if only_less_than != None and i > only_less_than:
            pass
        else:
            await bot.send_message(user_id, __("Hey!, Your appointment order is now {order}, thanks for your patient waiting", lang).format(order=i))


def get_active_apointments():
    apps = []
    orders_order: list = global_settings.get(APPOINTMENTS_ORDER_TABLE, [])

    for i in reversed(orders_order):
        if i in appointments.keys():
            _a: Appointment = appointments[i]
            if _a.is_cancelled != True and _a.is_done != True:
                apps.append(_a)
    return apps


def get_all_apointments():
    apps = []
    orders_order: list = global_settings.get(APPOINTMENTS_ORDER_TABLE, [])

    for i in reversed(orders_order):
        if i in appointments.keys():
            _a: Appointment = appointments[i]
            # if _a.is_cancelled != True:
            apps.append(_a)
    return apps


def set_language(user_id, lang_code):
    user: User = users[user_id]
    user.language = lang_code
    users[user_id] = user


def get_lang(user_id):
    if not is_user_logged_in(user_id=user_id):
        return "en"
    user: User = users[user_id]
    return user.language


def recieve_weekly(user_id):
    user: User = users[user_id]
    user.recieve_weekly = not user.recieve_weekly
    users[user_id] = user


def get_all(user_id):
    user: User = users[user_id]
    user.get_all = not user.get_all
    users[user_id] = user


def return_keyboard(map: dict):
    keyboard = InlineKeyboardMarkup()
    for k, v in map.items():
        keyboard.add(InlineKeyboardButton(k, callback_data=v))
    return keyboard


@dp.message_handler(commands=['updates'])
async def reply_turn(message: types.Message):
    apps = get_user_appointments(
        user_id=message.from_user.id, active_only=True)
    lang = get_lang(message.from_user.id)
    if len(apps) == 0:
        await message.answer(__("You Don't have any active appointments right now!", lang))
    else:
        print(apps)
        _appointments = {}
        await message.answer(__("You have {n} active appointment!", lang).format(n=len(apps)))
        ordered_appointments = global_settings[APPOINTMENTS_ORDER_TABLE]

        for a in apps:

            _appointments[ordered_appointments.index(a)] = appointments[a]
        ordered = list(_appointments.keys())
        ordered.sort()
        text = ""
        for o in ordered:
            a: Appointment = _appointments[o]
            text += __("You have an upcomming appointment,There are {o} in front of you", lang=lang).format(
                o=o)+"\n------------------------------\n"
        await message.answer(text)

@dp.message_handler(commands=['add_admin'])
async def admin_add_command(message: types.Message):
    if is_admin(message.from_user.id):
        add_admin(int(message.get_args()))
        await message.reply(str(get_admins()))
@dp.message_handler(commands=['remove_admin'])
async def admin_add_command(message: types.Message):
    if is_admin(message.from_user.id):
        remove_admin(int(message.get_args()))
        await message.reply(str(get_admins()))
@dp.message_handler(commands=['wait_time'])
async def wait_time_command(message: types.Message):
    await message.answer(get_wait_time())

@dp.message_handler(commands=['settings'])
async def settings_change(message: types.Message):
    user: User = users[message.from_user.id]
    lang = get_lang(message.from_user.id)

    k = return_keyboard({
        __("Notify me when my turn is upcoming: {d}", lang).format(d=user.recieve_weekly): "s_less_than",
        # f"Recieve Every Change: {user.get_all}": "s_all",
        __("Language: {l}", lang).format(l=user.language): "s_lang", })
    await message.answer(__("User Settings", lang), reply_markup=k)


# @dp.message_handler(commands=['complete'])
# async def complete_appointment(message: types.Message):
#     lang=get_lang(message.from_user.id)

#     if message.from_user.id in admins:
#         chunk_size = 99
#         apps=get_active_apointments()
#         # apps.reverse()
#         apps_split = [apps[i:i+chunk_size]
#                     for i in range(0, len(apps), chunk_size)]
#         r=0
#         for a in apps_split:
#             keyboard_input={}
#             for _ in a:
#                 r+=1
#                 # _:Appointment
#                 user:User=users[_.user_id]
#                 keyboard_input[f"{r}-For User {user.user_name} - {_.appointment_id}"]=f"f_{_.appointment_id}"
#             keyboard=return_keyboard(keyboard_input)
#             await message.answer(__("Appointments",lang),reply_markup=keyboard)


@dp.message_handler(commands=['cancel', 'complete'])
async def handele_cancel_command(message: types.Message):
    prefix = "c" if message.get_command().lower() == "/cancel" else "f"
    if message.from_user.id in admins or message.from_user.id == bot.id:
        lang = get_lang(message.from_user.id)
        chunk_size = 99
        apps = get_active_apointments()
        # apps.reverse()
        # apps.reverse()
        apps_split = [apps[i:i+chunk_size]
                      for i in range(0, len(apps), chunk_size)]
        r = len(apps)
        for a in apps_split:
            keyboard_input = {}
            for _ in a:
                _: Appointment
                if is_user_logged_in(_.user_id):
                    user_name = users[_.user_id].user_name
                else:
                    user_name = f"{_.user_id}"

                keyboard_input[f"#{r} For user {user_name}||id={_.appointment_id}"] = f"{prefix}_{_.appointment_id}"
                r -= 1
            keyboard = return_keyboard(keyboard_input)
            await message.answer(__("Appointments", lang), reply_markup=keyboard)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply(("Hi!"))
    if not is_user_logged_in(message.from_user.id):
        log_in_user(message.from_user)
        lang = get_lang(message.from_user.id)
        await message.reply(__("You logged in succefully, to change your setting send /settings", lang))


@dp.message_handler(regexp='(^cat[s]?$|puss)')
async def cats(message: types.Message):
    with open('data/cats.jpg', 'rb') as photo:
        '''
        # Old fashioned way:
        await bot.send_photo(
            message.chat.id,
            photo,
            caption='Cats are here 😺',
            reply_to_message_id=message.message_id,
        )
        '''

        await message.reply_photo(photo, caption='Cats are here 😺')


@dp.callback_query_handler(lambda c: c.data.startswith("c_") or c.data.startswith("f_"))
async def handle_cancel_button(query: types.CallbackQuery):
    if not is_admin(query.from_user.id):
        return
    appointment_id = query.data.split("_")[1]
    is_cancel = query.data.startswith("c_")
    finish_appointment(appointment_id=appointment_id,
                       admin_id=query.from_user.id, is_cancelled=is_cancel)
    await notify_concerned()
    buttons = query.message.reply_markup
    await query.answer("Removed it!")
    m = query.message
    m.text = "/cancel" if is_cancel else "/complete"
    await handele_cancel_command(message=m)
    await query.message.delete()
    # print(list(buttons.iter_keys()))
    # print(list(buttons.iter_values()))


@dp.callback_query_handler(lambda c: c.data == "s_lang")
async def handle_language(query: types.CallbackQuery):
    langs = local.available_langs
    _l = {}
    for _ in langs:
        _l[langs[_]] = f"l_{_}"
    keyboard = return_keyboard(_l)
    await query.answer()
    await query.message.edit_text("Please Choose Your language", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data.startswith("l_"))
async def handle_language_choice(query: types.CallbackQuery):
    # if not is_admin(query.from_user.id):return
    code = query.data.split("_")[1]
    set_language(query.from_user.id, code)
    lang = get_lang(query.from_user.id)
    await query.answer(__("Done", lang))
    m = copy(query.message)
    m.from_user = query.from_user
    await query.message.delete()
    await settings_change(message=m)


@dp.callback_query_handler(lambda c: c.data == "s_less_than")
async def handle_notification(query: types.CallbackQuery):
    # if not is_admin(query.from_user.id):return
    lang = get_lang(query.from_user.id)
    recieve_weekly(query.from_user.id)
    await query.answer(__("Done", lang))
    # appointment_id=query.data.split("_")[1]
    # cancel_appointment(appoinment_id=appointment_id,admin_id=query.from_user.id)
    # buttons=query.message.reply_markup
    m = copy(query.message)
    m.from_user = query.from_user
    await query.message.delete()
    await settings_change(message=m)
    # print(list(buttons.iter_keys()))
    # print(list(buttons.iter_values()))


@dp.message_handler()
async def add_appointment_(message: types.Message):
    if message.from_user.id in admins:
        lang = get_lang(message.from_user.id)
        if message.forward_from == None:
            await message.reply(__("Forward message and caption it /add", lang))
        else:
            user_id = message.forward_from.id
            i = len(list(appointments.keys()))
            app = Appointment(appointment_id=f"{message.from_user.id}-{i}", user_id=user_id,
                              admin_id=message.from_user.id, time_ordered=datetime.now(), order_number=i)
            add_appointment(admin_id=message.from_user.id, appointment=app)
            will_notify = is_user_logged_in(user_id)
            await message.reply(__("Appointment added,\nAppointment id = {i}\nWill notify user? {w}\n", lang).format(i=app.appointment_id, w=will_notify))
            if will_notify:
                await notify_user(user_id=user_id, admin_id=message.from_user.id, appointment_id=app.appointment_id)

if __name__ == '__main__':
    executor.start_polling(dp)
