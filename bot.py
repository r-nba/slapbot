import asyncio
import time
import comms
import database
import reddit
import datetime
import sys
import discord
import random

class Bot(object):
    async def ModStats(self):
        if self.isReady == 0 and self.pingOnStart == 0:
            return

        if self.botChannel == None:
             self.botChannel = self.comms.bot.get_channel('410134097235673089')

        if self.botServer == None:
            self.botServer = self.comms.bot.get_server('229123661624377345')

        pop = self.botServer.get_member('279640029410885634')
        slapbot = self.botServer.get_member('383726541764296705')
        
        mmCnt, mqCnt, newCnt, newPosts = await self.r.getModInfo()
        #print('new message length: ' + str(len(newPosts)))
        if mqCnt >= 0 or mmCnt >= 0:
            #onlineMembers = []
            #members = self.botServer.members

            #for member in members:
            #    #print(member.status.name)
            #    if member.status.name in ('online') and member != slapbot:
            #        #print(member)
            #        onlineMembers.append(member)

            #memberCnt = len(onlineMembers)
            #randNum = random.randint(0, (memberCnt-1))
            #randMem = onlineMembers[randNum]

            #if memberCnt == 0:
            #    randMention = '@here'
            #    randNick = '@here'
            #else:
            #    randMention = randMem.mention
            #    randNick = randMem.nick
            
            currentHour = (time.localtime().tm_hour + 3) % 24
            #modID, modNick = self.db.getRandomMod(currentHour)
            #print(modID)
            #randMem = self.botServer.get_member(modID)
            #randMention = randMem.mention
            #randNick = modNick
            #currentTime = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%dT%H:%M:%S')

            mlHero, mmHero = self.db.getModStatsHeroes()
            if mlHero == None:
                mlHero = 'Nobody :('
            if mmHero == None:
                mmHero = 'Nobody :('

            em = discord.Embed()
            em.timestamp = datetime.datetime.utcnow()
            em.add_field(name = 'MODMAIL', value = '[' + str(mmCnt) + '](https://mod.reddit.com/mail/all)', inline = True)
            em.add_field(name = 'MODQUEUE', value = '[' + str(mqCnt) + '](https://www.reddit.com/r/nba/about/modqueue/)', inline = True)
            em.add_field(name = 'NEW', value = '[' + str(newCnt) + '](https://www.reddit.com/r/nba/new/)', inline = True)
            em.add_field(name = '5 Newest Posts', value = newPosts)
            em.add_field(name = 'Last Hour Mod Heroes', value = 'Modlog Hero: ' + mlHero + '\r\nModmail Hero: ' + mmHero)
            em.set_footer(text = 'posted on')
            #await self.comms.bot.send_message(self.botChannel, content = 'Hello, ' + randMention + '! The sub needs your help! Please help us!', embed=em)
            await self.comms.bot.send_message(self.botChannel, content = 'Hello! Here''s some stats!', embed=em)

            self.db.insertInfo(mmCnt, mqCnt, newCnt, '')
        else:
            #print('no ping')
            self.db.insertInfo(mmCnt,mqCnt,newCnt,None)


    async def refreshDB(self):
        while True:
            await self.comms.bot.wait_until_ready()
            dtStart = datetime.datetime.now()
            
            try:
                dtNotes = datetime.datetime.now()
                jsonNotes, mods, warnings = self.r.getNotes()
                self.db.refreshUsernotes(jsonNotes, mods, warnings)
                dtNotes = str((datetime.datetime.now()-dtNotes).seconds)
            except:
                print ('dtNotesError: ', sys.exc_info())
                dtNotes = str(dtNotes)
                await asyncio.sleep(3600)
                
            try:
                lastMailUpdate = self.db.getMailUpdate()
                lastLogUpdate = self.db.getLogUpdate()
            except:
                print ('UpdateDateError: ', sys.exc_info())
                await asyncio.sleep(3600)
            
            try:
                dtRMail = datetime.datetime.now()
                mails, bodies = await self.r.getMail(lastMailUpdate)
                dtRMail = str((datetime.datetime.now()-dtRMail).seconds)
            except:
                print ('dtRMailError: ', sys.exc_info())
                dtRMail = str(dtRMail)
                await asyncio.sleep(3600)
                
            try:
                dtRLogs = datetime.datetime.now()
                logs = await self.r.getLog(lastLogUpdate)
                dtRLogs = str((datetime.datetime.now()-dtRLogs).seconds)
            except:
                print ('dtRLogsError: ', sys.exc_info())
                dtRLogs = str(dtRLogs)
                await asyncio.sleep(3600)
            
            try:
                dtDMail = datetime.datetime.now()
                mods = self.r.subreddit.moderator()
                for mail in mails:
                    self.db.insertMail(mail)
                    convo = self.r.subreddit.modmail(mail['id'])
                    del convo.messages[0]
                    for message in convo.messages:
                        if message.author.name in mods:
                            dt = datetime.datetime.strptime(message.date, '%Y-%m-%dT%H:%M:%S.%f+00:00')
                            sdt = datetime.datetime.strftime(dt, '%Y-%m-%d %H:%M:%S')
                            self.db.insertmessageCount(message.id, convo.id, message.author.name, sdt)
                self.db.nba_db.commit()
                #print('mail updated with ' + str(len(mails)) + ' mails')
                dtDMail = str((datetime.datetime.now()-dtDMail).seconds)
            except:
                print ('dtDMailError: ', sys.exc_info())
                dtDMail = str(dtDMail)
                await asyncio.sleep(3600)
                
            try:
                dtDMessage = datetime.datetime.now()
                for message in bodies:
                    self.db.insertMessage(message)
                self.db.nba_db.commit()
                dtDMessage = str((datetime.datetime.now()-dtDMessage).seconds)
            except:
                print ('dtDMessageError: ', sys.exc_info())
                dtDMessage = str(dtDMessage)
                await asyncio.sleep(3600)
            
            try:
                dtDLogs = datetime.datetime.now()
                for log in logs:
                    self.db.insertLog(log)
                self.db.nba_db.commit()
                #print('logs updated with ' + str(len(logs)) + ' logs')
                dtDLogs = str((datetime.datetime.now()-dtDLogs).seconds)
            except:
                print ('dtDLogsError: ', sys.exc_info())
                dtDLogs = str(dtDLogs)
                await asyncio.sleep(3600)

            dtModStats = datetime.datetime.now()
            try:
                await self.ModStats()
                dtModStats = str((datetime.datetime.now()-dtModStats).seconds)
            except:
                print('mod stats error: ', sys.exc_info())
                dtModStats = str(dtModStats)
                #await asyncio.sleep(3600)

            dtEnd = datetime.datetime.now()

            print('Updated with ' + str(len(mails)) + ' modmails and ' + str(len(bodies)) + ' messages and ' + str(len(logs)) + ' logs (' + str(dtEnd) + ') in ' + str((dtEnd - dtStart).seconds) + ' seconds |' + dtNotes + '|' + dtRMail + '|' + dtRLogs + '|' + dtDMail + '|' + dtDMessage + '|' + dtDLogs + '|' + dtModStats)
            self.isReady = 1
            await asyncio.sleep(3600)

            

    def run_bot(self):
        #event_loop = asyncio.get_event_loop()
        self.comms.loop.create_task(self.refreshDB())
        self.comms.loop.create_task(self.comms.myBotStart())
        #self.comms.bot.login(self.comms.token)
        #event_loop.run_forever()
        while True:
            try:
                self.comms.runLoop()
                print('something fucking happened')
            except:
                print ('Error: ', sys.exc_info())
                print('I had a little error.  taking a nap')
                time.sleep(3600)
                print('i''m back now.')
        #finally:
        #    event_loop.close()

    def __init__(self, botName):
        self.botName = botName
        
        self.r = reddit.Reddit()
        self.db = database.Database()
        self.comms = comms.Comms(self.db, self.r)

        self.botChannel = self.comms.bot.get_channel('410134097235673089')
        self.botServer = self.comms.bot.get_server('229123661624377345')
        self.pingOnStart = 1
        self.isReady = 0