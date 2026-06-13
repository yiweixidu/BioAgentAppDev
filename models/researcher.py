# models/researcher.py

class Researcher:
    def __init__(self, res_id="", name="", institution="",
                 pi="", domain="", role="researcher",
                 email="", password=""):
        self.__res_id      = res_id
        self.__name        = name
        self.__institution = institution
        self.__pi          = pi
        self.__domain      = domain
        self.__role        = role
        self.__email       = email
        self.__password    = password

    # ── Getters ──────────────────────────────────────────
    def getResId(self):       return self.__res_id
    def getName(self):        return self.__name
    def getInstitution(self): return self.__institution
    def getPi(self):          return self.__pi
    def getDomain(self):      return self.__domain
    def getRole(self):        return self.__role
    def getEmail(self):       return self.__email

    # ── Setters ──────────────────────────────────────────
    def setResId(self, v):       self.__res_id = v
    def setName(self, v):        self.__name = v
    def setInstitution(self, v): self.__institution = v
    def setPi(self, v):          self.__pi = v
    def setDomain(self, v):      self.__domain = v
    def setRole(self, v):        self.__role = v
    def setEmail(self, v):       self.__email = v

    # ── Methods ──────────────────────────────────────────
    def printInfo(self):
        print(f"{self.__res_id} // {self.__name} // "
              f"{self.__role} // {self.__email}")

    def toDict(self):
        return {
            "id":          self.__res_id,
            "name":        self.__name,
            "institution": self.__institution,
            "pi":          self.__pi,
            "domain":      self.__domain,
            "role":        self.__role,
            "email":       self.__email,
        }

    def __str__(self):
        return (f"Researcher({self.__res_id}, {self.__name}, "
                f"{self.__role})")