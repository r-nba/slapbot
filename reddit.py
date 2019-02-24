import time
import asyncio
import json
import praw
import zlib
import base64
import datetime
import sys

class Reddit(object):

    async def getLog(self, mostRecent):
        #print('getting logs from src')
        #print('looping through, assigning dict to list, breaking at mostRecent')
        modlog = self.subreddit.mod.log(limit=None)
        fullUpdate = False
        i = 0
        logList = []
        
        

        for item in modlog:
            i += 1
            rDate = datetime.datetime.fromtimestamp(item.created_utc).strftime('%Y-%m-%d %H:%M:%S')
            #if item.id == 'ModAction_5fcb919e-60c4-11e7-8146-0e18eb2eb5c7':
            if item.id == mostRecent:
                fullUpdate = True
                break
    
    
            ml_mod = item.mod.name
            ml_type = item.action
            ml_reason = item.description
            ml_details = item.details
            ml_user = item.target_author
            ml_title = "" if item.target_title == None else item.target_title.translate(self.non_bmp_map).replace('\"', '')
            ml_link = item.target_permalink
            ml_create_date = rDate
            ml_id = item.id

            logList.append({'ml_id': ml_id, 'ml_user': ml_user, 'ml_mod': ml_mod, 'ml_type': ml_type, 'ml_reason': ml_reason, 'ml_details': ml_details, 'ml_title': ml_title, 'ml_link': ml_link, 'ml_create_date': ml_create_date})
            
            #await asyncio.sleep(.0001) #sleep every once in a while during looping
        if fullUpdate == False:
            print('MISSING LOGS: ' + str(mostRecent))

        return logList

    async def getMail(self, mostRecent):
        #print('getting mail from src')
        #print('looping through, assigning dict to list, breaking at mostRecent')
        archivedMail = self.subreddit.modmail.conversations(limit=500, state='archived')
        newMail = self.subreddit.modmail.conversations(limit=500)
        fullUpdate = False
        i = 0
        mailList = []
        bodyList = []
        
        for item in archivedMail, newMail:
            for conversation in item:
                if conversation.last_updated > mostRecent:
                    i += 1
                    id = conversation.id
                    #print(id)
                    #print(conversation.last_updated)
                    participant = ''
                    try:
                        participant = conversation.user.name
                    except AttributeError:
                        participant = 'Automoderator'
                    subject = conversation.subject
                    create_date = conversation.messages[0].date
                    last_update_date = conversation.last_updated

                    mailList.append({'id': id, 'participant': participant, 'subject': subject, 'create_date': create_date, 'last_update_date': last_update_date})

                    if subject == 'AutoModerator notification':
                        mail = conversation.messages[0]
    
                        mail_body = mail.body_markdown
                        start = mail_body.find('/u/') + 3
                        end = mail_body.find(' ', start)

                        mm_author = mail_body[start:end]
                        mm_id = mail.id
                        mc_id = id
                        mm_body = mail_body
                        mm_create_date = mail.date

                        bodyList.append({'mm_id': mm_id, 'mc_id': mc_id, 'mm_author': mm_author, 'mm_body': mm_body, 'mm_create_date': mm_create_date, 'mm_create_date': mm_create_date})

                    await asyncio.sleep(.0001) #sleep every once in a while during looping
                else:
                    fullUpdate = True
                    break

        if fullUpdate == False:
            print('MISSING MAIL: ' + str(mostRecent))

        return (mailList, bodyList)

    async def getModInfo(self):
        newMail = self.subreddit.modmail.conversations(limit=500)
        modqueue = self.subreddit.mod.modqueue(limit=None)
        new = self.subreddit.new(limit=100)
        newCount = 0
        newPosts = ''
        
        newMailCount = sum(1 for x in newMail)
        await asyncio.sleep(.1)
        modqueueCount = sum(1 for x in modqueue)
        await asyncio.sleep(.1)
        nowutc = time.time()
        for post in new:
            if nowutc - post.created_utc <= 3600:
                newCount += 1
                #print(post.created_utc)
                if newCount <= 5:
                    newPosts += str(post.score) + '▲ | ' + str(int((nowutc - post.created_utc) / 60)) + ' min ago | [' + post.title + '](' + post.shortlink + ')\r\n'
        
        await asyncio.sleep(.1)

        return(newMailCount, modqueueCount, newCount, newPosts)

    
    def getNotes(self):        
        warnings = []
        mods = []
    
        jsonUsernotes = json.loads(self.subreddit.wiki['usernotes'].content_md)
        jsonNotes = json.loads(zlib.decompress(base64.b64decode(jsonUsernotes['blob'])).decode('utf-8').translate(self.non_bmp_map))

        for mod in jsonUsernotes['constants']['users']:
            mods.append(mod)
    
        for warning in jsonUsernotes['constants']['warnings']:
            warnings.append(str(warning))    

        return (jsonNotes, mods, warnings)

    def __init__(self):
        #print('Initializing Source Class ...')
        self.r = praw.Reddit(user_agent='NBA Moderation Database')
        self.subreddit = self.r.subreddit('nba')
        self.non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)


#def main():
#    src = Source()
#    logs = src.getLog('ABCDEF123456')
#    mails = src.getMail('1/1/2017')
#    print(src.getNotes())

   
if __name__ == '__main__':
    main()
