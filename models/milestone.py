# models/milestone.py

class Milestone:
    def __init__(self, grant_id, desc,
                 due, completed=False, id=None):
        self.__id        = id          # MySQL AUTO_INCREMENT id
        self.__grant_id  = grant_id
        self.__desc      = desc
        self.__due       = str(due)
        self.__completed = bool(completed)

    # ── Getters ──────────────────────────────────────────
    def getId(self):       return self.__id
    def getGrantId(self):  return self.__grant_id
    def getDesc(self):     return self.__desc
    def getDue(self):      return self.__due
    def isCompleted(self): return self.__completed

    # ── Setters ──────────────────────────────────────────
    def setDesc(self, v): self.__desc = v
    def setDue(self, v):  self.__due = str(v)

    # ── Methods ──────────────────────────────────────────
    def markDone(self):
        self.__completed = True

    def isOverdue(self):
        from datetime import date
        return (not self.__completed and
                self.__due < date.today().isoformat())

    def printInfo(self):
        status = "✔ Done" if self.__completed else (
            "⚠ Overdue" if self.isOverdue() else "Pending")
        print(f"{self.__grant_id} // {self.__desc} // "
              f"{self.__due} // {status}")

    def toDict(self):
        return {
            "id":        self.__id,
            "grant_id":  self.__grant_id,
            "desc":      self.__desc,
            "due":       self.__due,
            "completed": self.__completed,
        }

    def __str__(self):
        return f"Milestone({self.__grant_id}, {self.__desc[:30]})"