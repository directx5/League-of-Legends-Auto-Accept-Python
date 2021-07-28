from json import dumps
from os import path
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor

from requests import Session
from urllib3 import disable_warnings, exceptions


class League:
    def __init__(self, league: str):
        with open('champions.txt', 'r', encoding='UTF-8') as file:
            c = [i.split(':') for i in file.read().splitlines()]
            self.champions = dict(zip([i[0] for i in c], [i[1] for i in c]))
        with open(path.join(league, 'lockfile'), 'r', encoding='UTF-8') as lockfile:
            port, self.__password, protocol = lockfile.read().split(':')[2:]
        self.base_url = f'{protocol}://127.0.0.1:{port}/'
        self.__session = Session()
        self.__session.auth = ('riot', self.__password)
        self.__session.verify = False
        disable_warnings(exceptions.InsecureRequestWarning)

    def request(self, method, endpoint, data=None):
        return self.__session.request(method, urljoin(self.base_url, endpoint), data=dumps(data))

    def is_found(self):
        return self.request('get', '/lol-lobby/v2/lobby/matchmaking/search-state').json().get('searchState') == 'Found'

    def is_selecting(self):
        return self.request('get', '/lol-champ-select/v1/session').json().get('actions') is not None

    def search(self):
        self.request('post', '/lol-lobby/v2/lobby/matchmaking/search')

    def accept(self):
        self.request('post', '/lol-matchmaking/v1/ready-check/accept')

    def select_champion(self, champion_name: str, qid: int):
        data = {"championId": self.champions.get(champion_name), 'completed': True}
        self.request('patch', f'/lol-champ-select/v1/session/actions/{qid}', data)

    def is_me(self, qid: int):
        return self.request('get', f'/lol-champ-select/v1/summoners/{qid}').json().get('isSelf') is True

    def select(self, champion: str):
        with ThreadPoolExecutor() as executor:
            me = [i for i in range(0, 5) if executor.submit(self.is_me, i).result() is True][0]+1
            self.select_champion(champion, me)


if __name__ == '__main__':
    client = League(r'C:\Riot Games\League of Legends')
    while True:
        if client.is_selecting():
            client.select('Zed')
            break
        elif client.is_found():
            client.accept()
        else:
            continue
