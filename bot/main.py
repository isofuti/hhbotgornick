import asyncio
import os
import sys
from pathlib import Path
import tempfile
from typing import List

# Allow running as a script from the bot/ directory
if __package__ is None and not hasattr(sys, "frozen"):
	parent_dir = str(Path(__file__).resolve().parents[1])
	if parent_dir not in sys.path:
		sys.path.append(parent_dir)

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

from utils.extract_text import extract_text_from_file


load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")


dp = Dispatcher()


def get_main_reply_kb() -> ReplyKeyboardMarkup:
	return ReplyKeyboardMarkup(
		keyboard=[
			[KeyboardButton(text="/resume"), KeyboardButton(text="/search")]
		],
		resize_keyboard=True,
		one_time_keyboard=False,
		is_persistent=True,
	)


@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
	await message.answer(
		"Привет! Отправь /resume с файлом PDF/DOCX, или /search для примера вакансий.",
		reply_markup=get_main_reply_kb(),
	)


@dp.message(Command("resume"))
async def cmd_resume(message: Message) -> None:
	await message.answer(
		"Прикрепи PDF или DOCX файл в этом чате одним сообщением.",
		reply_markup=get_main_reply_kb(),
	)


@dp.message(F.document)
async def handle_document(message: Message) -> None:
	# This handler will run for any document; guide the user accordingly
	doc = message.document
	file_name = (doc.file_name or "").lower()
	if not (file_name.endswith(".pdf") or file_name.endswith(".docx") or file_name.endswith(".txt")):
		await message.reply("Поддерживаются только PDF, DOCX или TXT.", reply_markup=get_main_reply_kb())
		return

	bot = message.bot
	file = await bot.get_file(doc.file_id)
	with tempfile.TemporaryDirectory() as td:
		local_path = os.path.join(td, file_name or "resume")
		await bot.download(file, destination=local_path)
		try:
			text = extract_text_from_file(local_path)
		except Exception as e:
			await message.reply(f"Не удалось извлечь текст: {e}", reply_markup=get_main_reply_kb())
			return

		# Telegram message limits ~4096 chars; send a chunk and attach as file if long
		preview = text[:3500] + ("\n..." if len(text) > 3500 else "")
		await message.reply(preview or "Текст не обнаружен.", reply_markup=get_main_reply_kb())


def build_vacancies_keyboard() -> InlineKeyboardMarkup:
	builder = InlineKeyboardBuilder()
	vacancies = [
		{"id": "v1", "title": "Python Backend Developer"},
		{"id": "v2", "title": "Data Analyst"},
		{"id": "v3", "title": "DevOps Engineer"},
	]
	for v in vacancies:
		builder.button(text=f"Откликнуться: {v['title']}", callback_data=f"apply:{v['id']}")
	builder.adjust(1)
	return builder.as_markup()


@dp.message(Command("search"))
async def cmd_search(message: Message) -> None:
	text = (
		"Нашли 3 подходящих вакансии:\n"
		"1) Python Backend Developer — FastAPI, PostgreSQL, Docker\n"
		"2) Data Analyst — SQL, Power BI, Python\n"
		"3) DevOps Engineer — Kubernetes, Terraform, AWS\n"
	)
	await message.answer(text, reply_markup=build_vacancies_keyboard())


@dp.callback_query(F.data.startswith("apply:"))
async def cb_apply(call: CallbackQuery) -> None:
	vacancy_id = call.data.split(":", 1)[1]
	await call.answer()
	await call.message.reply(f"Заявка отправлена на вакансию {vacancy_id}! (заглушка)")


async def main() -> None:
	if not TELEGRAM_BOT_TOKEN:
		raise RuntimeError("Please set TELEGRAM_BOT_TOKEN in environment.")
	bot = Bot(TELEGRAM_BOT_TOKEN)
	await dp.start_polling(bot)


if __name__ == "__main__":
	asyncio.run(main())
