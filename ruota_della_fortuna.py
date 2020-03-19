class GiocatoreRDF:
    def __init__(self,nome: str):
        self._setNome(nome)
        self.montepremi = 0
        self.lista_premi = []
        self.richiestaVocale = False

    # Definisco nome come property, in modo da "controllare" il valore che gli viene attributo
    def _setNome(self, nome: str):
        if nome:
            if len(nome) == 1:
                raise ValueError('Nessuno ha un nome di un carattere solo!')                
            elif nome.isdigit():
                raise ValueError('Inserisci un nome non un numero!')                
            else:
                # Se qualcuno prova a inserire un numero decimale è un perverso...
                try:
                    val = float(nome)
                except ValueError:
                    # Non è neppure float, accetto il nome
                    self._nome = nome
                else:
                    raise ValueError('Ma allora sei perverso! Inserisci un nome non un numero decimale!')                
        else:
            raise ValueError('Inserisci un nome!')
    def _getNome(self) -> str:
        return self._nome    
    nome = property(_getNome, _setNome)

    def aggiungiVincita(self, vincita: int):
        self.montepremi = self.montepremi + vincita
        
    def inBancarotta(self):
        self.montepremi = 0

    def aggiungiPremio(self,premio: str):
        self.lista_premi.append(premio)

    def __str__(self):
        return '{} (EUR {})'.format(self.nome, self.montepremi)

class GiocatoreRDFUmano(GiocatoreRDF):
    def __init__(self,nome: str):
        super().__init__(nome)

    def ottieniMossa(self, indizio: str, fraseMacherata: str, tentativi: list) -> str:
        print('''{} ha EUR {}\nIndizio: {}\nFrase: {}\nTentativi: {}\n'''.format(self.nome, self.montepremi, indizio, fraseMacherata, ', '.join(sorted(tentativi))))
        tentativo = input("Prova con una lettera, la frase o 'esci' o 'passo': ")
        return tentativo

class GiocatoreRDFComputer(GiocatoreRDF):  
    FREQUENZA_ORDINATA_LETTERE = 'AEIONLRTSCDPUMVGHFBQZWYKJX' #Lettere più usate in Italiano, in ordine
    def __init__(self, nome: str, livello_difficolta: int):
        super().__init__(nome)
        self.livello_difficolta = livello_difficolta

    # Usa la strategia migliore (le lettere ordinate per frequenza) in base al livello
    # Casualmente decide se usarle o no
    # Metodo privato
    def _lanciaMonetinaPerLivello(self) -> bool:
        numero_casuale = random.randint(1, 10)
        if numero_casuale <= self.livello_difficolta:
            return True
        else:
            return False

    # Lista lettere selezionabili dal computer
    # Metodo privato
    def _letterePossibiliPerTentativo(self, tentativi: list) -> list:
        possibili_lettere = []
        for lettera in LETTERE:
            # Se è una vocale ma non ci sono soldi o il computer ha già chiesto una vocale nel turno, 
            # non la inserisco tra le lettere possibili
            if lettera in VOCALI and (self.montepremi < COSTO_VOCALE or (self.richiestaVocale)):
                continue
            # Per chiarezza in altro if, ma era possibile farne uno solo con il precedente
            if lettera in tentativi:
                continue
            possibili_lettere.append(lettera)
        return possibili_lettere
    
    # Mossa computer
    def ottieniMossa(self, indizio: str, fraseMacherata: str, tentativi: list) -> str:
        lppt = self._letterePossibiliPerTentativo(tentativi)
        if lppt == []:
            return 'passo'
        # Se il computer gioca "bene", usa la FREQUENZA_ORDINATA_LETTERE
        if self._lanciaMonetinaPerLivello():
            for lettera in GiocatoreRDFComputer.FREQUENZA_ORDINATA_LETTERE:
                if (lettera in lppt):
                    return lettera
                else:
                    pass
        # altrimenti a caso tra le lettere a disposizione
        else:
            return random.choice(lppt)

import sys

import json
import random
import time

LETTERE = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
VOCALI  = 'AEIOU'
COSTO_VOCALE  = 250

# Chiede ripetutamente all'utente un numero compreso tra min e max (incluso)
def ottieniNumeroTra(prompt, min: int, max: int) -> int:
    userinp = input(prompt) # chiede la prima volta

    while True:
        try:
            n = int(userinp) # prova forzatura a intero
            if n < min:
                errmessage = 'Minimo {}'.format(min)
            elif n > max:
                errmessage = 'Massimo {}'.format(max)
            else:
                return n
        except ValueError: # Non era un numero
            errmessage = '{} non è un numero.'.format(userinp)

        # in mancanza di numero, errore e riprovare
        userinp = input('{}\n{}'.format(errmessage, prompt))

# Gira la ruota per ottenre un premio a caso
# Esempi:
#    { "tipo": "cash", "testo": "EUR 950", "valore": 950, "premio": "A trip to Ann Arbor!" },
#    { "tipo": "bancarotta", "testo": "Bancarotta", "premio": false },
#    { "tipo": "perditurno", "testo": "Perdi il turno", "premio": false }
def giraRuota() -> dict:
    with open("ruota.json", 'r') as f:
        ruota = json.loads(f.read())
        return random.choice(ruota)

# Restituisce indizio & frase (come tupla) da indovinare
# Esempio:
#     ("Artista e canzone", "Whitney Houston I Will Always Love You")
def ottieniCasualmenteIndizioFrase() -> tuple:
    with open("frasi.json", 'r') as f:
        frasi = json.loads(f.read())
        indizio = random.choice(list(frasi.keys()))
        frase   = random.choice(frasi[indizio])
        return (indizio, frase.upper())

# Data una frase e un elenco di tentativi di lettere uscite, restituisce una versione oscurata
# Esempio:
#     tentativi: ['L', 'B', 'E', 'R', 'N', 'P', 'K', 'X', 'Z']
#     frase:  "GLACIER NATIONAL PARK"
#     ritorna> "_L___ER N____N_L P_RK"
def mascheraFrase(frase: str, tentativi: str) -> str:
    rv = ''
    for s in frase:
        if (s in LETTERE) and (s not in tentativi):
            rv = rv+'_'
        else:
            rv = rv+s
    return rv

# Restituisce una stringa che rappresenta lo stato corrente del gioco
def mostraTabellone(indizio: str, fraseMacherata: str, tentativi: str) -> str:
    return """
Indizio: {}
Frase:   {}
Lettere uscite:  {}""".format(indizio, fraseMacherata, ', '.join(sorted(tentativi)))

# Il gioco
titolo = 'RUOTA DELLA FORTUNA - PYTHON'
print('='*len(titolo))
print(titolo)
print('='*len(titolo))
print('')

num_umani = ottieniNumeroTra('Quanti giocatori (umani)?\n', 0, 10)

# Crea le istanze dei giocatori umani
giocatori_umani = []
for i in range(num_umani):
    while True:
        try:
            g = GiocatoreRDFUmano(input('Nome giocatore #{}\n'.format(i+1)))
        except ValueError as e:
            print(e)
        else:
            giocatori_umani.append(g)
            break        

num_computer = ottieniNumeroTra('Quanti giocatori mossi dal computer?\n', 0, 10)

# Per i giocatori computer, chiede livello
if num_computer >= 1:
    livello_difficolta = ottieniNumeroTra('Livello computer? (1-10)\n', 1, 10)

# Crea le istanze dei giocatori computer
giocatori_computer = [GiocatoreRDFComputer('Computer {}'.format(i+1), livello_difficolta) for i in range(num_computer)]

giocatori = giocatori_umani + giocatori_computer

# No giocatori, no game :(
if len(giocatori) == 0:
    print('Non ci sono abbastanza giocatori!')
    raise Exception('Non ci sono abbastanza giocatori')

# indizio e frase sono stringhe
indizio, frase = ottieniCasualmenteIndizioFrase()
# tentativi è una lista di lettere già usate
tentativi = []

# indiceGiocatore è l'indice del giocatore corrente, da 0 a len(giocatori)-1)
indiceGiocatore = 0

# sarà impostato sull'istanza del giocatore quando / se qualcuno vince
vincitore = False

def richiediMossaGiocatore(giocatore: GiocatoreRDF, indizio: str, tentativi: list) -> str:
    while True: # continueremo a chiedere una mossa al giocatore finché non ne darà una valida
        time.sleep(0.1) # aggiunto in modo che qualsiasi feedback venga stampato prima del prompt successivo

        move = giocatore.ottieniMossa(indizio, mascheraFrase(frase, tentativi), tentativi)
        move = move.upper() # converte qualsiasi input in UPPERCASE
        if move == 'ESCI' or move == 'PASSO':
            return move
        elif len(move) == 1: # tentativo di un carattere
            if move not in LETTERE: # carattere non valido, tipo @, # o EUR 
                print('Prova con lettere. Riprova.')
                continue
            elif move in tentativi: # lettera giù usata
                print('{} è già stata provata. Riprova.'.format(move))
                continue
            elif move in VOCALI and giocatore.richiestaVocale: # se vocale, controlla se giù richiesta nel turno
                    print('Hai già chiesto una vocale in questo turno.')
                    continue
            elif move in VOCALI and giocatore.montepremi < COSTO_VOCALE: # se vocale, controlla i soldi
                    print('Ti servono EUR {} per comprare una vocale. Riprova.'.format(COSTO_VOCALE))
                    continue
            else:
                return move
        else: # tentativo sulla frase
            return move

while True:
    giocatore = giocatori[indiceGiocatore]
    premioRuota = giraRuota()

    print('')
    print('-'*15)
    print(mostraTabellone(indizio, mascheraFrase(frase, tentativi), tentativi))
    print('')
    print('{} gira la ruota...'.format(giocatore.nome))
    time.sleep(2) # pausa per suspance
    print('{}!'.format(premioRuota['testo']))
    time.sleep(1) # pausa per suspance

    if premioRuota['tipo'] == 'bancarotta':
        giocatore.inBancarotta()
    elif premioRuota['tipo'] == 'perditurno':
        pass # nulla da fare; solo cambio turno
    elif premioRuota['tipo'] == 'soldi':
        move = richiediMossaGiocatore(giocatore, indizio, tentativi)
        if move == 'ESCI': # abbandona
            print('Alla prossima!')
            break
        elif move == 'PASSO': # solo cambio turno volontario
            print('{} passa'.format(giocatore.nome))
        elif len(move) == 1: # tentativo di una lettera (può essere vocale)
            tentativi.append(move)

            print('{} prova "{}"'.format(giocatore.nome, move))

            if move in VOCALI:
                print(giocatore, " RICHIEDE UNA VOCALE!")
                giocatore.montepremi -= COSTO_VOCALE
                giocatore.richiestaVocale = True

            count = frase.count(move) # restituisce un numero intero con quante volte appare questa lettera
            if count > 0:
                if count == 1:
                    print("C'è una {}".format(move))
                else:
                    print("Ci sono {} {}".format(count, move))

                # Dai loro il denaro e la lista_premi
                giocatore.aggiungiVincita(count * premioRuota['valore'])
                if premioRuota['premio']:
                    giocatore.aggiungiPremio(premioRuota['premio'])

                # tutte le lettere sono state trovate
                if mascheraFrase(frase, tentativi) == frase:
                    vincitore = giocatore
                    break

                continue # giocatore non cambia

            elif count == 0:
                print("Non ci sono {}".format(move))
        else: # tentativo sulla frase
            if move == frase: # trovata
                vincitore = giocatore

                # Dai loro il denaro e la lista_premi
                giocatore.aggiungiVincita(premioRuota['valore'])
                if premioRuota['premio']:
                    giocatore.aggiungiPremio(premioRuota['premio'])

                break
            else:
                print('{} non è la frase... '.format(move))

    # Passa al giocatore successivo (o torna al giocatore [0] se abbiamo raggiunto la fine)
    indiceGiocatore = (indiceGiocatore + 1) % len(giocatori)
    # Riazzera l'attributo sulla richiesta vocale
    giocatori[indiceGiocatore].richiestaVocale = False

if vincitore:
    # Nella tua testa, dovresti sentire questo come annunciato da un presentatore di giochi
    print('{} vince! La frase era {}'.format(vincitore.nome, frase))
    print('{} ha vinto EUR {}'.format(vincitore.nome, vincitore.montepremi))
    if len(vincitore.lista_premi) > 0:
        print('{} ha anche vinto:'.format(vincitore.nome))
        for premio in vincitore.lista_premi:
            print('    - {}'.format(premio))
else:
    print('Non ha vinto nessuno.\nLa frase era {}'.format(frase))
