# models/hypothesis.py

class Hypothesis:
    def __init__(self, hyp_id, project_id, text,
                 status="pending", confidence=0.5,
                 pmids="", note=""):
        self.__hyp_id     = hyp_id
        self.__project_id = project_id
        self.__text       = text
        self.__status     = status
        self.__confidence = float(confidence)
        self.__pmids      = pmids
        self.__note       = note

    # ── Getters ──────────────────────────────────────────
    def getHypId(self):      return self.__hyp_id
    def getProjectId(self):  return self.__project_id
    def getText(self):       return self.__text
    def getStatus(self):     return self.__status
    def getConfidence(self): return self.__confidence
    def getPmids(self):      return self.__pmids
    def getNote(self):       return self.__note

    # ── Setters ──────────────────────────────────────────
    def setStatus(self, v):      self.__status = v
    def setConfidence(self, v):  self.__confidence = float(v)
    def setNote(self, v):        self.__note = v

    # ── Methods ──────────────────────────────────────────
    def isSupported(self): return self.__status == "supported"
    def isRefuted(self):   return self.__status == "refuted"
    def isPending(self):   return self.__status == "pending"

    def updateResult(self, new_status, note=""):
        self.__status = new_status
        if note:
            self.__note = note

    def printInfo(self):
        print(f"{self.__hyp_id} // {self.__text[:40]} // "
              f"{self.__status} // conf={self.__confidence:.2f}")

    def toDict(self):
        return {
            "id":         self.__hyp_id,
            "project_id": self.__project_id,
            "text":       self.__text,
            "status":     self.__status,
            "confidence": self.__confidence,
            "pmids":      self.__pmids,
            "note":       self.__note,
        }

    def __str__(self):
        return (f"Hypothesis({self.__hyp_id}, "
                f"{self.__status}, conf={self.__confidence:.2f})")