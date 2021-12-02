#!/usr/bin/env bash

# запуск тестов в консоли:
python -m unittest

# coverage
coverage run --source=bot, handlers, settings -m unittest
coverage report -m

# create PostgreSQL database
psql.exe -U postgres
psql \! chcp 1251
psql -c "create database vk_chat_bot"
\connect vk_chat_bot
delete from userstate;
