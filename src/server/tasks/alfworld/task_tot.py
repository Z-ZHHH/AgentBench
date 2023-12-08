import os
from typing import Dict, Any

from src.server.task import Task, Session
from src.server.tasks.alfworld.environment import SingleAlfredTWEnv
from src.server.tasks.alfworld.utils import *
from src.typings import TaskOutput, TaskSampleExecutionResult, SampleStatus, AgentOutputStatus
from copy import deepcopy
import traceback
import random

class ALFWorld(Task):

    def __init__(self, **kwargs):
        # load data_path 
        self.data_path = kwargs.get("data_path", None)
        if self.data_path is None:
            raise Exception("missing parameter data_path")
        os.environ["ALFWORLD_DATA"] = self.data_path

        # load config for alfworld benchmark
        self.config_path = kwargs.get("config_path", None)
        if self.config_path is None:
            raise Exception("missing parameter config_path")
        self.config = load_config(self.config_path)

        # load prompts
        self.prompts_path = kwargs.get("prompts_path", None)
        if self.prompts_path is None:
            raise Exception("missing parameter prompts_path")
        self.prompts = load_prompts(self.prompts_path)

        # prepare data_files
        self.data_files = []
        self.split = kwargs.get("split", "dev")
        data_path = os.path.join("data/alfworld", f"{self.split}.json")
        with open(data_path, "r") as f:
            content = json.loads(f.read())
        for _, v in content.items():
            self.data_files.extend(v)
        self.data_files = [os.path.join(self.data_path, file) for file in self.data_files]
        print(f"> successfully loaded {len(self.data_files)} games")

        # other configs
        self.max_step = kwargs.get("max_step", 50)
        self.prefixes = {
            'pick_and_place': 'put',
            'pick_clean_then_place': 'clean',
            'pick_heat_then_place': 'heat',
            'pick_cool_then_place': 'cool',
            'look_at_obj': 'examine',
            'pick_two_obj': 'puttwo'
        }

        super().__init__(**kwargs)

    def get_indices(self) -> List[Any]:
        return list(range(len(self.data_files)))

    def calculate_overall(self, results: List[TaskOutput]) -> Dict[str, Any]:
        """
            TaskOutput.result 0/1
        """
        overall = {
            "total": len([config for config in results if config]),
            "pass": len([config for config in results if
                         (config and config.result and int(config.result.get("result", 0) == 1))]),
        }
        overall["wrong"] = overall["total"] - overall["pass"]
        overall["success_rate"] = overall["pass"] / overall["total"] if overall["total"] else 0
        return {
            "overall": overall,
        }


    async def start_sample(self, index, session: Session) -> TaskSampleExecutionResult:
        print("start sample")
        data_item = self.data_files[index]
        print("creating env")
        env = SingleAlfredTWEnv(self.config, data_item)
        print("initializing env")
        env = env.init_env(batch_size=1)
        try:
            print("running env")
            result, log_info, finish_reason = await self.alfworld_run(session, env)
        except Exception as e:
            print("error", e)
            traceback.print_exc()
            return TaskSampleExecutionResult(status=SampleStatus.UNKNOWN, result={"result": False, "error": e})
        log_info.update({"result": result})
        return TaskSampleExecutionResult(status=finish_reason, result=log_info)

    def release(self):
        if getattr(self, "env", None) is not None:
            del self.env

    @staticmethod
    def get_task_instruction():
        # return "Interact with a household to solve a task. Imagine you are an intelligent agent in a household environment and your target is to perform actions to complete the task goal. In the beginning of your interactions, you will be given the detailed description of the current environment and your goal to accomplish. For each of your turn, you should choose from two actions: \"THOUGHT\" or \"ACTION\". If you choose \"THOUGHT\", you should first think about the current condition and plan for your future actions, and then output your action in this turn. Your output must strictly follow this format:\"THOUGHT: your thoughts.\n ACTION: your next action\n\"; If you choose \"ACTION\", you should directly output the action in this turn. Your output must strictly follow this format:\"ACTION: your next action\n\". After your each turn, the environment will give you immediate feedback based on which you plan your next few steps. if the envrionment output \"Nothing happened\", that means the previous action is invalid and you should try more options.\n\n"
        return "Interact with a household to solve a task. Imagine you are an intelligent agent in a household environment and your target is to perform actions to complete the task goal. At the beginning of your interactions, you will be given the detailed description of the current environment and your goal to accomplish. For each of your turn, you will be given a list of actions which you can choose one to perform in this turn. You should choose from two actions: \"THOUGHT\" or \"ACTION\". If you choose \"THOUGHT\", you should first think about the current condition and plan for your future actions, and then output your action in this turn. Your output must strictly follow this format:\"THOUGHT: your thoughts.\n ACTION: your next action\n\"; If you choose \"ACTION\", you should directly output the action in this turn. Your output must strictly follow this format:\"ACTION: your next action\n\". After your each turn, the environment will give you immediate feedback based on which you plan your next few steps. if the environment output \"Nothing happened\", that means the previous action is invalid and you should try more options.\n Reminder: \n1. the action must be chosen from the given available actions. Any actions except provided available actions will be regarded as illegal. \n2. Think when necessary, try to act directly more in the process.\n\n"

    def get_prompt(self, filename: str):
        # return []
        for k, v in self.prefixes.items():
            if filename.startswith(k):
                example = self.prompts[v]
                return deepcopy(example)
        raise Exception(f"unsupported name: {filename}")
        # return self.prompts["naive_example"]

    @staticmethod
    def inject_info(session: Session, history: List):
        current_role = "user"
        traverse = {"user": "agent", "agent": "user"}
        for his in history:
            session.inject({"role": current_role, "content": his})
            current_role = traverse[current_role]

    @staticmethod
    def get_available_actions(actions):
        actions = "\n".join(actions)
        return " AVAILABLE ACTIONS: " + actions + "\n"

    async def alfworld_run(self, session: Session, env: Any):
        finish_reason = SampleStatus.COMPLETED
        # env init
        ob, info = env.reset()
        ob = '\n'.join(ob[0].split('\n\n')[1:])
        name = '/'.join(info['extra.gamefile'][0].split('/')[-3:-1])


        log_info = {}
        log_info["log"] = []
        session.inject({"role": "user", "content": self.get_task_instruction()})
        session.inject({"role": "agent", "content": "OK. I'll follow your instructions and try my best to solve the task."})

        # 1-shot naive example (react cot io)
        history = self.get_prompt(name)
        history[0] = "Here is one example.\n" + history[0]
        self.inject_info(session, history)

        init_prompt = "Here is your task. " + ob + self.get_available_actions(info.get('admissible_commands', [[]])[0])
        
        # 从初始的ob中分解出任务
        task = ob.split(":")[-1]
        log_info["init_prompt"] = init_prompt
        
        # 加入plan prompt
        
        plan_prompt = "break down the task into three subtasks and ouput in the following format: subtask1:{}subtask2:{}subtask3:{}"
        plan_example = """here is an example: 
            ###Input: 
            your task is put a soapbottle in toilet. 
            ###output:
            subtask1: The first subtask is to search for a soapbottle in the room. 
            subtask2: Once find the soapbottle, the second subtask is to pick it up and carry it to the toilet.
            subtask3: The final subtask is to put the soapbottle in the toilet.
            """
        log_info["init_prompt"] = init_prompt + plan_prompt + plan_example
        session.inject({"role": "user", "content": init_prompt + '.' + plan_prompt + plan_example})

        plan_output = session.action().split("content")[-1].split('finish_reason')[0]
        # plan_output = json.loads(plan_output)["choices"][0]['message']['content']
        subtasks = []
        # print(str(process_info(plan_output, "subtask1")).split('subtask2'))
        match_info = process_info(plan_output, "subtask1")
        try_nums = 0
        while True:
            if match_info is not None or try_nums>=3:
                break
            try_plan_prompt = "You did not break down the task in the required format. You should ouput in the following format: subtask1:{}subtask2:{}subtask3:{}"
            session.inject({"role": "user", "content": try_plan_prompt + plan_example})
            plan_output = session.action().split("content")[-1].split('finish_reason')[0]
            match_info = process_info(plan_output, "subtask1")
            try_nums +=1
        if match_info is None:
            match_info = str(plan_output)
        subtasks.append(str(match_info).lower().split('subtask2')[0])
        
        match_info = process_info(plan_output, "subtask2")
        if match_info is None:
            match_info = str(plan_output)
        subtasks.append(str(match_info).lower().split('subtask3')[0])
        
        match_info = process_info(plan_output, "subtask3")
        if match_info is None:
            match_info = str(plan_output)
        subtasks.append(str(match_info).lower())
        
        for i in range(len(subtasks)):
            print(f"subtask{i}: {subtasks[i]}")

        for subtask in subtasks:
            subtask_prompt = "now the subtask is: "+ subtask + "." + "the available action is:" + self.get_available_actions(info.get('admissible_commands', [[]])[0]) + "." + "give your thought and action. the action should come from available action list."
            session.inject({"role": "user", "content": subtask_prompt})
            path_num = 0
            sub_done = False
            while True:
                max_step = 16
                # interact
                for i in range(0, max_step):
                    output = await session.action()
                    if output.status == AgentOutputStatus.AGENT_CONTEXT_LIMIT:
                        finish_reason = SampleStatus.AGENT_CONTEXT_LIMIT
                        break
                    output = output.content or ""

                    # process action
                    admissible_commands = info.get('admissible_commands', [[]])[0]
                    action = process_action(output , admissible_commands)

                    if action is None or action not in admissible_commands:
                        action = random.choice(admissible_commands)
                    
                    session.history[-2]["content"] = session.history[-2]["content"].split("AVAILABLE ACTIONS")[0] # reduce the prompt length 

                    observation, reward, done, info = env.step([action])
                    observation, reward, done = process_ob(observation[0]), info['won'][0], done[0]

                    judge_prompt = "the subtask is:" + subtask + "." + "the action of the agent is:" + action + "." + "the observation from the environment is:" + observation + "." + "Judge whether the subtask is completed, output yes when completed, otherwise output no."
                    
                    judge_prompt = str(judge_prompt)
                    judge_prompt = judge_prompt.replace("{", "")
                    judge_prompt = judge_prompt.replace("}", "")
                    judge_prompt = judge_prompt.replace("'", "")
                    judge_prompt = judge_prompt.replace("\"", "")
                    judge_prompt = str(judge_prompt)
                    judge_config = {"model": "agentlm-7b", "messages": [{"role": "user", "content": judge_prompt}]} 
                    command = 'curl http://localhost:9000/v1/chat/completions -H "Content-Type: application/json" -d \' ' + json.dumps(judge_config) + "\'"
                    print("command: ", command)
                    judge_info = os.popen(command).read()
                    judge_info = json.loads(judge_info)["choices"][0]["message"]['content']
                    print("judge_info: ",judge_info)
                    if "no" not in judge_info and "No" not in judge_info and "NO" not in judge_info:
                        sub_done = True
                        break
                    
                    # save
                    payload = {
                        "round": i+1,
                        "output": output,
                        "action": action,
                        "admissible_commands": admissible_commands,
                        "observation": observation,
                        "done": done,
                    }
                    log_info["log"].append(payload)

                    # failure test
                    if len(log_info["log"]) > 3:
                        pre_logs = log_info["log"][-3:]
                        pre_acts = [pre_log["output"] for pre_log in pre_logs]
                        if len(list(set(pre_acts))) == 1:
                            print("repeat actions for 3 times: failure")
                            return 0, log_info, SampleStatus.AGENT_INVALID_ACTION
                    
                    if done:
                        return reward, log_info, finish_reason
                    
                    step_prompt = "give your next thought and action. the action should come from available action list."
                    session.inject({"role":"user", "content":observation + self.get_available_actions(info.get('admissible_commands', [[]])[0]) + step_prompt}) 
                    
                    

                if done:
                    return reward, log_info, finish_reason
                
                if path_num >=2 or sub_done is True:
                    break 
                path_num +=1
        return 0, log_info, finish_reason