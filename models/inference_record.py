# models/inference_record.py

class InferenceRecord:
    def __init__(self, inf_id, type, model, project_id,
                 input, result_summary, timestamp=""):
        self.__inf_id         = inf_id
        self.__type           = type
        self.__model          = model
        self.__project_id     = project_id
        self.__input          = input
        self.__result_summary = result_summary
        self.__timestamp      = timestamp

    # ── Getters ──────────────────────────────────────────
    def getInfId(self):         return self.__inf_id
    def getType(self):          return self.__type
    def getModel(self):         return self.__model
    def getProjectId(self):     return self.__project_id
    def getInput(self):         return self.__input
    def getResultSummary(self): return self.__result_summary
    def getTimestamp(self):     return self.__timestamp

    # ── Setters ──────────────────────────────────────────
    def setResultSummary(self, v): self.__result_summary = v
    def setTimestamp(self, v):     self.__timestamp = v

    # ── Methods ──────────────────────────────────────────
    def printInfo(self):
        print(f"{self.__inf_id} // {self.__type} // "
              f"{self.__model} // {self.__timestamp}")

    def toDict(self):
        return {
            "id":             self.__inf_id,
            "type":           self.__type,
            "model":          self.__model,
            "project_id":     self.__project_id,
            "input":          self.__input,
            "result_summary": self.__result_summary,
            "timestamp":      self.__timestamp,
        }

    def __str__(self):
        return (f"InferenceRecord({self.__inf_id}, "
                f"{self.__type}, {self.__timestamp})")