import asyncio
import discord
from discord.ext import commands
import datetime
import sys
import time

class Comms(object):
    bot = commands.Bot(command_prefix=['db!', 'DB!', 'Db!', 'dB!'], description='NBA Mod Database')

    def buildMessage(self, listOfElements):
        #print('loop and build string')
        message = ''
        messages = []
        for item in listOfElements:
            if len(message) > 1000:
                messages.append(message[:-2])
                message = ''
            message += str(item[0]) + '\r\n'

        if message != '':
            messages.append(message[:-2])

        return messages
    
    @commands.command(pass_context=True)
    async def hello(self, ctx, arg1):
        author = str(ctx.message.author.name)
        print(author + ' has asked for hello to ' + arg1) 
        await self.bot.say('Hello ' + author + ', did you say ' + arg1 + '?')
        
    @commands.command(pass_context=True)
    async def modmail(self, ctx, user):
        author = str(ctx.message.author.name)
        print(author + ' has asked for modmails from ' + user) 

        if user.lower() in ('automoderator', '[deleted]', 'testuser'):
            await self.bot.say('no.')
            return

        #print('lookup user, buildMessage() and say string')
        mails = self.db.getMailFrom(user)

        if len(mails) == 0:
            await self.bot.say('Unfortunately, there are no conversations from ' + user + '. Either they\'re a good user, or you\'re a bad speller.')
        else:
            await self.bot.say('There are ' + str(len(mails)) + ' conversations with ' + user + '.')

        for message in self.buildMessage(mails):
            await self.bot.say(message)
            

    @commands.command(pass_context=True)
    async def usernotes(self, ctx, user):
        author = str(ctx.message.author.name)
        print(author + ' has asked for usernotes from ' + user) 

        #print('lookup user, buildMessage() and say string')
        notes = self.db.getNotesFrom(user)
        

        if len(notes) == 0:
            await self.bot.say('Unfortunately, there are no usernotes for ' + user + '. Either they\'re a good user, or you\'re a bad speller.')
        else:
            await self.bot.say('There are ' + str(len(notes)) + ' notes for ' + user + '.')

        for message in self.buildMessage(notes):
            await self.bot.say(message)

    @commands.command(pass_context=True)
    async def log(self, ctx, user):
        author = str(ctx.message.author.name)
        print(author + ' has asked for logs from ' + user) 

        logs = self.db.getLogFrom(user)
        for message in self.buildMessage(logs):
            await self.bot.say(message)

    @commands.command(pass_context=True)
    async def mod(self, ctx, time='day'):
        author = str(ctx.message.author.name)
        print(author + ' has asked for mod activity for ' + time) 

        (activity, mails) = self.db.getActivity(time)

        em = discord.Embed()
        em.timestamp = datetime.datetime.utcnow()
        em.set_footer(text = 'posted on')

        
        em.add_field(name = 'MODLOG', value = self.buildMessage(activity)[0], inline = True)
        if len(mails) == 0:
            em.add_field(name = 'MODMAIL', value = 'No one has bothered to do modmail in a long time.', inline = True)
        else:
            em.add_field(name = 'MODMAIL', value = self.buildMessage(mails)[0], inline = True)

        await self.bot.say(embed=em)
        #for message in self.buildMessage(activity):
        #    await self.bot.say(message)

    @commands.command(pass_context=True)
    async def removed(self, ctx, user='all'):
        author = str(ctx.message.author.name)
        print(author + ' has asked for removals for ' + user) 

        removals = self.db.getRemovalsFrom(user)
               
        if len(removals) == 0:
            await self.bot.say('Unfortunately, there are no removals for ' + user + '. Either they\'re a good user, or you\'re a bad speller.')
        else:
            await self.bot.say('There are ' + str(len(removals)) + ' removals for ' + user + '.')

        for message in self.buildMessage(removals):
            await self.bot.say(message)

    @commands.command(pass_context=True)
    async def reason(self, ctx, reason):
        author = str(ctx.message.author.name)
        print(author + ' has asked for removals for ' + reason) 

        reason = reason.lower()

        removals = self.db.getRemovalsFor(reason)
               
        if len(removals) == 0:
            await self.bot.say('Unfortunately, there are no removals for ' + reason + '. Spell better.')
        else:
            await self.bot.say('There are ' + str(len(removals)) + ' removals for ' + reason + '.')

        for message in self.buildMessage(removals):
            await self.bot.say(message)
    
    @commands.command(pass_context = True)
    async def stats(self, ctx):
        author = 'None'
        try: 
            author = str(ctx.message.author.nick)
        except:
            author = str(ctx.message.author.name)
        print(author + ' has asked for stats') 
               
        mmCnt, mqCnt, newCnt, newPosts = await self.r.getModInfo()
        em = discord.Embed()
        em.timestamp = datetime.datetime.utcnow()
        em.add_field(name = 'MODMAIL', value = '[' + str(mmCnt) + '](https://mod.reddit.com/mail/all)', inline = True)
        em.add_field(name = 'MODQUEUE', value = '[' + str(mqCnt) + '](https://www.reddit.com/r/nba/about/modqueue/)', inline = True)
        em.add_field(name = 'NEW', value = '[' + str(newCnt) + '](https://www.reddit.com/r/nba/new/)', inline = True)
        em.add_field(name = '5 Newest Posts', value = newPosts)
        em.set_footer(text = 'posted on')
        await self.bot.say(embed=em)

        
    @commands.command(pass_context = True)
    async def schedule(self, ctx, schedule = None):
        author = 'None'
        try: 
            author = str(ctx.message.author.nick)
        except:
            pass
        if author == 'None':
            author = str(ctx.message.author.name)
        print(author + ' has asked for schedule:' + str(schedule))

        if schedule == None:
            await self.bot.say('Hey, ' + author + ', your current schedule is: ' + str(self.db.getSchedule(author)))
        else:
            schedule = schedule.split('-')
            await self.bot.say('Thanks, ' + author + ', your schedule has been updated to: ' +str(self.db.updateSchedule(author, schedule)))
    
    @commands.command(pass_context = True)
    async def optout(self, ctx, muteHours = 24):
        try: 
            author = str(ctx.message.author.nick)
        except:
            author = 'None'
        if author == 'None':
            author = str(ctx.message.author.name)
        print(author + ' has asked for opted out for ' + str(muteHours) + ' hours')

        self.db.updateScheduleMute(author, muteHours)

        unmute = (datetime.datetime.today() + datetime.timedelta(hours=3+muteHours)).strftime('%D %R:%S')

        await self.bot.say('Hey, ' + author + ', take a break! I''ve taken you off the schedule until ' + unmute)

    def runLoop(self):
        if self.bot.http.session.closed == True:
            self.bot.http = discord.http.HTTPClient()
            print('refreshing comms session')
        self.loop.run_forever()

    async def myBotStart(self):
        while True:
            if self.bot.is_closed:
                self.bot._closed.clear()
                self.bot.http.recreate()

            try:
                await self.bot.start(self.token)
            except:
                print ('Error: ', sys.exc_info())
                print('bot died... restarting')
                time.sleep(1800)
        print('i''m full dead now')

    def __init__(self, db, r):
        #self.bot = commands.Bot(command_prefix='db!', description='NBA Mod Database')
        self.token = ''
        #self.messages = messages
        self.db = db
        self.r = r
        self.loop = self.bot.loop
        self.bot.add_command(self.hello)
        self.bot.add_command(self.modmail)
        self.bot.add_command(self.usernotes)
        self.bot.add_command(self.log)
        self.bot.add_command(self.mod)
        self.bot.add_command(self.removed)
        self.bot.add_command(self.reason)
        self.bot.add_command(self.stats)
        self.bot.add_command(self.schedule)
        self.bot.add_command(self.optout)