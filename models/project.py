# models/project.py

class Project:
    def __init__(self, proj_id="", title="", domain="",
                 grant_src="", pi="", status="active",
                 skill=None, progress=0):
        self.__proj_id  = proj_id
        self.__title    = title
        self.__domain   = domain
        self.__grant    = grant_src
        self.__pi       = pi
        self.__status   = status
        self.__skill    = skill
        self.__progress = progress

    # ── Getters ──────────────────────────────────────────
    def getProjId(self):   return self.__proj_id
    def getTitle(self):    return self.__title
    def getDomain(self):   return self.__domain
    def getGrant(self):    return self.__grant
    def getPi(self):       return self.__pi
    def getStatus(self):   return self.__status
    def getSkill(self):    return self.__skill
    def getProgress(self): return self.__progress

    # ── Setters ──────────────────────────────────────────
    def setProjId(self, v): self.__proj_id = v
    def setDomain(self, v): self.__domain = v
    def setGrant(self, v):  self.__grant = v
    def setPi(self, v):     self.__pi = v
    def setTitle(self, v):    self.__title = v
    def setStatus(self, v):   self.__status = v
    def setSkill(self, v):    self.__skill = v
    def setProgress(self, v): self.__progress = max(0, min(100, int(v)))

    # ── Methods ──────────────────────────────────────────
    def isActive(self):
        return self.__status == "active"

    def printInfo(self):
        print(f"{self.__proj_id} // {self.__title} // "
              f"{self.__domain} // {self.__status}")

    def toDict(self):
        return {
            "id":       self.__proj_id,
            "title":    self.__title,
            "domain":   self.__domain,
            "grant":    self.__grant,
            "pi":       self.__pi,
            "status":   self.__status,
            "skill":    self.__skill,
            "progress": self.__progress,
        }

    def __str__(self):
        return f"Project({self.__proj_id}, {self.__title}, {self.__status})"