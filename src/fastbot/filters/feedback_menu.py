from aiogram import types
from aiogram.fsm.context import FSMContext
from src.FastBotLib.decorators.reply_menu_decorator import menu_handler
from src.FastBotLib.logger.logger import Logger
from src.FastBotLib.builders.reply_menu_builder import ReplyMenuBuilder
from states.states import MenuState


async def show_feedback_menu(message: types.Message, state: FSMContext):
    keyboard = ReplyMenuBuilder.simple_menu("Да", "Нет")
    await state.set_state(MenuState.WAITING_FEEDBACK)
    await message.answer("Нравится ли вам бот?", reply_markup=keyboard)


@menu_handler(buttons=["Да", "Нет"], state=MenuState.WAITING_FEEDBACK)
async def handle_feedback_menu_reply_buttons(message: types.Message, state: FSMContext):
    Logger.info("IN handle_feedback_menu_reply_buttons")
    text = message.text

    if text == "Да":
        await message.answer(
            "Спасибо за фидбек! 😊", reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        await message.answer(
            "Учтем ваше мнение! 🛠", reply_markup=types.ReplyKeyboardRemove()
        )
