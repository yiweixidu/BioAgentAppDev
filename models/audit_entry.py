# models/audit_entry.py
from datetime import datetime

class AuditEntry:
    def __init__(self, user, action, entity,
                 detail, timestamp=None, id=None):
        self.__id        = id
        self.__timestamp = timestamp or datetime.now().strftime(
                               "%Y-%m-%d %H:%M:%S")
        self.__user      = user
        self.__action    = action
        self.__entity    = entity
        self.__detail    = detail

    # ── Getters ──────────────────────────────────────────
    def getId(self):        return self.__id
    def getTimestamp(self): return self.__timestamp
    def getUser(self):      return self.__user
    def getAction(self):    return self.__action
    def getEntity(self):    return self.__entity
    def getDetail(self):    return self.__detail

    # ── Setters ──────────────────────────────────────────
    def setUser(self, v):   self.__user = v
    def setDetail(self, v): self.__detail = v

    # ── Methods ──────────────────────────────────────────
    def printInfo(self):
        print(f"[{self.__timestamp}] {self.__user} | "
              f"{self.__action} | {self.__entity} | {self.__detail}")

    def toDict(self):
        return {
            "id":        self.__id,
            "timestamp": self.__timestamp,
            "user":      self.__user,
            "action":    self.__action,
            "entity":    self.__entity,
            "detail":    self.__detail,
        }

    def __str__(self):
        return (f"AuditEntry({self.__timestamp}, "
                f"{self.__user}, {self.__action})")