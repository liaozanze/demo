# -*- coding: utf-8 -*-
from locust import HttpUser, task, between, TaskSet, events
from locust.runners import STATE_INIT, STATE_RUNNING, STATE_STOPPING, \
    STATE_STOPPED, STATE_CLEANUP, MasterRunner, LocalRunner
import gevent
import os
import time

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.53 Safari/537.36 Edg/103.0.1264.37"
}
time_start = 0


@events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument("--failure_rate", type=float, env_var="LOCUST_MY_ARGUMENT", default=0.3)  # 失败率
    parser.add_argument("--json_code", type=str, default="0")  # 断言的code值
    parser.add_argument("--run_time_minute", type=float, default=0.5)  # 运行时间


@events.test_start.add_listener
def _(environment, **kw):
    print(f"失败率参数值: {environment.parsed_options.failure_rate}")  # 失败率   failure_rate
    print(f"断言的 Json Code 值: {environment.parsed_options.json_code}")  # 断言的code值
    print(f"运行时间(分钟): {environment.parsed_options.run_time_minute}")  # 运行时间


def checker(environment):  # 检测函数，写入检测条件
    global time_start
    while environment.runner.state not in [STATE_STOPPING,
                                           STATE_STOPPED,
                                           STATE_CLEANUP]:
        if time_start == 0 and environment.runner.state == STATE_RUNNING:  # RUNNING状态开始计时
            time_start = time.time()
            print(time_start)
        time.sleep(1)
        if environment.runner.stats.total.fail_ratio > environment.parsed_options.failure_rate:  # 失败率 failure_rate
            print(f"失败率是： {environment.runner.stats.total.fail_ratio}, 强制退出！")
            environment.runner.quit()
            time_start = 0
            return

        if time_start != 0 and time.time() - time_start > environment.parsed_options.run_time_minute * 60:  # 运行时间
            print("运行时间到了,停止压测")
            environment.runner.quit()
            time_start = 0
            return


@events.init.add_listener
def on_locust_init(environment, **_kwargs):
    # 不能写在worker里
    if isinstance(environment.runner, MasterRunner) or isinstance(environment.runner, LocalRunner):
        gevent.spawn(checker, environment)


class WebsiteUser(HttpUser):
    wait_time = between(1, 2)
    host = "https://api.m.jd.com"

    @task
    def my_task(self):

        json_code = self.environment.parsed_options.json_code

        url = 'https://api.m.jd.com/client.action?functionId=queryMaterialProducts&client=wh5'
        with self.client.post(url=url, headers=headers, catch_response=True) as response:
            try:
                if response.json()["code"] == json_code:
                    response.success()
                else:
                    response.failure("response err:" + response.text)
            except Exception as e:
                response.failure("exception:" + str(e))


if __name__ == '__main__':
    os.system("locust -f locust自定义界面参数.py")
