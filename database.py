import sqlite3
import datetime
#import reddit

class Database:
    # REFRESH FUNCTIONS
    def insertMail(self, dictMail):
        #print('inserting mail: ' + str(dictMail))
        self.c.execute('INSERT OR REPLACE INTO modmail_conversations VALUES (?,?,?,?,?,?)', \
            (dictMail['id'], \
            dictMail['participant'], \
            dictMail['subject'], \
            dictMail['create_date'], \
            dictMail['last_update_date'], \
            0))

    def insertMessage(self, dictMessage):
        #print('inserting mail: ' + str(dictMessage))
        self.c.execute('INSERT OR REPLACE INTO modmail_messages VALUES (?,?,?,?,?)', \
            (dictMessage['mm_id'], \
            dictMessage['mc_id'], \
            dictMessage['mm_author'], \
            dictMessage['mm_body'], \
            dictMessage['mm_create_date']))

    def insertmessageCount(self, messageID, conversationID, author, create_date):
        self.c.execute('INSERT OR REPLACE INTO modmail_tracker VALUES (?,?,?,?)', \
            (messageID, \
            conversationID, \
            author, \
            create_date))

    def insertLog(self, dictLog):
        #print('inserting log: ' + str(dictLog))
        self.c.execute('INSERT OR REPLACE INTO modlog VALUES (?,?,?,?,?,?,?,?,?)', \
            (dictLog['ml_id'], \
            dictLog['ml_user'], \
            dictLog['ml_mod'], \
            dictLog['ml_type'], \
            dictLog['ml_reason'], \
            dictLog['ml_details'], \
            dictLog['ml_title'], \
            dictLog['ml_link'], \
            dictLog['ml_create_date']))

    def insertInfo(self, mmCnt, mqCnt, newCnt, mod = None):
        self.c.execute('INSERT INTO mod_info (mi_create_date, mi_modmail, mi_modqueue, mi_new, mi_mod_pinged) VALUES (CURRENT_TIMESTAMP,?,?,?,?)', \
            (mmCnt, \
             mqCnt, \
             newCnt, \
             mod))

    def updateSchedule(self, user, schedule):
        self.c.execute('UPDATE mod_schedule set ms_start_hour = ?, ms_end_hour = ? WHERE ms_mod_nick = ?', (schedule[0], schedule[1], user))
        self.nba_db.commit()

        return self.getSchedule(user)

    def updateScheduleMute(self, user, muteHours):
        self.c.execute('UPDATE mod_schedule set ms_mute_until = datetime(\'now\', \'' + str(muteHours) + ' hour\') WHERE ms_mod_nick = ?', (user, ))
        self.nba_db.commit()

    def refreshUsernotes(self, jsonNotes,  mods, warnings):
        #print('store a new copy of notes')
        self.jsonNotes = jsonNotes
        self.mods = mods
        self.warnings = warnings


    # USER FUNCTIONS
    def getMailFrom(self, user):
        userLower = user.lower()

        msg_prefix = 'CASE WHEN mc_is_old = 0 THEN \'https://mod.reddit.com/mail/archived/\' ELSE \'https://www.reddit.com/message/messages/\' END'

        querySelect = 'SELECT mc_subject || \' | \' || ' + msg_prefix + ' || mc.mc_id '
        queryFrom = ' FROM modmail_conversations mc LEFT JOIN modmail_messages mm on mm.mc_id = mc.mc_id WHERE lower(mc_participant) = ? or lower(mm_author) = ? ORDER BY mc_last_update_date DESC'
        queryLimit = 'LIMIT 10'
        if all:
            queryLimit = ''

        self.c.execute(querySelect + queryFrom + queryLimit, (userLower, userLower))
        modmails = self.c.fetchall()

        return modmails

    def getLogFrom(self, user):
        userLower = user.lower()
        self.c.execute('SELECT ml_type || \' | \' || count(*) FROM modlog where lower(ml_user) = ? group by ml_type order by count(*) DESC;', (userLower,))

        logs = self.c.fetchall()
        #message = ''
        #for log in logs:
        #    message += log[0] + ' | ' + str(log[1]) + '\r\n'

        return logs

    def getNotesFrom(self, user):
        userLower = user.lower()
        notes = []
        for noteUser in self.jsonNotes:
            if noteUser.lower() == userLower:
                for usernote in self.jsonNotes[noteUser]['ns']:
                    url = ''
                    if usernote['l'].startswith('https://mod.reddit.com'):
                        url = usernote['l']
                    else:
                        link = usernote['l'].split(',')
                        if link[0] == 'l':
                            if len(link) == 3:
                                url = 'https://www.reddit.com/r/' + 'nba/comments/' + link[1] + '/-/' + link[2]
                            else:
                                url = 'https://www.reddit.com/r/' + 'nba/' + link[1]
                        elif link[0] == 'm':
                            url = 'https://www.reddit.com/message/messages/' + link[1]
                    usernoteMessage = datetime.datetime.fromtimestamp(usernote['t']).strftime('%m-%d-%y') + '|' + self.mods[usernote['m']] + ' | ' + self.warnings[usernote['w']] + '|' + usernote['n'].replace('\"', '').replace('|', '') + '|' + url
                    notes.append((usernoteMessage,))

        return notes
    
    def getRemovalsFrom(self, user):
        userLower = user.lower()
        if userLower == 'all':
            self.c.execute('SELECT ml_mod || \' | \' || ml_type  || \'|\' || ml_details || \' | \' || \'<https://reddit.com\' || ml_link || \'> | \' || ml_create_date FROM modlog WHERE ml_type = \'removelink\' ORDER BY ml_create_date DESC LIMIT 10;')
        else:
            self.c.execute('SELECT ml_mod || \' | \' || ml_type  || \'|\' || ml_details || \' | \' || \'<https://reddit.com\' || ml_link || \'> | \' || ml_create_date FROM modlog WHERE lower(ml_user) = ? AND ml_type IN (\'removelink\', \'removecomment\') ORDER BY ml_create_date DESC LIMIT 10;', (userLower,))

        removals = self.c.fetchall()

        return removals

    def getRemovalsFor(self, reason):

        self.c.execute('SELECT ml_user || \' | \' || ml_type  || \'|\' || ml_details || \' | \' || \'<https://reddit.com\' || ml_link || \'> | \' || ml_create_date FROM modlog WHERE lower(ml_details) LIKE ? ORDER BY ml_create_date DESC LIMIT 10;', ('%' + reason + '%',))
        
        removals = self.c.fetchall()

        return removals

    def getActivity(self, time):
        if time == 'day':
            days = '-24 hour'
        elif time == 'week':
            days = '-7 day'
        elif time == 'month':
            days = '-30 day'
        elif time == 'year':
            days = '-365 day'
        elif time == 'all':
            days = '-99999 day'
        elif time == 'musketeers':
            days = str(-1*((datetime.datetime.today() - datetime.datetime(2017, 7, 14)).days+1)) + ' day'
        elif time == 'new':
            days = str(-1*((datetime.datetime.today() - datetime.datetime(2018, 2, 5)).days+1)) + ' day'
        else:
            days = '-24 hour'

        self.c.execute('select ml_mod || \'|\' || count(*) from modlog where ml_type <> \'approvelink\' and ml_create_date > datetime(datetime(\'now\', \'localtime\'), \'' + days + '\') group by ml_mod order by count(*) desc;')

        activity = self.c.fetchall()

        self.c.execute('select mt_author || \'|\' || count(*) from modmail_tracker where mt_create_date > datetime(datetime(\'now\'), \'' + days + '\') group by mt_author order by count(*) desc;')

        mails = self.c.fetchall()

        return (activity, mails)

    def getRandomMod(self, hour):
        self.c.execute('''
            SELECT 
	            ms_mod_id, ms_mod_nick
            FROM 
	            mod_schedule ms
	            LEFT JOIN (
		            SELECT mi_mod_pinged, count(*) cnt FROM mod_info WHERE mi_create_date > datetime('now', '-12 hour') GROUP BY mi_mod_pinged
	            ) mi
		            ON ms_mod_nick = mi_mod_pinged
            WHERE 
	            datetime('now') > ms_mute_until
                AND ((ms_start_hour < ms_end_hour AND (ms_start_hour <= ? AND ? < ms_end_hour)) 
	            OR (ms_start_hour > ms_end_hour AND (? >= ms_start_hour OR ? < ms_end_hour)))
            ORDER BY 
	            mi.cnt,
	            RANDOM()
            LIMIT 1;''',
            (hour, hour, hour, hour)
        )
        
        mod = self.c.fetchall()
        
        return (mod[0][0], mod[0][1])

    def getSchedule(self, user):
        self.c.execute('SELECT ms_start_hour || \'-\' || ms_end_hour FROM mod_schedule where ms_mod_nick = ?;', (user,))

        schedule = self.c.fetchone()[0]

        return schedule
        
    def getModStatsHeroes(self):
        self.c.execute('''
            SELECT
				ml.mlHero,
				mm.mmHero
			FROM
				(SELECT 1 id) base
				LEFT JOIN (
					SELECT 1 id, ml_mod || ' | ' || count(*) as mlHero 
					FROM modlog 
					WHERE 
						ml_create_date > datetime(datetime('now', 'localtime'), '-1 hour') 
						AND ml_type <> 'approvelink'
						AND ml_mod NOT IN ('AutoModerator', 'NBA_MOD')
					GROUP BY ml_mod order by count(*) desc limit 1) ml
					ON base.id = ml.id
				LEFT JOIN (
                    SELECT 1 id, mt_author || ' | ' || count(*) as mmHero 
                    FROM modmail_tracker 
                    WHERE mt_create_date > datetime(datetime('now'), '-1 hour') 
                    GROUP BY mt_author order by count(*) desc limit 1) mm
					ON base.id = mm.id;
        '''
		)
        
        mod = self.c.fetchall()

        return (mod[0][0], mod[0][1])

    # UTIL FUNCTIONS
    def getMailUpdate(self):
        self.c.execute('SELECT MAX(mc_last_update_date) from modmail_conversations;')
        date = self.c.fetchone()[0]

        return date

    def getLogUpdate(self):
        self.c.execute('SELECT ml_id from modlog ORDER BY ml_create_date DESC LIMIT 1;')
        lastLog = self.c.fetchone()[0]

        return lastLog

    def __init__(self):
        self.nba_db = sqlite3.connect(r'd:\dev\ClipperBot\moderation.sqlite')
        self.c = self.nba_db.cursor()
        
        #self.r = reddit.Reddit()
        #self.notes = self.refresh()


#def main():
#    myDB = DB()
    
#    lastMailUpdate = myDB.getMailUpdate()
#    lastLogUpdate = myDB.getLogUpdate()

#    myDB.insertMail(('a7zfc', 'user', 'subject'))
#    myDB.insertLog(('ABCDEF123', 'user', 'action'))
#    myDB.refreshUsernotes('{"user": {"ns": [{"message": "bad user"}, {"message": "good user"}]}}')
    

#    for mail in myDB.getMailFrom('user'):
#        print(mail)
        
#    for log in myDB.getLogFrom('user'):
#        print(log)
        
#    for note in myDB.getNotesFrom('user'):
#        print(note)

    
if __name__ == '__main__':
    main()
