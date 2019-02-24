import bot
import sys
from ctypes import windll, c_uint, c_bool
from os import getpid
import time

pid = getpid()
process = windll.kernel32.OpenProcess(c_uint( 0x0200 | 0x0400 ), c_bool( False ), c_uint( pid ))
windll.kernel32.SetPriorityClass(process, c_uint(0x0080))
print(pid)

myBot = bot.Bot('Hello')

#myBot.comms.bot.recursively_remove_all_commands()
#myBot = bot.Bot('Hello')
myBot.run_bot()

print('i\'m done now')