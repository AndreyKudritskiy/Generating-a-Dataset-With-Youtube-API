import json

class Params:
    def __init__(self):
        self.media_outlets = [
                "CBC News",
                "USA TODAY",
                "Washington Post",
                "NBC News",
                "Reuters",
                "Globe and Mail",
                "CNN",
                "BBC News",
                "The New York Times",
                "Fox News"]

        self.people_of_intrest =[
                "Donald Trump",
                "Xi Jinping",
                "Vladimir Putin",
                "Jensen Huang",
                "Sam Altman",
                "Dario Amodel",
                "Jeff Bezos",
                "Satya Nadella",
                "Mark Zuckerberg",
                "Elon Musk"]
        with open("keys.json","r") as file:
           self.auth = json.load(file)
        