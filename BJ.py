import random
import numpy as np
from enum import Enum, auto

class Card():
    def __init__(self, face, value, suit, effect):
        self.face = face #face 2-10,J,Q,K,A
        self.value = value #value 1-11
        self.suit = suit #Heart,Club,Diamond,Spade
        self.effect = effect #-1,0,1

    def ShowCard(self):
        print(str(self.face) + " of " + str(self.suit))

class Deck():
    def __init__(self):
        cards = []
        self.cards = cards
        self.InitDeck()

    def InitDeck(self):
        for suit in ['Hearts','Clubs','Diamonds','Spades']: #4 suits
            for face in [2,3,4,5,6,7,8,9,10,'J','Q','K','A']: #cards of each suit
                if face == 'A': #assign values for each card
                    value = 11
                elif face == 'J' or face == 'Q' or face == 'K':
                    value = 10
                else:
                    value = face
                if (value >= 2) and (value <= 6): #assign true count effect from card's value
                    effect = 1
                elif value >= 10:
                    effect = -1
                else:
                    effect = 0
                self.cards.append(Card(face,value,suit,effect)) #init Card with attributes and add to deck

class Hand():
    def __init__(self):
        cards = []
        self.cards = cards
        self.value = 0
        self.bet = 0
    
    def HandValue(self):
        aces = 0
        tempValue = 0
        values = []
        for card in self:
            if card.face != 'A': 
                tempValue += card.value
            else: 
                aces += 1 #SOFT HAND if aces > 0; USE FOR BASIC STRATEGY
        aceValues = Aces(aces)
        for i in aceValues:
            if i + tempValue <= 21:
                values.append(i + tempValue)
        if values == []:
            return min(aceValues) + tempValue
        else:
            return max(values)

class Player():
    def __init__(self,cash):
        pHands = [] #array of hands to allow multiple hands if hands are split
        hand = Hand() #init hand
        pHands.append(hand) #add to list of hands
        self.pHands = pHands
        self.bankroll = cash
        self.active = True #active in current round of play
        self.canPlay = True #bankroll exceeds minBet

    def resetHands(self):
        self.pHands = [] #empty list of hands
        hand = Hand() #init single hand
        self.pHands.append(hand) #add to list of hands
        
class Dealer():
    def __init__(self):
        self.hand = Hand()
        
#### FUNCTIONS ####
        
def GenDeck():
    deck = Deck()
    random.shuffle(deck.cards)
    return deck

def GenShoe():
    shoe = []
    for decks in range (0,6): #6-deck shoe
        eachDeck = GenDeck()
        for card in range (0,len(eachDeck.cards)):
            eachCard = eachDeck.cards.pop()
            shoe.append(eachCard)
    random.shuffle(shoe)
    return shoe;

def CalcTrueCount(dealer, players, trueCount): #evaluate true count from visible cards each hand
    allCardEffects = 0
    for i in range(len(dealer.hand.cards)):
        allCardEffects += dealer.hand.cards[i].effect
    for pl in range(len(players)): #EACH PLAYER
        for h in range(len(players[pl].pHands)): #EACH HAND OF PLAYER
            for c in range(len(players[pl].pHands[h].cards)): #EACH CARD OF HAND
                allCardEffects += players[pl].pHands[h].cards[c].effect
    trueCount += allCardEffects
    return trueCount

#JUST MAKING SURE THAT THE OBSERVED TRUE COUNT AND SHOE TRUE COUNT ARE SAME. THEY ARE :)
def GetTrueCount(shoe): #evaluate true count from cards remaining in shoe
    trueCount = 0
    for i in range (0,len(shoe)):
        trueCount -= shoe[i].effect
    return trueCount

def Aces(count): #build list of 2-option arrays for each ace in hand, then eval all permutations, return sums of ace values < 21
    opt = []
    for i in range(count):
        opt.append([1,11])
    perms = np.zeros((2**len(opt), len(opt))) #build ~truth table 2^#opts rows, #opts cols
    for j in range(len(opt)): #same code as autogenerating truth table
        n = len(opt) - j
        fill = int(2 ** (n - 1)) 
        for col in range(int(perms.shape[0]/fill/2)):
            perms[col * 2 ** n : col * 2 ** n + fill, j] = 1
            perms[col * 2 ** n + fill : col * 2 ** n + fill * 2, j] = 11
            #print(perms) #show build of aces value permutation array
    return list(set([int(k) for k in np.sum(perms, axis = 1) if k <= 21])) #return list of unordered sets

def HandValue(hand):
    aces = 0
    tempValue = 0
    values = []
    for card in hand:
        if card.face != 'A':
            tempValue += card.value
        else: 
            aces += 1 #SOFT HAND if aces > 0; USE FOR BASIC STRATEGY
    aceValues = Aces(aces)
    #print(aceValues)
    for i in aceValues:
        if i + tempValue <= 21:
            values.append(i + tempValue)
    if values == []:
        return min(aceValues) + tempValue
    else:
        return max(values)
    
def Deal(shoe,players):
    dealer = Dealer() #all hands reset with each deal
    for pl in range(len(players)):
        players[pl].resetHands()
    #hands = [] #array of hands, length players
    for pl in range(len(players)):
        if players[pl].pHands[0].bet > 0:
            players[pl].active = True
        #hands.append([]) #array of cards per player
    for j in range(2): #2 cards each OUTER LOOP
        for pl in range(len(players)): #INNER LOOP PLAYERS
            if players[pl].active == True:
                players[pl].pHands[0].cards.append(shoe.pop(0))
        dealer.hand.cards.append(shoe.pop(0)) #dealer's 1st card -- CASINO CARD, 2nd card hidden
    return shoe, dealer, players

def PlaceBets(bets, players,trueCount): #add parm 'results' if win/loss streak affects betting
    minBet = 5
    if trueCount > 1: 
        for pl in range(len(players)):
            players[pl].pHands[0].bet = 5 * round(((trueCount - 1) * players[pl].bankroll / 1000) / 5) #bet in $5 increments
            if players[pl].pHands[0].bet < minBet:
                players[pl].pHands[0].bet = minBet
            players[pl].bankroll -= players[pl].pHands[0].bet
    else: # if true count is <= 1, play the table minimum
        for pl in range(len(players)):
            players[pl].pHands[0].bet = minBet
    for pl in range(len(players)):
        bets[pl] = players[pl].pHands[0].bet
    return bets, players

def BasicStrategy(dealerShows,players,results):
    return players, results

def main():
    shoes = 3            #no. shoes to simulate
    noPlayers = 2          #no. players
    minBet = 5           #minimum wager
    cash = 5000          #initial funds for all players
    reshuffle = (6*52)/4 #reshuffle when 25% of shoe remains
    
    #bankrolls = []
    #bankrolls = [cash for i in range(noPlayers)] #bankroll array; start with $cash
    bets = []
    bets = [0 for j in range(noPlayers)] #bets array ONLY USED TO SHOW ALL BETS WITHOUT ITERATING PLAYERS
    results = []
    results = [0 for k in range(noPlayers)] #single round results array
    values = []
    values = [0 for l in range(noPlayers)] #values of hands for each player -- should move this to hand
    players = []
    for pl in range(noPlayers):
        addPlayer = Player(cash)
        players.append(addPlayer)
    blackjack = set([11,10]) #unordered set BJ to compare 2-card hands
    for each in range(shoes):
        trueCount = 0
        shoe = GenShoe()
        while len(shoe) > (reshuffle):
            dealerValue = 0
            bets, players = PlaceBets(bets, players,trueCount) #bet is attribute of each player
            shoe, dealer, players = Deal(shoe,players) #ALL HANDS ARE RESET IN DEAL()
            print(bets)
            print('Dealer shows:')
            dealer.hand.cards[0].ShowCard() #casino card
            dealer.hand.cards[1].ShowCard() #down card (hide)
            for pl in range(len(players)): # SHOW PLAYER CARDS
                if players[pl].active == True:
                    print('Player[' + str(pl) + ']')
                    players[pl].pHands[0].cards[0].ShowCard()
                    players[pl].pHands[0].cards[1].ShowCard()
                    players[pl].pHands[0].value = HandValue(players[pl].pHands[0].cards)
                    print(players[pl].pHands[0].value)
            dealerBJ = False # sentinel
            if set([dealer.hand.cards[0].value,dealer.hand.cards[1].value]) == blackjack: #CHECK FOR DEALER BJ
                dealerBJ = True
                print('*** Dealer Blackjack ***')
                for pl in range(len(players)):
                    if set([players[pl].pHands[0].cards[0].value,players[pl].pHands[0].cards[1].value]) != blackjack: #PLAYER LOSES IF NO BJ
                        results[pl] += -1
                    else:
                        print('*** PUSH *** Player Blackjack ***') #PLAYER PUSHES IF ALSO BJ
            else: # IF NO DEALER BJ...
                for pl in range(len(players)):
                    if set([players[pl].pHands[0].cards[0].value,players[pl].pHands[0].cards[1].value]) == blackjack: #PLAYER BJ, NO GAMEPLAY
                        print('*** Player Blackjack ***')
                        results[pl] += 1
                    else:
                        players, results = BasicStrategy(dealer.hand.cards[0].value,players,results)
                #for i in range(len(dealer.hand.cards)):
                #    dealerValue += dealer.hand.cards[i].value
                dealerValue = HandValue(dealer.hand.cards)
                while dealerValue < 17: #DEALER PLAY
                    dealer.hand.cards.append(shoe.pop(0))
                    #dealerValue += dealer.hand.cards[len(dealer.hand.cards)-1].value
                    dealerValue = HandValue(dealer.hand.cards)
                    print('Dealer hit')
                    dealer.hand.cards[len(dealer.hand.cards)-1].ShowCard() #show most recent card drawn
                print('Dealer Final: ' + str(dealerValue))
            trueCount = CalcTrueCount(dealer, players, trueCount) #adjust true count after play ends
            print('True Count: ' + str(trueCount))
    
main() 
