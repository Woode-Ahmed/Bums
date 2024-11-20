import os
import json
import base64
import time
import hashlib
import random
import requests
from urllib.parse import unquote

class Bums:
    def __init__(self):
        self.base_url = 'https://api.bums.bot'
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br", 
            "Accept-Language": "en",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://app.bums.bot",
            "Referer": "https://app.bums.bot/",
            "Sec-Ch-Ua": '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
            "Sec-Ch-Ua-Mobile": "?1",
            "Sec-Ch-Ua-Platform": '"Android"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Mobile Safari/537.36"
        }
        self.SECRET_KEY = '7be2a16a82054ee58398c5edb7ac4a5a'
        self.config = self.load_config()

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')
            
    def key_bot(self):
        url = base64.b64decode("aHR0cHM6Ly9kcml2ZS5nb29nbGUuY29tL3VjP2lkPTEtSzVKOGtsc3E5anFQbXg5YnRvdmpSVVNNcWJrSHFjdyZleHBvcnQ9ZG93bmxvYWQ=").decode('utf-8')
        try:
            response = requests.get(url)
            response.raise_for_status()
            try:
                data = response.json()
                header = data['header']
                print(header)
            except json.JSONDecodeError:
                print(response.text)
        except requests.RequestException as e:
            print_(f"Failed to load header")
            
    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.log(f"Error loading config: {str(e)}")
            return {
                "maxUpgradeCost": 1000000,
                "Task": True,
                "Upgrade": True
            }

    def log(self, msg):
        print(f"[⚔] | {msg}")

    async def countdown(self, seconds):
        for i in range(seconds, 0, -1):
            print(f"\rWaiting {i} seconds to continue...", end="", flush=True)
            await asyncio.sleep(1)
        print("\r" + " " * 50 + "\r", end="")

    async def login(self, init_data, invitation_code):
        url = f"{self.base_url}/miniapps/api/user/telegram_auth"
        data = {
            'invitationCode': invitation_code,
            'initData': init_data
        }
        
        try:
            response = requests.post(url, data=data, headers=self.headers)
            json_response = response.json()
            if response.status_code == 200 and json_response['code'] == 0:
                return {
                    'success': True,
                    'token': json_response['data']['token'],
                    'data': json_response['data']
                }
            else:
                return {'success': False, 'error': json_response.get('msg', 'Unknown error')}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def get_game_info(self, token):
        url = f"{self.base_url}/miniapps/api/user_game_level/getGameInfo"
        headers = {**self.headers, "Authorization": f"Bearer {token}"}
        
        try:
            response = requests.get(url, headers=headers)
            json_response = response.json()
            if response.status_code == 200 and json_response['code'] == 0:
                return {
                    'success': True,
                    'coin': json_response['data']['gameInfo']['coin'],
                    'energySurplus': json_response['data']['gameInfo']['energySurplus'],
                    'data': json_response['data']
                }
            else:
                return {'success': False, 'error': json_response.get('msg', 'Unknown error')}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def generate_hash_code(self, collect_amount, collect_seq_no):
        data = f"{collect_amount}{collect_seq_no}{self.SECRET_KEY}"
        return hashlib.md5(data.encode()).hexdigest()

    def distribute_energy(self, total_energy):
        parts = 10
        remaining = int(total_energy)
        distributions = []
        
        for i in range(parts):
            is_last = i == parts - 1
            if is_last:
                distributions.append(remaining)
            else:
                max_amount = min(300, remaining // 2)
                amount = random.randint(1, max_amount)
                distributions.append(amount)
                remaining -= amount
        
        return distributions

    async def collect_coins(self, token, collect_seq_no, collect_amount):
        url = f"{self.base_url}/miniapps/api/user_game/collectCoin"
        headers = {**self.headers, "Authorization": f"Bearer {token}"}
        
        hash_code = self.generate_hash_code(collect_amount, collect_seq_no)
        data = {
            'hashCode': hash_code,
            'collectSeqNo': str(collect_seq_no),
            'collectAmount': str(collect_amount)
        }

        try:
            response = requests.post(url, data=data, headers=headers)
            json_response = response.json()
            if response.status_code == 200 and json_response['code'] == 0:
                return {
                    'success': True,
                    'newCollectSeqNo': json_response['data']['collectSeqNo'],
                    'data': json_response['data']
                }
            else:
                return {'success': False, 'error': json_response.get('msg', 'Unknown error')}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def process_energy_collection(self, token, energy, initial_collect_seq_no):
        energy_distributions = self.distribute_energy(energy)
        current_collect_seq_no = initial_collect_seq_no
        total_collected = 0

        for i, amount in enumerate(energy_distributions):
            if amount <= 0:
                continue
                
            result = await self.collect_coins(token, current_collect_seq_no, amount)
            
            if result['success']:
                total_collected += amount
                current_collect_seq_no = result['newCollectSeqNo']
                print(f"\033[2F[🔥] | Collection {i + 1}/10: {amount} energy           ")
                print(f"[🔥] | Success! Collected: {total_collected}/{energy}")
            else:
                print(f"[🔥] | Error while collecting: {result['error']}")
                break

            if i < len(energy_distributions) - 1:
                await self.countdown(self.config['Delays']['betweenCollect'])
        
        print(f"\n[🔥] | Total collected: {total_collected}/{energy}")
        return total_collected

    async def get_task_lists(self, token):
        url = f"{self.base_url}/miniapps/api/task/lists"
        headers = {**self.headers, "Authorization": f"Bearer {token}"}
        params = {'_t': int(time.time() * 1000)}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            json_response = response.json()
            if response.status_code == 200 and json_response['code'] == 0:
                return {
                    'success': True,
                    'tasks': [task for task in json_response['data']['lists'] if task['isFinish'] == 0]
                }
            else:
                return {'success': False, 'error': json_response.get('msg', 'Unknown error')}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def finish_task(self, token, task_id):
        url = f"{self.base_url}/miniapps/api/task/finish_task"
        headers = {**self.headers, "Authorization": f"Bearer {token}"}
        data = {
            'id': str(task_id),
            '_t': str(int(time.time() * 1000))
        }

        try:
            response = requests.post(url, data=data, headers=headers)
            json_response = response.json()
            if response.status_code == 200 and json_response['code'] == 0:
                return {'success': True}
            else:
                return {'success': False, 'error': json_response.get('msg', 'Unknown error')}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def process_tasks(self, token):
        self.log('Getting task list...')
        task_list = await self.get_task_lists(token)
        
        if not task_list['success']:
            self.log(f"Cannot get task list: {task_list['error']}")
            return

        if not task_list['tasks']:
            self.log('No new tasks!')
            return

        for task in task_list['tasks']:
            self.log(f"Working on task: {task['name']}")
            result = await self.finish_task(token, task['id'])
            
            if result['success']:
                self.log(f"Task {task['name']} completed | Reward: {task['rewardParty']}")
            else:
                self.log(f"Cannot complete task {task['name']}: {result.get('error', 'requirements not met or needs manual completion')}")

            await self.countdown(self.config['Delays']['betweenTask'])

    async def get_mine_list(self, token):
        url = f"{self.base_url}/miniapps/api/mine/getMineLists"
        headers = {**self.headers, "Authorization": f"Bearer {token}"}
        
        try:
            response = requests.post(url, headers=headers)
            json_response = response.json()
            if response.status_code == 200 and json_response['code'] == 0:
                return {
                    'success': True,
                    'mines': json_response['data']['lists']
                }
            else:
                return {'success': False, 'error': json_response.get('msg', 'Unknown error')}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def upgrade_mine(self, token, mine_id):
        url = f"{self.base_url}/miniapps/api/mine/upgrade"
        headers = {**self.headers, "Authorization": f"Bearer {token}"}
        
        data = {
            'mineId': str(mine_id)
        }
        
        try:
            response = requests.post(url, data=data, headers=headers)
            json_response = response.json()
            if response.status_code == 200 and json_response['code'] == 0:
                return {'success': True}
            else:
                return {'success': False, 'error': json_response.get('msg', 'Unknown error')}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def process_mine_upgrades(self, token, current_coin):
        self.log('Getting card list...')
        
        while True: 
            mine_list = await self.get_mine_list(token)
            
            if not mine_list['success']:
                self.log(f"Cannot get card list: {mine_list['error']}")
                return

            available_mines = [
                mine for mine in mine_list['mines']
                if mine['status'] == 1 and 
                int(mine['level']) < self.config.get('maxMineLevel', 10)
            ]
            
            available_mines.sort(
                key=lambda x: int(x['nextPerHourReward']), 
                reverse=True
            )

            if not available_mines:
                self.log('No more cards available for upgrade!')
                return

            upgradeable = False
            remaining_coin = int(current_coin)

            for mine in available_mines:
                cost = int(mine['nextLevelCost'])
                if cost > remaining_coin:
                    continue

                self.log(f"Upgrading card ID {mine['mineId']} | Level: {mine['level']} | Cost: {cost} | Reward/h: {mine['nextPerHourReward']}")
                result = await self.upgrade_mine(token, mine['mineId'])
                
                if result['success']:
                    upgradeable = True
                    remaining_coin -= cost
                    current_coin = remaining_coin 
                    self.log(f"Successfully upgraded card ID {mine['mineId']} | Remaining coin: {remaining_coin}")
                else:
                    continue  

                await self.countdown(self.config['Delays']['betweenMine'])

            if not upgradeable:
                self.log('No more upgrades possible with current coins!')
                return

    async def main(self):
        self.clear_terminal()
        data_file = os.path.join(os.path.dirname(__file__), 'query.txt')
        if not os.path.exists(data_file):
            self.log('query.txt file not found!')
            return

        with open(data_file, 'r', encoding='utf-8') as f:
            data = [line.strip() for line in f.readlines() if line.strip()]

        if not data:
            self.log('query.txt is empty!')
            return
        
        self.key_bot()
        task = self.config.get('Task', True)
        mine = self.config.get('Mine', True)

        while True:
            for i, init_data in enumerate(data):
                try:
                    user_data = json.loads(unquote(init_data.split('user=')[1].split('&')[0]))
                    user_id = user_data['id']
                    first_name = user_data['first_name']

                    self.log(f"Account {i + 1}/{len(data)} | {first_name}")
                    
                    self.log('Logging in...')
                    login_result = await self.login(init_data, 'tjkzJBie')
                    
                    if not login_result['success']:
                        self.log(f"Login failed: {login_result['error']}")
                        continue

                    self.log('Login successful!')
                    token = login_result['token']
                    
                    game_info = await self.get_game_info(token)
                    if game_info['success']:
                        self.log(f"Coins: {game_info['coin']}")
                        self.log(f"Energy: {game_info['energySurplus']}")
                        
                        if int(game_info['energySurplus']) > 0:
                            self.log('Starting energy collection...')
                            collect_seq_no = game_info['data']['tapInfo']['collectInfo']['collectSeqNo']
                            await self.process_energy_collection(token, game_info['energySurplus'], collect_seq_no)
                        else:
                            self.log('Not enough energy to collect')
                    else:
                        self.log(f"Cannot get game info: {game_info['error']}")

                    if task:
                        await self.process_tasks(token)

                    if mine:
                        await self.process_mine_upgrades(token, int(game_info['coin']))

                    if i < len(data) - 1:
                        await self.countdown(self.config['Delays']['betweenAccount'])

                except Exception as e:
                    self.log(f"Error processing account: {str(e)}")
                    continue

            await self.countdown(self.config['Delays']['nextCycle'])

if __name__ == "__main__":
    client = Bums()
    try:
        import asyncio
        asyncio.run(client.main())
    except KeyboardInterrupt:
        client.log("Program stopped by user")
    except Exception as err:
        client.log(str(err))
        exit(1)