class File:
    size: int
    name: str
    belongsTo: str

    def __init__(self, size, name, belongsTo):
        self.size = size
        self.name = name
        self.belongsTo = belongsTo

    def getName(self):
        return self.name
    
    def getSize(self):
        return self.size
    
    def getOwner(self):
        return self.belongsTo
