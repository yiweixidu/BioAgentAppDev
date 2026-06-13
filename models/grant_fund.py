# models/grant_fund.py

class Grant:
    def __init__(self, grant_id, project_id, grant_type,
                 deadline, total, used=0):
        self.__grant_id   = grant_id
        self.__project_id = project_id
        self.__grant_type = grant_type
        self.__deadline   = str(deadline)
        self.__total      = float(total)
        self.__used       = float(used)

    # ── Getters ──────────────────────────────────────────
    def getGrantId(self):   return self.__grant_id
    def getProjectId(self): return self.__project_id
    def getGrantType(self): return self.__grant_type
    def getDeadline(self):  return self.__deadline
    def getTotal(self):     return self.__total
    def getUsed(self):      return self.__used

    # ── Setters ──────────────────────────────────────────
    def setUsed(self, v):     self.__used = float(v)
    def setDeadline(self, v): self.__deadline = str(v)

    # ── Methods ──────────────────────────────────────────
    def getBudgetPct(self):
        if self.__total == 0:
            return 0
        return int(self.__used / self.__total * 100)

    def isOverdue(self):
        from datetime import date
        return self.__deadline < date.today().isoformat()

    def getRemaining(self):
        return self.__total - self.__used

    def printInfo(self):
        print(f"{self.__grant_id} // {self.__grant_type} // "
              f"${self.__used:,.0f} / ${self.__total:,.0f} "
              f"({self.getBudgetPct()}%)")

    def toDict(self):
        return {
            "id":         self.__grant_id,
            "project_id": self.__project_id,
            "grant_type":     self.__grant_type,
            "deadline":   self.__deadline,
            "total":      self.__total,
            "used":       self.__used,
        }

    def __str__(self):
        return (f"Grant({self.__grant_id}, {self.__grant_type}, "
                f"{self.getBudgetPct()}% used)")