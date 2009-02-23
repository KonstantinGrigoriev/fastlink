import sqlite3

from util import log

class DAO(object):
    
    def __init__(self, database):
        log.debug(" opening database...%s", database)
        self.conn = sqlite3.connect(database)
        c = self.conn.cursor()
        try:
            cache_version = c.execute('SELECT VALUE FROM PARAM WHERE KEY = ?', ("cache_version",)).fetchone()[0]
            log.debug("  database found, cache version : %s", cache_version)
        except sqlite3.OperationalError:
            self._create_db()
        finally:
            c.close()
        log.debug(" opening database...Ok")
        
    def __del__(self):
        log.debug(" closing database...")
        self.conn.close()
        log.debug(" closing database...Ok")

    def _create_db(self):
        log.debug(" creating new database...")
        c = self.conn.cursor()
        try:
            c.executescript("""
            CREATE TABLE TAG(
                NAME TEXT,
                COUNT INTEGER,
                PRIMARY KEY(NAME)
            );
            
            CREATE TABLE POST(
                URL TEXT,
                TITLE TEXT,
                NOTES TEXT,
                TAG TEXT,
                HASH TEXT,
                META TEXT,
                TIMESTAMP TEXT,
                PRIMARY KEY(URL),
                FOREIGN KEY (TAG) REFERENCES TAG(NAME) ON DELETE CASCADE
            );
        
            CREATE TABLE PARAM(
                KEY,
                VALUE,
                PRIMARY KEY(KEY)
            );
        
            INSERT INTO PARAM(KEY, VALUE)
            VALUES (
                'cache_version',
                '0.1'
            );
            """)
        finally:
            c.close()
        log.debug(" creating new database...Ok")
        
    def get_param(self, param_name):
        log.debug("getting %s...", param_name)
        c = self.conn.cursor()
        try:
            param_value = c.execute('SELECT VALUE FROM PARAM WHERE KEY = ?', (param_name,)).fetchone()
            if param_value:
                param_value = param_value[0]
        finally:
            c.close()
        log.debug("getting %s...Ok(%s)", param_name, param_value)
        return param_value
            
    def update_param(self, param_name, param_value):
        log.debug("updating %s with value %s...", param_name, param_value)
        c = self.conn.cursor()
        try:
            c.execute('INSERT OR REPLACE INTO PARAM(KEY, VALUE) VALUES(?, ?)', (param_name, param_value))
            self.conn.commit()
        finally:
            c.close() 
        log.debug("updating %s...Ok", param_name)
        
    def update_last_sync(self, last_sync):
        self.update_param("last_sync", last_sync)

    def get_last_sync(self):
        return self.get_param("last_sync")

    def update_last_update(self, last_update):
        self.update_param("last_update", last_update)

    def get_last_update(self):
        return self.get_param("last_update")          
    
    def clear_tags(self):
        log.debug("clearing tags...")
        c = self.conn.cursor()
        try:
            c.execute('DELETE FROM TAG')
            self.conn.commit()
        finally:
            c.close()        
        log.debug("clearing tags...Ok")
        
    def update_tags(self, tags):
        log.debug("updating tags... : %s", tags)
        c = self.conn.cursor()
        try:
            c.executemany('INSERT OR REPLACE INTO TAG(NAME, COUNT) VALUES(:tag, :count)', tags)
            self.conn.commit()
        finally:
            c.close() 
        log.debug("updating tags...Ok")

    def clear_posts(self):
        log.debug("clearing posts...")
        c = self.conn.cursor()
        try:
            c.execute('DELETE FROM POST')
            self.conn.commit()
        finally:
            c.close()        
        log.debug("clearing posts...Ok")
        
    def update_posts(self, posts):       
        log.debug("updating posts... : %s", posts)
        c = self.conn.cursor()
        try:
            c.executemany("""INSERT OR REPLACE INTO POST(URL, 
                                                         TITLE, 
                                                         NOTES,
                                                         TAG,
                                                         HASH,
                                                         META,
                                                         TIMESTAMP) 
                                                VALUES(:href,
                                                       :description,
                                                       :extended,
                                                       :tag,
                                                       :hash,
                                                       :meta,
                                                       :time)""", posts)
            self.conn.commit()
        finally:
            c.close() 
        log.debug("updating posts...Ok")
        
    def find_posts_by_tag(self, tag, exact):
        log.debug("getting posts by tag %s, exact=%s...", tag, exact)
        c = self.conn.cursor()
        try:
            if not exact:
                result= c.execute("""SELECT p.title, p.url, p.tag FROM POST p WHERE p.tag LIKE ?""", ("%" + tag + "%" ,)).fetchall()
            else:
                result= c.execute("""SELECT p.title, p.url, p.tag FROM POST p 
                    WHERE p.tag LIKE ? OR p.tag LIKE ? OR p.tag LIKE ?""", ("% " + tag + " %" , tag + "%", "%" + tag)).fetchall()
        finally:
            c.close()
        log.debug("getting posts by tag...Ok(%s found)", len(result))
        return result          

    def find_tags(self, pattern):
        log.debug("getting tags...%s", pattern)
        c = self.conn.cursor()
        try:
            result= c.execute('SELECT t.name FROM TAG t WHERE t.name LIKE ? ORDER BY t.name', (pattern + '%',)).fetchall()
        finally:
            c.close()
        log.debug("getting tags...Ok(%s found)", len(result))
        return result    
