import aiohttp
import asyncio
import json

# async def main():
#     url = "http://localhost:9000/v1/chat/completions"
#     judge_config = {
#         "model": "agentlm-7b",
#         "messages": [{"role": "user", "content": "hello, how are you"}]
#     }

#     async with aiohttp.ClientSession() as session:
#         async with session.post(url, json=judge_config) as resp:
#             judge_info = await resp.text()
#             judge_info = json.loads(judge_info)["choices"][0]["message"]['content']
#     with open("log-test.txt", "a") as log_file:
#         log_file.write("Judge judge_info: \n")
#         log_file.write(judge_info+'\n\n\n\n')

#     # 你的剩余代码

# asyncio.run(main())

vote_prompt: str = """
You should judge the action of an intelligent agent in web shopping environment. Give you the discription of the task and some actions, You pick the right one for the next round. The task is " + task + ". The actions is:" + str_actions + ". you should reponse the id of the actions with RESPONSE:{ids}
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


try:
    vote_prompt = str(vote_prompt)
    vote_prompt = vote_prompt.replace("{", "")
    vote_prompt = vote_prompt.replace("}", "")
    vote_prompt = vote_prompt.replace("'", "")
    vote_prompt = vote_prompt.replace("\"", "")
    vote_prompt = str(vote_prompt)

    vote_url = "http://localhost:9000/v1/chat/completions"
    judge_config = {"model": "agentlm-7b", "messages": [{"role": "user", "content": vote_prompt}]} 
    # async with aiohttp.ClientSession() as http_session:
    print('OK')
except:
    print('FUCK')