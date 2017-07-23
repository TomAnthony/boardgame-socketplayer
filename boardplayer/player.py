import json
import socket
import sys
import os

class Client(object):
    def __init__(self, player, addr=None, port=None, logfile=None):
        self.player = player
        self.running = False
        self.receiver = {'player': self.handle_player,
                         'decline': self.handle_decline,
                         'error': self.handle_error,
                         'illegal': self.handle_illegal,
                         'update': self.handle_update}

        self.logfile = logfile
        self.addr = addr if addr is not None else '127.0.0.1'
        self.port = port if port is not None else 4242
        self.final_points = {}
        self.final_winners = {}

    def run(self):
        self.socket = socket.create_connection((self.addr, self.port))
        self.running = True
        while self.running:
            message = self.socket.recv(4096)
            messages = message.rstrip().split('\r\n')
            for message in messages:
                data = json.loads(message)
                if data['type'] not in self.receiver:
                    raise ValueError(
                        "Unexpected message from server: {0!r}".format(message))

                self.receiver[data['type']](data)
        
        # Game is over:
        try:
            if self.player.player:
                print("You were Player " + str(self.player.player))
                if self.logfile:
                    # only works for two player at moment

                    me = unicode(self.player.player)
                    them = unicode(3-self.player.player) 

                    if self.final_winners[me] == 1:
                        outcome = "win"
                    elif self.final_winners[unicode(self.player.player)] == 0.5:
                        outcome = "draw"
                    elif self.final_winners[unicode(self.player.player)] == 0:
                        outcome = "loss"
                    else:
                        outcome = "unknown"

                    with open(self.logfile, 'a') as the_file:
                        entry = "\t".join([
                                    outcome,
                                    str(me),
                                    str(self.final_points[me]),
                                    str(self.final_points[them])
                                    ])
                        the_file.write(entry + "" + "\n")

        except:
            pass

    def handle_player(self, data):
        player = data['message']
        print "You are player #{0}.".format(player)
        self.player.player = player

    def handle_decline(self, data):
        print data['message']
        self.running = False

    def handle_error(self, data):
        print data['message'] # FIXME: do something useful

    def handle_illegal(self, data):
        print data['message'] # FIXME: do something useful

    def handle_update(self, data):
        state = data['state']
        action = data.get('last_action', {}).get('notation') or ''
        self.player.update(state)

        print self.player.display(state, action)
        if data.get('winners') is not None:
            self.final_points = data['points']
            self.final_winners = data['winners']
            print self.player.winner_message(data['winners'])
            self.running = False
        elif data['state']['player'] == self.player.player:
            action = self.player.get_action()
            # print("You are Player " + str(self.player.player))
            self.send({'type': 'action', 'message': action})

    def send(self, data):
        self.socket.sendall("{0}\r\n".format(json.dumps(data)))


class HumanPlayer(object):
    def __init__(self, board):
        self.board = board
        self.player = None
        self.history = []

    def update(self, state):
        self.history.append(self.board.pack_state(state))

    def display(self, state, action):
        state = self.board.pack_state(state)
        action = self.board.pack_action(action)
        return self.board.display(state, action)

    def winner_message(self, winners):
        return self.board.winner_message(winners)

    def get_action(self):
        while True:
            notation = raw_input("Please enter your action: ")
            action = self.board.pack_action(notation)
            if action is None:
                continue
            if self.board.is_legal(self.history, action):
                break
        return notation
