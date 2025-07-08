from aiogram import types
from aiogram.fsm.context import FSMContext
from src.FastBotLib.logger.logger import Logger
from src.FastBotLib.builders.reply_menu_builder import ReplyMenuBuilder
from states.states import MenuState


async def show_confirmation_menu(message: types.Message, state: FSMContext):
    keyboard = (
        ReplyMenuBuilder()
        .add_row("Да", "Нет")
        .add_row("Отмена")
        .set_placeholder("Подтвердите выбор")
        .build()
    )
    await state.set_state(MenuState.WAITING_CONFIRMATION)
    await message.answer("Подтвердите действие:", reply_markup=keyboard)


async def handle_conf_menu_reply_buttons(message: types.Message, state: FSMContext):
    Logger.info("IN handle_conf_menu_reply_buttons")
    text = message.text

    if text == "Да":
        await message.answer(
            "✅ Действие подтверждено!", reply_markup=types.ReplyKeyboardRemove()
        )
    elif text == "Нет":
        await message.answer(
            "❌ Действие отменено", reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        await message.answer(
            "❌ Действие отменено", reply_markup=types.ReplyKeyboardRemove()
        )

    await state.clear()
