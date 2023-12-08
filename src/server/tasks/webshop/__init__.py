from os.path import dirname, realpath

import re
import sys
import json
import subprocess
from typing import Dict, List, Any
import asyncio
import aiohttp
import json

sys.path.append(dirname(realpath(__file__)))


from src.server.task import Task, Session
from src.typings import SampleStatus, TaskOutput
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

# match = re.search("RESPONSE:(.*)", response)
# if match:
#     response = match.group(1)
#     response = response.replace("{", "")
#     response = response.replace("}", "")

def process_reponse(response):

    match = re.search("ACTION:\d+", response)
    if match:
        response = match.group(0)
        response = response.replace("{", "")
        response = response.replace("}", "")
        response = response.replace("ACTION:", "")
        try:
            response = int(response)
            return response
        except:
            return 0
    else:
        return 0
    
def editDist(str1, str2):
    m = len(str1)
    n = len(str2)

    # 初始化dp数组
    dp = [[0 for _ in range(n+1)] for _ in range(m+1)]

    # 初始化第一行和第一列
    for i in range(1, m+1):
        dp[i][0] = i
    for j in range(1, n+1):
        dp[0][j] = j

    # 计算dp数组值
    for i in range(1, m+1):
        for j in range(1, n+1):
            if str1[i-1] == str2[j-1]:
                dp[i][j] = dp[i-1][j-1] 
            else:
                dp[i][j] = min(dp[i][j-1], dp[i-1][j], dp[i-1][j-1]) + 1
        
    return dp[-1][-1]

def find_closest(element, list):
    min_dist = float('inf')
    closest = None
    element = element.lower()

    for item in list:
        item_original = item
        item = item.lower()
        dist = editDist(element, item)
        if dist < min_dist:
            min_dist = dist
            closest = item_original
    if min_dist < 4:
        return closest
    else:
        return list[0]

# def find_closest(element, list):

#     element = element.lower()

#     for item in list:
#         item_original = item
#         item = item.lower()
#         if item == element:
#             return item_original
#     return list[0]
    

class WebShop(Task):
    def __init__(self, **configs):
        super().__init__(**configs)
        self.ranging = (configs.pop("start", 0), configs.pop("end", 500))
        self.env = WebAgentTextEnv(observation_mode="text", human_goals=True)
        # print(6666666666)

    def get_indices(self) -> List[Any]:
        return list(range(*self.ranging))
    # async 
    async def start_sample(self, index: int, session: Session) -> TaskOutput:
        history = []
        env = self.env
        env.reset(index)
        session.inject({"role": "user", "content": prompt})
        session.inject({"role": "agent", "content": "Ok."})

        # one shot

        session.inject({'role': 'user', 'content': 'Observation:\n"WebShop [SEP] Instruction: [SEP] i need a long lasting 6.76 fl oz bottle of l\'eau d\'issey, and price lower than 100.00 dollars [SEP] Search"\n\nAvailable Actions:\n{"has_search_bar": true, "clickables": ["..."]}'})
        session.inject({'role': 'agent', 'content': 'Thought:\nI think I should use the search bar to look for the product I need.\n\nAction:\nsearch[l\'eau d\'issey 6.76 fl oz bottle price < 100.00]'})
        session.inject({'role': 'user', 'content': 'Observation:\n"Instruction: [SEP] i need a long lasting 6.76 fl oz bottle of l\'eau d\'issey, and price lower than 100.00 dollars [SEP] Back to Search [SEP] Page 1 (Total results: 50) [SEP] Next > [SEP] B000VOHH8I [SEP] L\'eau D\'issey By Issey Miyake for MenEau De Toilette Spray, 6.7 Fl Oz Bottle [SEP] $64.98 [SEP] B000MJZOPK [SEP] L\'eau d\'Issey by Issey Miyake for Women 3.3 oz Eau de Toilette Spray [SEP] $49.98 [SEP] B0012S249E [SEP] L\'eau D\'issey By Issey Miyake For Women. Shower Cream 6.7-Ounces [SEP] $31.36 [SEP] B01H8PGKZS [SEP] L\'eau D\'Issey FOR MEN by Issey Miyake - 6.7 oz EDT Spray [SEP] $67.97 [SEP] B00G3C8FHE [SEP] L\'Eau d\'Issey pour Homme - Eau de Toilette 4.2 fl oz [SEP] $51.25 [SEP] B000R94HRG [SEP] Issey Miyake L\'Eau D\'Issey Pour Homme Eau De Toilette Natural Spray [SEP] $44.99 [SEP] B000C214CO [SEP] Issey Miyake L\'eau D\'issey Eau de Toilette Spray for Men, 4.2 Fl Oz [SEP] $53.99 [SEP] B0018SBRDC [SEP] Issey Miyake L\'eau d\'Issey for Women EDT, White, 0.84 Fl Oz [SEP] $27.04 [SEP] B000XEAZ9Y [SEP] L\'eau De Issey By Issey Miyake For Men. Eau De Toilette Spray 6.7 Fl Oz [SEP] $67.08 [SEP] B079HZR2RX [SEP] L\'eau d\'Issey Pure by Issey Miyake for Women 3.0 oz Nectar de Parfum Spray [SEP] $71.49"\n\nAvailable Actions:\n{"has_search_bar": false, "clickables": ["...", "...", "...", "...", "...", "...", "...", "...", "...", "...", "...", "..."]}'})
        session.inject({'role': 'agent', 'content': 'Thought:\nI think I should click on the product I need, which is B000VOHH8I.\n\nAction:\nclick[B000VOHH8I]'})
        session.inject({'role': 'user', 'content': 'Observation:\n"Instruction: [SEP] i need a long lasting 6.76 fl oz bottle of l\'eau d\'issey, and price lower than 100.00 dollars [SEP] Back to Search [SEP] < Prev [SEP] size [SEP] 2.5 fl oz [SEP] 6.76 fl oz (pack of 1) [SEP] L\'eau D\'issey By Issey Miyake for MenEau De Toilette Spray, 6.7 Fl Oz Bottle [SEP] Price: $64.98 [SEP] Rating: N.A. [SEP] Description [SEP] Features [SEP] Reviews [SEP] Buy Now"\n\nAvailable Actions:\n{"has_search_bar": false, "clickables": ["...", "...", "...", "...", "...", "...", "...", "..."]}'})
        session.inject({'role': 'agent', 'content': 'Thought:\nI think I should click on the \'6.76 fl oz (pack of 1)\' option to select the size I need.\n\nAction:\nclick[6.76 fl oz (pack of 1)]'})
        session.inject({'role': 'user', 'content': 'Observation:\n"Instruction: [SEP] i need a long lasting 6.76 fl oz bottle of l\'eau d\'issey, and price lower than 100.00 dollars [SEP] Back to Search [SEP] < Prev [SEP] size [SEP] 2.5 fl oz [SEP] 6.76 fl oz (pack of 1) [SEP] L\'eau D\'issey By Issey Miyake for MenEau De Toilette Spray, 6.7 Fl Oz Bottle [SEP] Price: $64.98 [SEP] Rating: N.A. [SEP] Description [SEP] Features [SEP] Reviews [SEP] Buy Now"\n\nAvailable Actions:\n{"has_search_bar": false, "clickables": ["...", "...", "...", "...", "...", "...", "...", "..."]}'})
        session.inject({'role': 'agent', 'content': 'Thought:\nI think I should click on the \'Buy Now\' button to purchase the product.\n\nAction:\nclick[Buy Now]'})


        path_num = 0
        reward = 0
        final_rewards = 0
        finish_reason = SampleStatus.COMPLETED
        while True:
            if path_num>0:
                env.reset(index)
                # path_prompt = "Based on the previous interaction, it was observed that the purchased item was not the optimal choice. \
                #     Therefore, we will now proceed with another round of web shopping, following the same rules. \
                #     However, it is important to note that actions should be adjusted appropriately based on the historical information."
                path_prompt = prompt + "\nIn the previous interaction round, the item you choose to buy was not the optimal choice. \
                    Therefore, we will now restart another new round of web shopping. \
                    Note that the item you choose in the new round should be different from previous. " #adjusted appropriately based on the historical information."
                    # Remember, a change in strategy and actions is crucial and diversity to previous interaction round is key to maximizing the efficiency and effectiveness of task completion."
                session.inject({"role": "user", "content": path_prompt})
                session.inject({"role": "agent", "content": "Ok."})
            observation = env.observation
            task = observation.split(":")[-1]
            reward = 0
            format_fail = False
            path_num += 1
            
            # sys.stderr.write(11111111111)
            for ii in range(15):
                available_actions = env.get_available_actions()
                session.inject(
                    {
                        "role": "user",
                        "content": f"Observation:\n{observation}\n\n"
                        f"Available Actions:\n{available_actions}",
                    }
                )         
                with open("log.txt", "a") as log_file:
                    log_file.write("INIT actions: \t\t\t")
                    log_file.write(str(ii)+' Init '+'\n')
                    log_file.write(f"Available Actions:\n {available_actions}"+'\n\n')   

                sample_nums = 3  # 子节点个数 
                actions = []
                # sys.stderr.write(2222222222)
                for j in range(0, sample_nums):

                    response = await session.action()  # await session.action()  !!!!!!!!!!!!! async
                    response = response.content

                    # with open("log.txt", "a") as log_file:
                    #     log_file.write("Original response: \t\t\t")
                    #     log_file.write(str(ii)+', '+str(j)+'\n')
                    #     log_file.write(response+'\n\n\n\n')

                    try:
                        action = re.search(
                            r"[Aa]ction: *\n* *((search|click)\[.+?])", response
                        ).group(1)
                        with open("log.txt", "a") as log_file:
                            log_file.write("Original action: \t\t\t")
                            log_file.write(str(ii)+', '+str(j)+'\n')
                            log_file.write(action+'\n\n')
                        # action = re.search(
                        #     r"[Aa]ction: *(\\*n*|\\*\n|)* *((search|click)\[.+?])", response
                        #     ).group(2)
                    except:
                        finish_reason = SampleStatus.AGENT_VALIDATION_FAILED
                        action = None
                    if action is not None:
                        actions.append(action)

                    if ii == 0:
                        break
                    if j < sample_nums - 1:
                        # generate_prompt = "Please think and give an action, we will choose one from all the actions you give. "
                        generate_prompt = "You have choosen an action, we ask you to generate another distinct action choice. \
                            This alternative action should be capable of progressing the task, providing us with the flexibility to choose the one most suitable given the current conditions and observations. "
                        session.inject({"role": "user", "content": generate_prompt + f"Available Actions:\n {available_actions}"})
                    
                    with open("log.txt", "a") as log_file:
                        log_file.write("available_actions: \t\t\t")
                        log_file.write(str(ii)+', '+str(j)+'\n')
                        log_file.write(f"Available Actions:\n {available_actions}"+'\n\n')                
     


                if len(actions)==0:
                    action = None
                else:
                    actions = list(set(actions))
                    with open("log.txt", "a") as log_file:
                        log_file.write("AAAAActions: \t\t\t")
                        log_file.write(str(len(actions))+' , , '+' '.join(actions)+'\n')
                    ids = "ids"
                    str_actions = ", ".join(str(i)+ " " for i in actions)
                    
                    # vote_prompt = """Your task is to evaluate the appropriateness of an intelligent agent's action within a web shopping environment considering the Relevance, Task Completion and Accuracy.
                    # Given a task description and a corresponding set of actions, you are to select the most suitable action for the next round.
                    # The task is " + task + ". The actions is:" + str_actions + ". you should reponse the id of the actions with RESPONSE:{ids}
                    # here are some example:
                    # ###input:
                    # The actions are : ['search[small blue blazer, price lower than 90 dollars, dry cleaning]', 'search[small blue blazer, price larger than 90 dollars, dry cleaning]']
                    # ###output:
                    # response:{0}

                    # ###input:
                    # The actions are:  ['click[Buy Now]', 'click[Reviews]']
                    # ###output:
                    # response:{0}
                    # """ observation   If the agent not click[Buy Now] in an appropriate step, it fails.
                    vote_prompt = f"""Your task is to evaluate if an intelligent agent's action leads to complete the purchase task within a web shopping environment considering the Relevance and Task Completion.
                    The intelligent agent MUST buy an required item to complete its task. 
                    Given a task description and a corresponding set of actions, you are to select the most suitable action from the constituency actions for the next round.
                    you have to choose one action from constituency actions based on the state and instruction.
                    The actions could be:
                    search[keywords]
                    click[value]
                    Your response should use the following format:

                    Thought:
                    I think ...

                    Action:
                    click[something]


                    Now, the observation is: '{observation}'.\n The constituency actions are: '{str_actions}'.\n 

                    """
                    # here are some example:
                    # ###input:
                    # The observation is: WebShop [SEP] Instruction: [SEP] i would like some old fashioned summer sausage, and price lower than 20.00 dollars [SEP] Search.
                    # The available actions are: ['search[small blue blazer, price lower than 20 dollars, dry cleaning]', 'click[search]']
                    # ###output:
                    # Thought: 
                    # I think the first step is to enter the keywords 'old fashioned summer sausage whose price is lower than 90 dollars' in the search bar to look for the product, not just click the search button. So I choose the action 0. 
                    
                    # Action:
                    # search[small blue blazer, price lower than 20 dollars, dry cleaning]

                    # ###input:
                    # The observation is: Instruction: [SEP] i am looking for a high quality purple ice roller skin care tool kit, and price lower than 40.00 dollars [SEP] Back to Search [SEP] < Prev [SEP] color [SEP] black [SEP] blue [SEP] diamond pink [SEP] diamond purple [SEP] pink [SEP] purple [SEP] small pink [SEP] Small Ice Face Roller Ice Cube for Face and Eye, Silicone Ice Mold Face Massage, Facial Beauty Ice Roller Skin Care Tools, Face Ice Roller Skin Care Kit,Remove Fine Lines,Shrink Pores [SEP] Price: $12.99 [SEP] Rating: N.A. [SEP] Description [SEP] Features [SEP] Reviews [SEP] Buy Now.
                    # The available actions are: ['click[purple]', 'click[Buy Now]']
                    # ###output:
                    # Thought: 
                    # The task is to find a high quality purple ice roller skin care tool kit and price lower than 40.00 dollars. This item has a purple color and fulfills the requirements perfectly. Because the intelligent agent MUST buy an item to complete its task. So I choose the action 1 to buy this item. 
                    
                    # Action:
                    # click[Buy Now]
                    vote_prompt = str(vote_prompt)
                    vote_prompt = vote_prompt.replace("{", "")
                    vote_prompt = vote_prompt.replace("}", "")
                    vote_prompt = vote_prompt.replace("'", "")
                    vote_prompt = vote_prompt.replace("\"", "")
                    vote_prompt = str(vote_prompt)
 
                    vote_url = "http://localhost:9000/v1/chat/completions"  #agentlm-7b   llama2-7b-chat-hf
                    judge_config = {"model": "agentlm-7b", "messages": [{"role": "user", "content": vote_prompt}]} 
                    with open("log.txt", "a") as log_file:
                        log_file.write("TEST Judge: \t\t\n") 
                        # log_file.write(vote_prompt+"\t\n")
            
                    async with aiohttp.ClientSession() as http_session:
                        async with http_session.post(vote_url, json=judge_config) as resp:
                            # with open("log.txt", "a") as log_file:
                            #     log_file.write(str(resp.status))
                            if resp.status == 200:
                                judge_info = await resp.json()
                                judge_info = judge_info["choices"][0]["message"]['content']
                                # 处理响应获取id
                                # id = process_reponse(judge_info)
                                # if id >= 0 and id < len(actions):
                                #     action = actions[id]
                                # else:
                                #     action = actions[0]
                                try:
                                    tmp = re.search(
                                    r"[Aa]ction: *\n* *((search|click)\[.+?])", judge_info
                                    ).group(1)
                                    action = find_closest(tmp, actions)
                                except:
                                    action = actions[0]

                                with open("log.txt", "a") as log_file:
                                    log_file.write("Judge judge_info: \t\t\t")
                                    log_file.write(str(ii)+'\n')
                                    log_file.write(judge_info+'\n')
                                    log_file.write('choosen Action:'+action+'\n\n')
                            else:
                                # 处理非200响应
                                with open("log.txt", "a") as log_file:
                                    log_file.write("Judge judge_info: \t\t\t")
                                    log_file.write(str(ii)+'\n')
                                    log_file.write('Request Error !!!!! \n\n\n')
                                action = actions[0]


                history.append(
                    {
                        "observation": observation,
                        "available_actions": available_actions,
                        "response": response,
                        "action": action,
                    }
                )

                if not action:
                    # 20230927 当为找到action时，不直接break，给出相应的prompt再次询问
                    reward = 0
                    observation = "Please review the set of available actions and select the most appropriate one for the given context. Ensure you prefix your selected action with 'Action:',\
                          to clearly indicate your choice. NOTE to avoid the repetition of the same action consistently."
                    # observation= "Don't get the action info from your reply, please select the appropriate action from the available actions. \
                    #     Remember to prefix the action with Action: and don't always repeat the same action!"
                    continue

                observation, reward, done, info = env.step(action)
                if reward >= final_rewards:
                    final_rewards =  reward
                history[-1]["reward"] = reward
                history[-1]["done"] = done

                if done:
                    break
            else:
                finish_reason = SampleStatus.TASK_LIMIT_REACHED
            if final_rewards >= 1.0 or path_num>=1:
                break
            
        return TaskOutput(
            status=finish_reason,
            result={
                "reward": final_rewards,
                "history": history,
            },
        )


    def calculate_overall(self, results: List[TaskOutput]) -> Dict:
        def factory(key):
            def f(output):
                output = [x for x in output if x]
                if key == "history":
                    return (
                        sum([len(x[key]) for x in output]) / len(output)
                        if len(output) > 0
                        else 0
                    )
                return (
                    sum([x[key] for x in output]) / len(output)
                    if len(output) > 0
                    else 0
                )

            return f

        results = [x.result for x in results if x]

        return {
            "reward": factory("reward")(results),
        }
