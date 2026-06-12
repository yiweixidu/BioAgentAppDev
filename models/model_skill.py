# models/model_skill.py

class ModelSkill:
    def __init__(self, skill_id, name, project_id,
                 lora_version, threshold=200,
                 benchmark="default_eval",
                 status="inactive", loaded=""):
        self.__skill_id     = skill_id
        self.__name         = name
        self.__project_id   = project_id
        self.__lora_version = lora_version
        self.__threshold    = int(threshold)
        self.__benchmark    = benchmark
        self.__status       = status
        self.__loaded       = loaded

    # ── Getters ──────────────────────────────────────────
    def getSkillId(self):      return self.__skill_id
    def getName(self):         return self.__name
    def getProjectId(self):    return self.__project_id
    def getLoraVersion(self):  return self.__lora_version
    def getThreshold(self):    return self.__threshold
    def getBenchmark(self):    return self.__benchmark
    def getStatus(self):       return self.__status
    def getLoaded(self):       return self.__loaded

    # ── Setters ──────────────────────────────────────────
    def setStatus(self, v):     self.__status = v
    def setThreshold(self, v):  self.__threshold = int(v)
    def setBenchmark(self, v):  self.__benchmark = v

    # ── Methods ──────────────────────────────────────────
    def activate(self):   self.__status = "active"
    def deactivate(self): self.__status = "inactive"
    def isActive(self):   return self.__status == "active"

    def printInfo(self):
        print(f"{self.__skill_id} // {self.__name} // "
              f"{self.__lora_version} // {self.__status}")

    def toDict(self):
        return {
            "id":           self.__skill_id,
            "name":         self.__name,
            "project_id":   self.__project_id,
            "lora_version": self.__lora_version,
            "threshold":    self.__threshold,
            "benchmark":    self.__benchmark,
            "status":       self.__status,
            "loaded":       self.__loaded,
        }

    def __str__(self):
        return (f"ModelSkill({self.__skill_id}, {self.__name}, "
                f"{self.__status})")