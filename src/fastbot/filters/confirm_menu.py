from aiogram import types
from aiogram.fsm.context import FSMContext
from FastBot.decorators import menu, menu_handler
from FastBot.logger import Logger
from FastBot.builders import ReplyMenuBuilder
from states import MenuState


@menu(
    name="confirm",
    desc="Меню подтверждения действия",
    state=MenuState.WAITING_CONFIRMATION,
    command="confirm",
)
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


@menu_handler(buttons=["Да", "Нет", "Отмена"], state=MenuState.WAITING_CONFIRMATION)
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
