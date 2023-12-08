import os
import json
import re
import sys
from os.path import dirname, realpath

sys.path.append(dirname(realpath(__file__)))

import multiprocess as mp
import subprocess
from typing import Dict, Callable, List

from src.task import Task, Dataset, DataPiece, Session
from .web_agent_site.envs.web_agent_text_env import WebAgentTextEnv

prompt: str = """
You are web shopping.
I will give you instructions about what to do.
You have to follow the instructions.
Every round I will give you an observation and a list of available actions, \
you have to respond an action based on the state and instruction.
You can use search action if search is available.
You can click one of the buttons in clickables.
An action should be of the following structure:
search[keywords]
click[value]
If the action is not valid, perform nothing.
Keywords in search are up to you, but the value in click must be a value in the list of available actions.
Remember that your keywords in search should be carefully designed.
Your response should use the following format:

Thought:
I think ...

Action:
click[something]
"""
Ract_prompt = """Webshop 
Instruction:  
i would like a 3 ounce bottle of bright citrus deodorant for sensitive skin, and price lower than 50.00 dollars 
[Search]  

Action: search[3 ounce bright citrus deodorant sensitive skin]
Observation: 
[Back to Search] 
Page 1 (Total results: 50) 
[Next >] 
[B078GWRC1J] 
Bright Citrus Deodorant by Earth Mama | Natural and Safe for Sensitive Skin, Pregnancy and Breastfeeding, Contains Organic Calendula 3-Ounce 
$10.99 
[B078GTKVXY] 
Ginger Fresh Deodorant by Earth Mama | Natural and Safe for Sensitive Skin, Pregnancy and Breastfeeding, Contains Organic Calendula 3-Ounce 
$10.99 
[B08KBVJ4XN] 
Barrel and Oak - Aluminum-Free Deodorant, Deodorant for Men, Essential Oil-Based Scent, 24-Hour Odor Protection, Cedar & Patchouli Blend, Gentle on Sensitive Skin (Mountain Sage, 2.7 oz, 2-Pack) 
$15.95  

Action: think[B078GWRC1J and B078GTKVXY are bright citrus deodorant less then 50 dollars. I can check B078GWRC1J first.]
Observation: OK.

Action: click[B078GWRC1J]
Observation: 
[Back to Search] 
[< Prev] 
scent [assorted scents][bright citrus][calming lavender][ginger fresh][simply non-scents]
size [travel set (4-pack)][3 ounce (pack of 1)][3-ounce (2-pack)]
Bright Citrus Deodorant by Earth Mama | Natural and Safe for Sensitive Skin, Pregnancy and Breastfeeding, Contains Organic Calendula 3-Ounce 
Price: $10.99 
Rating: N.A. 
[Description] 
[Features] 
[Reviews] 
[Buy Now]  

Action: think[For 3 ounce bottle of bright citrus deodorant for sensitive skin, the item has options 'bright citrus' and '3 ounce (pack of 1)' and seems good to buy.]
Observation: OK.

Action: click[bright citrus]
Observation: You have clicked bright citrus. 

Action: click[3 ounce (pack of 1)]
Observation: You have clicked 3 ounce (pack of 1). 

Action: click[Buy Now]
"""

def process_reponse(response):
    match = re.search("ADVICE:(.*)\n", response)
    if match:
        response = match.group(1)
        response = response.replace("{", "")
        response = response.replace("}", "")
        try:
            response = int(response)
        except:
            return 0
    else:
        return 0


def predict(receiver):
    env = WebAgentTextEnv(observation_mode="text", human_goals=True)
    command = "apt update"
    subprocess.check_output(command, shell=True, encoding="utf-8")
    command = "apt install curl -y"
    subprocess.check_output(command, shell=True, encoding="utf-8")
    while True:
        data_item, session, sender = receiver.recv()
        history = []
        env.reset(data_item)
        session.inject({"role": "user", "content": prompt})
        session.inject({"role": "agent", "content": "Ok."})

        # one shot
        # react 
        session.inject({'role': 'user', 'content': 'Observation:\n"WebShop [SEP] Instruction: [SEP] i need a long lasting 6.76 fl oz bottle of l\'eau d\'issey, and price lower than 100.00 dollars [SEP] Search"\n\nAvailable Actions:\n{"has_search_bar": true, "clickables": ["..."]}'})
        session.inject({'role': 'agent', 'content': 'Thought:\nI think I should use the search bar to look for the product I need.\n\nAction:\nsearch[l\'eau d\'issey 6.76 fl oz bottle price < 100.00]'})
        session.inject({'role': 'user', 'content': 'Observation:\n"Instruction: [SEP] i need a long lasting 6.76 fl oz bottle of l\'eau d\'issey, and price lower than 100.00 dollars [SEP] Back to Search [SEP] Page 1 (Total results: 50) [SEP] Next > [SEP] B000VOHH8I [SEP] L\'eau D\'issey By Issey Miyake for MenEau De Toilette Spray, 6.7 Fl Oz Bottle [SEP] $64.98 [SEP] B000MJZOPK [SEP] L\'eau d\'Issey by Issey Miyake for Women 3.3 oz Eau de Toilette Spray [SEP] $49.98 [SEP] B0012S249E [SEP] L\'eau D\'issey By Issey Miyake For Women. Shower Cream 6.7-Ounces [SEP] $31.36 [SEP] B01H8PGKZS [SEP] L\'eau D\'Issey FOR MEN by Issey Miyake - 6.7 oz EDT Spray [SEP] $67.97 [SEP] B00G3C8FHE [SEP] L\'Eau d\'Issey pour Homme - Eau de Toilette 4.2 fl oz [SEP] $51.25 [SEP] B000R94HRG [SEP] Issey Miyake L\'Eau D\'Issey Pour Homme Eau De Toilette Natural Spray [SEP] $44.99 [SEP] B000C214CO [SEP] Issey Miyake L\'eau D\'issey Eau de Toilette Spray for Men, 4.2 Fl Oz [SEP] $53.99 [SEP] B0018SBRDC [SEP] Issey Miyake L\'eau d\'Issey for Women EDT, White, 0.84 Fl Oz [SEP] $27.04 [SEP] B000XEAZ9Y [SEP] L\'eau De Issey By Issey Miyake For Men. Eau De Toilette Spray 6.7 Fl Oz [SEP] $67.08 [SEP] B079HZR2RX [SEP] L\'eau d\'Issey Pure by Issey Miyake for Women 3.0 oz Nectar de Parfum Spray [SEP] $71.49"\n\nAvailable Actions:\n{"has_search_bar": false, "clickables": ["...", "...", "...", "...", "...", "...", "...", "...", "...", "...", "...", "..."]}'})
        session.inject({'role': 'agent', 'content': 'Thought:\nI think I should click on the product I need, which is B000VOHH8I.\n\nAction:\nclick[B000VOHH8I]'})
        session.inject({'role': 'user', 'content': 'Observation:\n"Instruction: [SEP] i need a long lasting 6.76 fl oz bottle of l\'eau d\'issey, and price lower than 100.00 dollars [SEP] Back to Search [SEP] < Prev [SEP] size [SEP] 2.5 fl oz [SEP] 6.76 fl oz (pack of 1) [SEP] L\'eau D\'issey By Issey Miyake for MenEau De Toilette Spray, 6.7 Fl Oz Bottle [SEP] Price: $64.98 [SEP] Rating: N.A. [SEP] Description [SEP] Features [SEP] Reviews [SEP] Buy Now"\n\nAvailable Actions:\n{"has_search_bar": false, "clickables": ["...", "...", "...", "...", "...", "...", "...", "..."]}'})
        session.inject({'role': 'agent', 'content': 'Thought:\nI think I should click on the \'6.76 fl oz (pack of 1)\' option to select the size I need.\n\nAction:\nclick[6.76 fl oz (pack of 1)]'})
        session.inject({'role': 'user', 'content': 'Observation:\n"Instruction: [SEP] i need a long lasting 6.76 fl oz bottle of l\'eau d\'issey, and price lower than 100.00 dollars [SEP] Back to Search [SEP] < Prev [SEP] size [SEP] 2.5 fl oz [SEP] 6.76 fl oz (pack of 1) [SEP] L\'eau D\'issey By Issey Miyake for MenEau De Toilette Spray, 6.7 Fl Oz Bottle [SEP] Price: $64.98 [SEP] Rating: N.A. [SEP] Description [SEP] Features [SEP] Reviews [SEP] Buy Now"\n\nAvailable Actions:\n{"has_search_bar": false, "clickables": ["...", "...", "...", "...", "...", "...", "...", "..."]}'})
        session.inject({'role': 'agent', 'content': 'Thought:\nI think I should click on the \'Buy Now\' button to purchase the product.\n\nAction:\nclick[Buy Now]'})


        
        path_num = 0
        final_rewards = 0.0
        while True:
            if path_num>0:
                env.reset(data_item)
                path_prompt = "Based on the previous interaction, it was observed that the purchased item was not the optimal choice. Therefore, we will now proceed with another round of web shopping, following the same rules. However, it is important to note that actions should be adjusted appropriately based on the historical information."
                session.inject({"role": "user", "content": path_prompt})
                session.inject({"role": "agent", "content": "Ok."})
            observation = env.observation
            task = observation.split(":")[-1]
            reward = 0
            format_fail = False
            path_num += 1
            for j in range(10):
                # print(6666666666666666)
                available_actions = env.get_available_actions()
                session.inject({"role": "user", "content": f"Observation:\n{observation}\n\n"
                                                        f"Available Actions:\n{available_actions}"})
                sample_nums = 2
                actions = []
                for j in range(0, sample_nums):
                    
                    response = session.action()
                    try:
                        #action = re.search(r"[Aa]ction: *\n *((search|click)\[.+?])", response).group(1)
                        # action = re.search(r"[Aa]ction: *(\\n|\n) *((search|click)\[.+?])", response).group(1)
                        action = re.search(r"[Aa]ction: *(\\*n*|\\*\n|)* *((search|click)\[.+?])", response).group(2)
                    except:
                        format_fail = True
                        action = None
                    if action is not None:
                        actions.append(action)
                    if j < sample_nums - 1:
                        generate_prompt = "Please think and give an action, we will choose one from all the actions you give."
                        session.inject({"role": "user", "content": generate_prompt + f"Available Actions:\n {available_actions}"})

                if len(actions)==0:
                    action = None
                else:
                    print("actions: ", actions)
                    ids = "ids"
                    str_actions = " ".join(str(i)+ " " for i in actions)
                    try:
                        vote_prompt = """You should judge the action of an intelligent agent in web shopping environment. Give you the discription of the task and some actions, You pick the right one for the next round. The task is " + task + ". The actions is:" + str_actions + ". you should reponse the id of the actions with RESPONSE:{ids}
                        here are some example:
                        ###input:
                        The actions is : ['search[small blue blazer, price lower than 90 dollars, dry cleaning]', 'search[small blue blazer, price larger than 90 dollars, dry cleaning]']
                        ###output:
                        response:{0}

                        ###input:
                        The actions is:  ['click[Buy Now]', 'click[Reviews]']
                        ###output:
                        response:{0}
                        """
                        vote_prompt = str(vote_prompt)
                        vote_prompt = vote_prompt.replace("{", "")
                        vote_prompt = vote_prompt.replace("}", "")
                        vote_prompt = vote_prompt.replace("'", "")
                        vote_prompt = vote_prompt.replace("\"", "")
                        vote_prompt = str(vote_prompt)
                        judge_config = {"model": "agentlm-7b", "messages": [{"role": "user", "content": vote_prompt}]} 
                        command = 'curl http://localhost:22001/v1/chat/completions -H "Content-Type: application/json" -d \' ' + json.dumps(judge_config) + "\'"
                        print("command: ", command)
                        judge_info = subprocess.check_output(command, shell=True, encoding="utf-8")
                        # print("os popen", os.popen(command))
                        # judge_info = os.popen(command).read()
                        print("judge_info:", judge_info)
                        judge_info = json.loads(judge_info)["choices"][0]["message"]['content']
                        id = process_reponse(judge_info)
                        if id>=0 and id<len(actions):
                            action = actions[id]
                        else:
                            action = actions[0]
                    except:
                        action = actions[0]

                history.append({"observation": observation, "available_actions": available_actions,
                                "response": response, "action": action})
                if not action:
                    # 20230927 当为找到action时，不直接break，给出相应的prompt再次询问
                    reward = 0
                    observation= "Don't get the action info from your reply, please select the appropriate action from the available actions. Remember to prefix the action with Action: and don't always repeat the same action!"
                    continue

                observation, reward, done, info = env.step(action)
                if reward >= final_rewards:
                    final_rewards =  reward
                history[-1]["reward"] = final_rewards
                history[-1]["done"] = done
                
                if done:
                    break

            if final_rewards >= 1.0 or path_num>=2:
                break


        sender.send({
            "history": history,
            "reward": final_rewards,
            "format_fail": format_fail
        })

def process_advice(advice):
    match = re.search("ADVICE:(.*)\n", advice)
    if match:
        advice = match.group(1)
    else:
        match = re.search("ADVICE:(.*)", advice)
        if match:
            advice = match.group(1)
    return advice


class WebShop(Task[int, Dict, None]):
    def __init__(self, **configs):
        super().__init__(**configs)
        self.ranging = (configs.pop("start", 0), configs.pop("end", 500))
        self.num_envs = min(self.workers, configs.pop("num_envs", 1))
        self.processes = []
        ctx = mp.get_context('spawn')
        print('testing!!!!!!!!!!!!!!!!!!!!!!')
        for i in range(self.num_envs):
            receiver, sender = ctx.Pipe(False)
            p = ctx.Process(target=predict, args=(receiver,))
            p.start()
            self.processes.append((sender, ctx.Lock(), p))

    def get_data(self) -> Dataset[int, None]:
        dataset = Dataset()
        for i in range(*self.ranging):
            dataset.append(DataPiece(i, None))
        return dataset

    def predict_single(self, session: Session, data_item: Dict) -> Dict[str, None]:
        ctx = mp.get_context('spawn')
        receiver, sender = ctx.Pipe(False)
        i = 0
        while True:
            if self.processes[i][1].acquire(timeout=0.2):
                break
            i += 1
            i %= self.num_envs
        self.processes[i][0].send((data_item, session, sender))
        ret = receiver.recv()
        # print(data_item)
        print(ret)
        self.processes[i][1].release()
        return ret

    @property
    def metrics(self) -> Dict[str, Callable[[List[Dict], List[None]], float]]:
        def factory(key):
            def f(output, target):
                output = [x for x in output if x]
                if key == "history":
                    return sum([len(x[key]) for x in output]) / len(output) if len(output) > 0 else 0
                return sum([x[key] for x in output]) / len(output) if len(output) > 0 else 0

            return f

        return {
            "reward": factory("reward"),
            "format_fail_rate": factory("format_fail"),
            "average_round": factory("history"),
        }

    def release(self):
        for _, _, p in self.processes:
            p.terminate()
            p.join()
