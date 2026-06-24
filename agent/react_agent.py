from langchain.agents import create_agent
from model.factory import chat_model
from utils.prompt_loader import load_system_prompts
from agent.tools.agent_tools import (
    rag_summarize, list_majors, assess_risk, generate_report,
    fill_context_for_report,
    set_rank, set_province, set_priority, set_target_majors,
    set_weak_subjects, set_accept_adjustment,
)
from agent.tools.midddleware import monitor_tool,log_before_model,report_prompt_switch

class ReactAgent():
    def __init__(self):
        self.agent=create_agent(
            model=chat_model,
            system_prompt=load_system_prompts(),
            tools=[
                rag_summarize, list_majors, assess_risk, generate_report,
                fill_context_for_report,
                set_rank, set_province, set_priority, set_target_majors,
                set_weak_subjects, set_accept_adjustment,
            ],
            middleware=[monitor_tool,log_before_model,report_prompt_switch],
        )

    def execute_stream(self,query):
        input_dict={
            "messages":[
                {"role":"user","content":query}
            ]
        }
        #第三个参数context是上下文runtime中的信息，是做提示词切换的标记
        for chunk in self.agent.stream(input_dict,stream_mode="values",context={"report":False}):
            latest_message=chunk["messages"][-1]
            if latest_message.content:
                yield latest_message.content.strip()+'\n'   

# agent=ReactAgent()
# for chunk in agent.execute_stream("自动化专业怎么样"):
#     print(chunk,end="",flush=True)